---
title: Support Triage OpenEnv
emoji: 🎫
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
tags:
  - openenv
  - customer-support
  - nlp
  - triage
license: mit
---

# 🎫 Support Triage OpenEnv

A customer support ticket triage environment for AI agent training and evaluation. Built to the full OpenEnv specification.

An AI agent reads incoming support tickets one at a time and makes structured triage decisions: classify the issue category, set urgency level, route to the correct team, decide whether to escalate, and optionally draft a professional reply.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check — returns 200 |
| POST | `/reset` | Reset environment, returns first ticket |
| POST | `/step` | Submit triage action, returns reward |
| GET | `/state` | Current episode state |
| GET | `/docs` | Interactive Swagger UI |

### Reset
```bash
curl -X POST https://your-space.hf.space/reset
# or with task:
curl -X POST https://your-space.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_easy"}'
```

### Step
```bash
curl -X POST https://your-space.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "category": "billing",
    "urgency": "medium",
    "assign_to": "billing_team",
    "needs_escalation": false,
    "tags": ["refund"],
    "draft_reply": null
  }'
```

---

## Action Space

| Field | Values |
|-------|--------|
| `category` | `billing`, `technical`, `account`, `feature_request`, `abuse`, `general` |
| `urgency` | `critical`, `high`, `medium`, `low` |
| `assign_to` | `billing_team`, `technical_team`, `account_team`, `trust_safety`, `product_team`, `general_support` |
| `needs_escalation` | `true` / `false` |
| `draft_reply` | string or null |
| `tags` | list of strings |

---

## Tasks

| Task | Difficulty | Tickets | Passing Score |
|------|-----------|---------|---------------|
| `task_easy` | Easy | 5 | 0.70 |
| `task_medium` | Medium | 5 | 0.60 |
| `task_hard` | Hard | 5 | 0.50 |

---

## Reward Function

Each action is scored immediately across 5 components:

| Component | Weight (easy) | Weight (medium) | Weight (hard) |
|-----------|:---:|:---:|:---:|
| Category | 0.35 | 0.30 | 0.20 |
| Urgency | 0.30 | 0.25 | 0.20 |
| Routing | 0.25 | 0.30 | 0.20 |
| Escalation | 0.10 | 0.15 | 0.15 |
| Reply quality | 0.00 | 0.00 | 0.25 |

Urgency gives **partial credit (0.5)** for being one level off.

---

## Running the Baseline Agent

```bash
export API_BASE_URL="https://router.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-3.1-8B-Instruct"
export HF_TOKEN="your_token_here"
export ENV_BASE_URL="https://your-space.hf.space"

python inference.py
```

---

## Project Structure

```
├── Dockerfile
├── requirements.txt
├── inference.py
├── openenv.yaml
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── environment.py
└── tasks/
    ├── __init__.py
    ├── task_definitions.py
    └── graders.py
```