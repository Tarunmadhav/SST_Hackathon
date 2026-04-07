"""
Inference Script — Support Triage OpenEnv Baseline
===================================================
MANDATORY environment variables:
  API_BASE_URL   The API endpoint for the LLM (e.g. https://router.huggingface.co/v1)
  MODEL_NAME     The model identifier (e.g. meta-llama/Llama-3.1-8B-Instruct)
  HF_TOKEN       Your HuggingFace token / API key

Run:
  python inference.py

The script runs the baseline agent on all 3 tasks and prints per-ticket scores
plus a final summary table.
"""

import os
import json
import textwrap
import time
import sys
from typing import Dict, Any, Optional

import requests
from openai import OpenAI

# ── Config ──────────────────────────────────────────────────────────────────
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY: str = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
MODEL_NAME: str = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
ENV_BASE_URL: str = os.getenv("ENV_BASE_URL", "http://localhost:7860")

MAX_TOKENS = 512
TEMPERATURE = 0.1
TASKS = ["task_easy", "task_medium", "task_hard"]

# ── OpenAI client ────────────────────────────────────────────────────────────
client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY or "dummy")

# ── System prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""
You are an expert customer support triage specialist. You will be shown a support ticket
and must make a triage decision.

You MUST respond with ONLY a valid JSON object (no markdown, no explanation) with these exact fields:

{
  "category": "<one of: billing, technical, account, feature_request, abuse, general>",
  "urgency": "<one of: critical, high, medium, low>",
  "assign_to": "<one of: billing_team, technical_team, account_team, trust_safety, product_team, general_support>",
  "needs_escalation": <true or false>,
  "tags": ["tag1", "tag2"],
  "draft_reply": "<professional reply to the customer, or null>"
}

Triage rules:
- billing: payment, invoice, charge, refund, subscription pricing
- technical: bugs, errors, outages, API issues, broken features
- account: login, password, access, GDPR/data deletion, account settings
- feature_request: suggestions, new features, improvements
- abuse: harassment, spam, illegal content, policy violations
- general: how-to questions, general inquiries not fitting above

Urgency rules:
- critical: production down, security breach, data loss, legal threat, child safety
- high: major feature broken, angry customer, time-sensitive deadline
- medium: non-blocking issue, billing discrepancy, general problem
- low: feature requests, how-to questions, minor issues

Escalation: set true for critical urgency, multi-issue tickets, threats, or abuse reports.

Routing:
- billing issues → billing_team
- technical/bugs → technical_team
- account/access/GDPR → account_team
- abuse/policy violations → trust_safety
- feature requests → product_team
- general how-to → general_support

The draft_reply should be professional, empathetic, and address the customer's specific concern.
For null-urgency or non-critical tickets, draft_reply can be null.
""").strip()


# ── Environment API helpers ───────────────────────────────────────────────────

def env_reset(task_id: str) -> Dict[str, Any]:
    resp = requests.post(f"{ENV_BASE_URL}/reset", json={"task_id": task_id}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def env_step(action: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(f"{ENV_BASE_URL}/step", json=action, timeout=30)
    resp.raise_for_status()
    return resp.json()


def env_state() -> Dict[str, Any]:
    resp = requests.get(f"{ENV_BASE_URL}/state", timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── LLM call ─────────────────────────────────────────────────────────────────

def call_llm(ticket_obs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a prompt from the ticket observation and call the LLM.
    Returns a parsed action dict.
    """
    user_content = textwrap.dedent(f"""
    TICKET ID: {ticket_obs['ticket_id']}
    SUBJECT: {ticket_obs['subject']}
    FROM: {ticket_obs['sender_email']}
    DATE: {ticket_obs['created_at']}
    ATTACHMENTS: {', '.join(ticket_obs.get('attachments', [])) or 'None'}

    BODY:
    {ticket_obs['body']}
    """).strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        action = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: safe defaults
        print(f"  [WARN] JSON parse failed, using fallback. Raw: {raw[:200]}")
        action = {
            "category": "general",
            "urgency": "medium",
            "assign_to": "general_support",
            "needs_escalation": False,
            "tags": [],
            "draft_reply": None,
        }

    # Ensure required fields exist
    action.setdefault("needs_escalation", False)
    action.setdefault("tags", [])
    action.setdefault("draft_reply", None)

    return action


# ── Main runner ───────────────────────────────────────────────────────────────

def run_task(task_id: str) -> Dict[str, Any]:
    """Run the agent on one task. Returns summary dict."""
    # Structured output for validator
    print(f"[START] task={task_id}", flush=True)

    reset_result = env_reset(task_id)
    obs = reset_result["observation"]
    total_tickets = reset_result["info"]["total_tickets"]

    ticket_scores = []
    step_num = 0

    while obs is not None:
        step_num += 1
        print(f"  [{step_num}/{total_tickets}] Ticket: {obs['ticket_id']}")
        print(f"  Subject: {obs['subject'][:80]}")

        # Agent decision
        action = call_llm(obs)
        print(f"  Action: category={action['category']}, urgency={action['urgency']}, "
              f"assign_to={action['assign_to']}, escalate={action['needs_escalation']}")

        # Submit to environment
        step_result = env_step(action)
        reward = step_result["reward"]
        ticket_scores.append(reward["total"])

        # Structured step output for validator
        print(f"[STEP] step={step_num} reward={reward['total']:.4f} feedback=\"{reward['feedback'][:50]}\"", flush=True)

        if step_result["done"]:
            obs = None
        else:
            obs = step_result["observation"]

        time.sleep(0.3)  # Rate limiting

    final_state = env_state()
    task_score = final_state["task_score"]

    print(f"\n  Per-ticket scores: {[round(s, 3) for s in ticket_scores]}")
    print(f"  Task score:        {task_score:.4f}")

    # Structured end output for validator
    print(f"[END] task={task_id} score={task_score:.4f} steps={step_num}", flush=True)

    return {
        "task_id": task_id,
        "task_score": task_score,
        "ticket_scores": ticket_scores,
    }


def main():
    print("Support Triage OpenEnv — Baseline Inference")
    print(f"Model:   {MODEL_NAME}")
    print(f"API URL: {API_BASE_URL}")
    print(f"Env URL: {ENV_BASE_URL}")

    # Health check
    try:
        health = requests.get(f"{ENV_BASE_URL}/health", timeout=10)
        health.raise_for_status()
        print(f"Env health: {health.json()['status']}")
    except Exception as e:
        print(f"[ERROR] Cannot reach environment at {ENV_BASE_URL}: {e}")
        sys.exit(1)

    results = []
    for task_id in TASKS:
        try:
            result = run_task(task_id)
            results.append(result)
        except Exception as e:
            print(f"[ERROR] Task {task_id} failed: {e}")
            results.append({"task_id": task_id, "task_score": 0.0, "ticket_scores": []})

    # Final summary
    print(f"\n{'='*60}")
    print("  FINAL RESULTS")
    print(f"{'='*60}")
    print(f"  {'Task':<20} {'Score':>8}  {'Tickets'}")
    print(f"  {'-'*52}")
    overall_scores = []
    for r in results:
        scores_str = str([round(s, 2) for s in r["ticket_scores"]])
        print(f"  {r['task_id']:<20} {r['task_score']:>8.4f}  {scores_str}")
        overall_scores.append(r["task_score"])

    avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0.0
    print(f"  {'-'*52}")
    print(f"  {'OVERALL AVERAGE':<20} {avg:>8.4f}")
    print(f"{'='*60}\n")

    # Machine-readable output
    output = {
        "model": MODEL_NAME,
        "results": results,
        "overall_average": round(avg, 4),
    }
    with open("baseline_scores.json", "w") as f:
        json.dump(output, f, indent=2)
    print("Scores written to baseline_scores.json")


if __name__ == "__main__":
    main()
