"""
Typed Pydantic models for the Support Triage OpenEnv environment.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────

class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    ABUSE = "abuse"
    GENERAL = "general"


class TicketUrgency(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssignTo(str, Enum):
    BILLING_TEAM = "billing_team"
    TECHNICAL_TEAM = "technical_team"
    ACCOUNT_TEAM = "account_team"
    TRUST_SAFETY = "trust_safety"
    PRODUCT_TEAM = "product_team"
    GENERAL_SUPPORT = "general_support"


# ── Sub-models ─────────────────────────────────────────────────────────────

class TicketMessage(BaseModel):
    role: str = Field(..., description="'customer' or 'agent'")
    content: str
    timestamp: str


class Observation(BaseModel):
    """What the agent sees at each step."""
    ticket_id: str
    subject: str
    body: str
    sender_email: str
    created_at: str
    attachments: List[str] = Field(default_factory=list)
    history: List[TicketMessage] = Field(default_factory=list)
    step_number: int = 0
    task_id: str = ""
    tickets_remaining: int = 0
    tickets_completed: int = 0


class Action(BaseModel):
    """The agent's triage decision for the current ticket."""
    category: TicketCategory
    urgency: TicketUrgency
    assign_to: AssignTo
    draft_reply: Optional[str] = Field(
        default=None,
        description="Draft reply to send to the customer"
    )
    needs_escalation: bool = False
    tags: List[str] = Field(default_factory=list)


class Reward(BaseModel):
    """Reward breakdown for the current action."""
    total: float = Field(..., ge=0.0, le=1.0)
    category_score: float = Field(0.0, ge=0.0, le=1.0)
    urgency_score: float = Field(0.0, ge=0.0, le=1.0)
    routing_score: float = Field(0.0, ge=0.0, le=1.0)
    reply_score: float = Field(0.0, ge=0.0, le=1.0)
    escalation_score: float = Field(0.0, ge=0.0, le=1.0)
    feedback: str = ""


class StepResult(BaseModel):
    """Response from step()."""
    observation: Optional[Observation]
    reward: Reward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class ResetResult(BaseModel):
    """Response from reset()."""
    observation: Observation
    info: Dict[str, Any] = Field(default_factory=dict)


class EnvironmentState(BaseModel):
    """Full internal state, returned by state()."""
    task_id: str
    current_ticket_index: int
    total_tickets: int
    cumulative_reward: float
    step_count: int
    done: bool
    scores_per_ticket: List[float]
    task_score: float
