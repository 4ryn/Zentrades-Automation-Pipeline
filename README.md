# Clara AI Agent Configuration Automation Pipeline

This project implements an **end-to-end automation pipeline** that converts business call transcripts into structured configurations for AI voice agents.

The system processes **two types of calls**:

1. **Demo Calls** → Generate an initial AI agent configuration  
2. **Onboarding Calls** → Update the configuration and create a new version

The pipeline extracts structured information from conversations, generates configuration files, and tracks changes across versions.

---

# Architecture Overview

The system is composed of three main components:

```
n8n            → Workflow orchestration
Groq LLM       → Transcript information extraction
FastAPI        → Configuration generation and version management
Docker         → Local deployment
```

### High Level Architecture

```
             Transcript Dataset
                    │
                    ▼
              n8n Workflow
                    │
        ┌───────────┴───────────┐
        ▼                       ▼

   Pipeline A              Pipeline B
   Demo Call               Onboarding Call

        │                       │
        ▼                       ▼

     Groq LLM              Groq LLM
  Information Extractor   Update Extractor

        │                       │
        ▼                       ▼

      FastAPI                 FastAPI
 Configuration Generator    Version Updater

        │                       │
        ▼                       ▼

    v1 Agent Config        v2 Agent Config
```

---

# System Components

## n8n

n8n orchestrates the workflow and performs:

- transcript ingestion
- LLM requests
- JSON parsing
- API communication

It ensures the pipeline runs automatically for multiple transcripts.

---

## Groq LLM

Groq's **Llama-3.3-70B** model is used to convert unstructured call transcripts into structured JSON.

Two prompt templates are used:

### Demo Extraction Prompt

Extracts:

- company information
- business hours
- services
- emergency routing rules
- call handling logic

### Onboarding Extraction Prompt

Extracts:

- operational updates
- routing changes
- business hour changes
- integration updates

---

## FastAPI Backend

The Python API performs:

- memo validation
- configuration generation
- version management
- change tracking

Endpoints:

```
POST /process-demo
POST /process-onboarding
```

---

# Pipeline A — Demo Call → Preliminary Agent

Purpose:  
Generate the **initial AI agent configuration (v1)**.

### Workflow

```
Transcript
   │
   ▼
Read File (n8n)
   │
   ▼
Clean Transcript
   │
   ▼
Groq Extraction
   │
   ▼
Parse JSON
   │
   ▼
POST /process-demo
   │
   ▼
Generate memo.json
Generate agent_spec.json
```

### Output

```
outputs/
  accounts/
    account_{id}/
      v1/
        memo.json
        agent_spec.json
```

---

### memo.json

Structured business information extracted from the demo call.

Example:

```json
{
  "account_id": "case_001",
  "company_name": "Ben's Electric",
  "business_hours": {
    "days": "Monday-Friday",
    "start": "08:00",
    "end": "16:30",
    "timezone": "MT"
  },
  "services_supported": [
    "Electrical repair",
    "Commercial electrical work"
  ],
  "emergency_definition": [
    "Power outage",
    "Electrical hazard"
  ]
}
```

---

### agent_spec.json

Defines the AI voice assistant configuration.

Example:

```json
{
  "agent_name": "Ben's Electric Assistant",
  "voice_style": "professional friendly",
  "version": "v1",
  "call_transfer_protocol": {
    "primary_contact": "403-975-1773"
  }
}
```

---

# Pipeline B — Onboarding → Agent Update

Purpose:  
Update an existing agent configuration using onboarding information.

### Workflow

```
Onboarding Transcript
       │
       ▼
Read File
       │
       ▼
Clean Transcript
       │
       ▼
Groq Extraction
       │
       ▼
Parse JSON
       │
       ▼
POST /process-onboarding
       │
       ▼
Merge Updates
Generate v2 Config
Create Change Log
```

---

# Versioning System

Each account configuration is stored with version folders.

```
outputs/accounts/{account_id}/
```

Example:

```
account_001
   │
   ├── v1
   │    memo.json
   │    agent_spec.json
   │
   └── v2
        memo.json
        agent_spec.json
```

### Version meanings

```
v1 → initial demo configuration
v2 → onboarding updates
v3 + → future updates
```

This allows full **configuration history tracking**.

---

# Change Tracking

Changes between versions are automatically generated.

Location:

```
data/changelog/
```

Example:

```
account_001_changes.json
```

Example output:

```json
{
  "business_hours": {
    "old": "Monday-Friday 9-5",
    "new": "Monday-Friday 8-4:30"
  },
  "emergency_routing": {
    "old": "voicemail",
    "new": "Direct call to technician"
  }
}
```

This enables auditing of configuration updates.

---

# Repository Structure

```
clara-pipeline
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
│
├── workflows
│   ├── pipelineA.json
│   └── pipelineB.json
│
├── scripts
│   └── api.py
│
├── data
│   ├── demo_calls
│   └── onboarding_calls
│
├── outputs
│   └── accounts
│
├── changelog
│
└── README.md

```

---

# Setup Instructions

## 1. Clone Repository

```
git clone <repository>
cd clara-pipeline
```

---

## 2. Start Docker Environment

```
docker compose build
docker compose up
```

This launches:

- n8n
- FastAPI backend
- shared data volume

---

## 3. Access n8n

```
http://localhost:5678
```

Import the workflow and run the pipelines.

---

# API Endpoints

### Create Initial Configuration

```
POST /process-demo
```

Example:

```json
{
  "account_id": "case_001",
  "llm_output": "{...}"
}
```

---

### Update Configuration

```
POST /process-onboarding
```

Example:

```json
{
  "account_id": "case_001",
  "updates": {
    "business_hours": "Monday-Friday 8-4:30",
    "emergency_routing": "Direct call to technician"
  }
}
```

---

### List Accounts

```
GET /accounts
```

---

# Key Features

- automated transcript processing
- structured information extraction
- AI voice agent configuration generation
- configuration versioning
- automated change tracking
- containerized deployment

---

# Technologies Used

- Python
- FastAPI
- n8n
- Groq LLM API
- Docker
- JSON configuration management

---

# Future Work

Potential improvements include:

- real-time transcript ingestion
- automatic prompt optimization
- multi-agent configuration generation
- CRM integrations



# Summary

This project demonstrates a scalable architecture for **automating AI agent onboarding workflows**.

By converting conversational transcripts into structured configuration files, the system enables rapid AI voice agent deployment while maintaining full configuration history and change tracking.