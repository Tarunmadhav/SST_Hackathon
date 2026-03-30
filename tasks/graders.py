"""
Graders for the Support Triage environment.

Each grader takes an Action and the ticket's ground truth and returns a Reward.
All scores are in [0.0, 1.0].

Scoring breakdown:
  - category_score  : 0.30 weight
  - urgency_score   : 0.25 weight
  - routing_score   : 0.25 weight
  - escalation_score: 0.10 weight
  - reply_score     : 0.10 weight (only in task_hard)
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.models import Action, Reward, TicketCategory, TicketUrgency, AssignTo


# ── Urgency adjacency (partial credit for close misses) ───────────────────
URGENCY_ORDER = {
    TicketUrgency.CRITICAL: 3,
    TicketUrgency.HIGH: 2,
    TicketUrgency.MEDIUM: 1,
    TicketUrgency.LOW: 0,
}

# Category → expected team mapping (used to cross-check routing)
CATEGORY_TEAM_MAP: Dict[str, str] = {
    "billing": "billing_team",
    "technical": "technical_team",
    "account": "account_team",
    "feature_request": "product_team",
    "abuse": "trust_safety",
    "general": "general_support",
}


def score_category(predicted: str, truth: str) -> float:
    """1.0 for exact match, 0.0 otherwise."""
    return 1.0 if predicted == truth else 0.0


def score_urgency(predicted: str, truth: str) -> float:
    """
    Full credit for exact match.
    Partial credit (0.5) for adjacent levels.
    Zero for misses ≥2 levels away.
    """
    pred_val = URGENCY_ORDER.get(TicketUrgency(predicted), -1)
    truth_val = URGENCY_ORDER.get(TicketUrgency(truth), -1)
    diff = abs(pred_val - truth_val)
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.5
    else:
        return 0.0


def score_routing(predicted: str, truth: str, category: str) -> float:
    """
    Full credit for exact team match.
    Partial credit (0.4) if routed to the canonical team for the correct category
    (catches cases where agent got category right but slightly wrong team name).
    """
    if predicted == truth:
        return 1.0
    # partial: if category is right, the "natural" team routing is acceptable
    expected_from_category = CATEGORY_TEAM_MAP.get(category, "")
    if predicted == expected_from_category:
        return 0.6
    return 0.0


def score_escalation(predicted: bool, truth: bool) -> float:
    """1.0 for correct escalation decision, 0.5 for false negative, 0.0 for false positive on critical items."""
    if predicted == truth:
        return 1.0
    # False negative (missed escalation) on a ticket that needs it — penalize less
    if truth and not predicted:
        return 0.3
    # False positive (unnecessary escalation) — minor penalty
    return 0.6


def score_reply(draft: Optional[str], ground_truth: Dict) -> float:
    """
    Score reply quality for task_hard.
    Checks:
      - Reply is non-empty and non-trivial (>50 chars)
      - Covers required topics from reply_must_include
      - Tone signals detected via keywords
    Returns 0.0–1.0.
    """
    if not ground_truth.get("reply_required", False):
        return 1.0  # Not required, skip

    if not draft or len(draft.strip()) < 50:
        return 0.0

    text_lower = draft.lower()
    score = 0.0

    # Base score for a non-trivial reply
    score += 0.3

    # Check for required content signals
    must_include: list = ground_truth.get("reply_must_include", [])
    if must_include:
        hits = 0
        # Keyword maps for each required element
        signal_keywords = {
            "acknowledge frustration": ["apologize", "sorry", "understand", "frustrat"],
            "confirm review": ["look into", "review", "investigate", "check"],
            "specific next step": ["will", "refund", "escalat", "team", "within"],
            "timeline": ["hour", "day", "business", "soon", "immediately"],
            "acknowledge severity": ["serious", "urgent", "security", "immediate"],
            "immediate steps taken": ["locked", "suspend", "investigat", "team"],
            "security team involvement": ["security team", "security", "protect"],
            "contact for follow-up": ["contact", "reach", "email", "call"],
            "address all 3 issues": ["billing", "export", "upgrade", "enterprise"],
            "routing for each": ["team", "route", "forward", "specialist"],
            "account management for upgrade": ["account manager", "sales", "enterprise team"],
            "acknowledge report": ["report", "received", "thank"],
            "confirm immediate action": ["immediate", "action", "taken", "investigat"],
            "reference to safety team": ["safety", "trust", "team"],
            "thank for reporting": ["thank", "grateful", "appreciate"],
            "acknowledge urgency": ["urgent", "48 hour", "deadline", "understand"],
            "technical escalation": ["team", "engineer", "technical"],
            "alternative export method": ["alternative", "method", "api", "manual", "direct"],
            "dedicated support contact": ["contact", "dedicated", "direct", "engineer"],
            "apologetic, empathetic, action-oriented": ["sorry", "understand", "will"],
        }
        for item in must_include:
            kws = signal_keywords.get(item, [item.lower().split()[0]])
            if any(kw in text_lower for kw in kws):
                hits += 1
        coverage = hits / max(len(must_include), 1)
        score += 0.7 * coverage

    return min(score, 1.0)


# ── Weights per task ───────────────────────────────────────────────────────

TASK_WEIGHTS = {
    "task_easy": {
        "category": 0.35,
        "urgency": 0.30,
        "routing": 0.25,
        "escalation": 0.10,
        "reply": 0.00,
    },
    "task_medium": {
        "category": 0.30,
        "urgency": 0.25,
        "routing": 0.30,
        "escalation": 0.15,
        "reply": 0.00,
    },
    "task_hard": {
        "category": 0.20,
        "urgency": 0.20,
        "routing": 0.20,
        "escalation": 0.15,
        "reply": 0.25,
    },
}


def grade(action: Action, ground_truth: Dict, task_id: str) -> Reward:
    """
    Grade a single ticket action against ground truth.
    Returns a Reward with all sub-scores and total.
    """
    weights = TASK_WEIGHTS.get(task_id, TASK_WEIGHTS["task_easy"])

    cat_score = score_category(action.category.value, ground_truth["category"])
    urg_score = score_urgency(action.urgency.value, ground_truth["urgency"])
    rout_score = score_routing(
        action.assign_to.value,
        ground_truth["assign_to"],
        ground_truth["category"]
    )
    esc_score = score_escalation(action.needs_escalation, ground_truth["needs_escalation"])
    rep_score = score_reply(action.draft_reply, ground_truth)

    total = (
        weights["category"] * cat_score
        + weights["urgency"] * urg_score
        + weights["routing"] * rout_score
        + weights["escalation"] * esc_score
        + weights["reply"] * rep_score
    )
    total = round(min(max(total, 0.0), 1.0), 4)

    # Build human-readable feedback
    parts = []
    if cat_score < 1.0:
        parts.append(f"category should be '{ground_truth['category']}' (got '{action.category.value}')")
    if urg_score < 1.0:
        parts.append(f"urgency should be '{ground_truth['urgency']}' (got '{action.urgency.value}')")
    if rout_score < 1.0:
        parts.append(f"routing should be '{ground_truth['assign_to']}' (got '{action.assign_to.value}')")
    if esc_score < 1.0:
        flag = "needed" if ground_truth["needs_escalation"] else "not needed"
        parts.append(f"escalation was {flag}")
    if weights["reply"] > 0 and rep_score < 0.6:
        parts.append("reply quality needs improvement (check coverage of required topics)")

    feedback = "Perfect triage!" if not parts else "Issues: " + "; ".join(parts)

    return Reward(
        total=total,
        category_score=round(cat_score, 4),
        urgency_score=round(urg_score, 4),
        routing_score=round(rout_score, 4),
        reply_score=round(rep_score, 4),
        escalation_score=round(esc_score, 4),
        feedback=feedback,
    )
