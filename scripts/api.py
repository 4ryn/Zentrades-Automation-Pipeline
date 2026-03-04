from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import json
import os
from datetime import datetime
import logging

app = FastAPI(title="Clara Automation Pipeline")

BASE_PATH = "/data/outputs/accounts"
CHANGELOG_PATH = "/data/changelog"

logging.basicConfig(level=logging.INFO)


# -------------------------
# Models
# -------------------------

class DemoInput(BaseModel):
    account_id: str
    llm_output: str


class OnboardingInput(BaseModel):
    account_id: str
    updates: Dict[str, Any]


# -------------------------
# Utilities
# -------------------------

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def save_json(path, data):
    ensure_dir(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def recursive_merge(old, new):
    """Deep merge dictionaries"""
    for k, v in new.items():
        if isinstance(v, dict) and isinstance(old.get(k), dict):
            recursive_merge(old[k], v)
        else:
            old[k] = v
    return old


def recursive_diff(old, new, path=""):
    """Deep JSON diff"""
    diff = []

    keys = set(old.keys()) | set(new.keys())

    for key in keys:

        old_val = old.get(key)
        new_val = new.get(key)

        full_path = f"{path}.{key}" if path else key

        if isinstance(old_val, dict) and isinstance(new_val, dict):
            diff.extend(recursive_diff(old_val, new_val, full_path))

        elif old_val != new_val:
            diff.append({
                "field": full_path,
                "old": old_val,
                "new": new_val
            })

    return diff


def generate_agent_spec(memo, version):

    return {
        "agent_name": f"{memo.get('company_name','Company')} Assistant",
        "version": version,
        "generated_at": datetime.utcnow().isoformat(),

        "voice_style": "professional friendly",

        "key_variables": {
            "business_hours": memo.get("business_hours"),
            "office_address": memo.get("office_address"),
            "services_supported": memo.get("services_supported")
        },

        "call_transfer_protocol": memo.get("call_transfer_rules"),

        "fallback_protocol": {
            "message": memo.get("call_transfer_rules",{}).get(
                "failure_message",
                "A technician will call you back shortly."
            )
        },

        "system_prompt": f"""
You are the virtual receptionist for {memo.get('company_name')}.

Office Hours Flow:
- greet caller
- understand issue
- collect name and number
- route call appropriately
- confirm next steps
- ask if anything else needed

After Hours Flow:
- greet caller
- confirm emergency
- collect name phone address
- attempt transfer
- fallback if transfer fails
"""
    }


# -------------------------
# Pipeline A
# Demo Processing
# -------------------------

@app.post("/process-demo")
def process_demo(data: DemoInput):

    try:

        memo = json.loads(data.llm_output)

        memo["account_id"] = data.account_id

        version = "v1"

        base = f"{BASE_PATH}/{data.account_id}/{version}"

        agent_spec = generate_agent_spec(memo, version)

        save_json(f"{base}/memo.json", memo)

        save_json(f"{base}/agent_spec.json", agent_spec)

        logging.info(f"Created v1 agent for {data.account_id}")

        return {
            "status": "v1_created",
            "account_id": data.account_id
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# -------------------------
# Pipeline B
# Onboarding Updates
# -------------------------

@app.post("/process-onboarding")
def process_onboarding(data: OnboardingInput):

    try:

        account_path = f"{BASE_PATH}/{data.account_id}"

        memo_v1 = load_json(f"{account_path}/v1/memo.json")

        if not memo_v1:
            raise HTTPException(404, "Account not found")

        memo_v2 = recursive_merge(memo_v1.copy(), data.updates)

        diff = recursive_diff(memo_v1, memo_v2)

        agent_spec_v2 = generate_agent_spec(memo_v2, "v2")

        v2_path = f"{account_path}/v2"

        save_json(f"{v2_path}/memo.json", memo_v2)

        save_json(f"{v2_path}/agent_spec.json", agent_spec_v2)

        ensure_dir(CHANGELOG_PATH)

        save_json(
            f"{CHANGELOG_PATH}/{data.account_id}_changes.json",
            diff
        )

        logging.info(f"Updated account {data.account_id} to v2")

        return {
            "status": "v2_created",
            "account_id": data.account_id,
            "changes_detected": len(diff)
        }

    except Exception as e:
        raise HTTPException(500, str(e))


