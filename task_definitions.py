"""
Task definitions for the Support Triage environment.
Each task has a list of tickets with ground-truth labels used by graders.
"""
from __future__ import annotations
from typing import Any, Dict, List


# ── Ticket schema ──────────────────────────────────────────────────────────
# Each ticket has:
#   id, subject, body, sender_email, created_at, attachments
#   _ground_truth: {category, urgency, assign_to, needs_escalation, key_topics}

TASK_EASY: Dict[str, Any] = {
    "task_id": "task_easy",
    "name": "Basic Ticket Classification",
    "difficulty": "easy",
    "description": (
        "Classify 5 straightforward tickets. Each ticket has clear, unambiguous "
        "signals indicating category, urgency, and routing."
    ),
    "tickets": [
        {
            "id": "TKT-001",
            "subject": "Cannot login to my account - password not working",
            "body": (
                "Hi support,\n\nI've been trying to log into my account for the past hour "
                "and keep getting 'Invalid credentials'. I've tried resetting my password "
                "twice but the reset email isn't arriving. My account email is john.doe@email.com.\n\n"
                "Please help, I need to access my files urgently for a meeting in 2 hours.\n\nJohn"
            ),
            "sender_email": "john.doe@email.com",
            "created_at": "2024-01-15T09:00:00Z",
            "attachments": [],
            "_ground_truth": {
                "category": "account",
                "urgency": "high",
                "assign_to": "account_team",
                "needs_escalation": False,
                "key_topics": ["login", "password", "reset", "urgent"]
            }
        },
        {
            "id": "TKT-002",
            "subject": "I was charged twice for my subscription this month",
            "body": (
                "Hello,\n\nI just checked my credit card statement and noticed two charges "
                "of $49.99 from your company on the same day (Jan 5th). My account ID is #78234. "
                "I've been a customer for 3 years and this has never happened before.\n\n"
                "Please refund the duplicate charge immediately.\n\nThanks,\nSarah"
            ),
            "sender_email": "sarah.m@company.com",
            "created_at": "2024-01-15T10:30:00Z",
            "attachments": ["bank_statement.pdf"],
            "_ground_truth": {
                "category": "billing",
                "urgency": "medium",
                "assign_to": "billing_team",
                "needs_escalation": False,
                "key_topics": ["duplicate charge", "refund", "subscription"]
            }
        },
        {
            "id": "TKT-003",
            "subject": "Feature request: dark mode for mobile app",
            "body": (
                "Hey team!\n\nLove using your app. One thing I'd love to see is a dark mode "
                "option for the mobile app. I use it a lot at night and the bright white screen "
                "is really harsh on the eyes.\n\nKeep up the great work!\nMike"
            ),
            "sender_email": "mike.t@gmail.com",
            "created_at": "2024-01-15T11:00:00Z",
            "attachments": [],
            "_ground_truth": {
                "category": "feature_request",
                "urgency": "low",
                "assign_to": "product_team",
                "needs_escalation": False,
                "key_topics": ["dark mode", "mobile", "feature request"]
            }
        },
        {
            "id": "TKT-004",
            "subject": "URGENT: Production database completely down - all users affected",
            "body": (
                "This is critical! Our entire production system is down. We are an enterprise "
                "customer (account #ENT-5521) and ALL of our 500+ users cannot access the platform. "
                "Error: 'Service Unavailable 503' across all endpoints. This has been down for "
                "20 minutes and we are losing thousands of dollars per minute.\n\n"
                "Need immediate response. Escalate to your highest technical team NOW.\n\n"
                "— CTO, Acme Corp"
            ),
            "sender_email": "cto@acmecorp.com",
            "created_at": "2024-01-15T14:00:00Z",
            "attachments": ["error_logs.txt"],
            "_ground_truth": {
                "category": "technical",
                "urgency": "critical",
                "assign_to": "technical_team",
                "needs_escalation": True,
                "key_topics": ["outage", "production", "enterprise", "503", "critical"]
            }
        },
        {
            "id": "TKT-005",
            "subject": "How do I export my data as CSV?",
            "body": (
                "Hi,\n\nI'm trying to figure out how to export my data as a CSV file. "
                "I've looked through the help docs but can't find the option. "
                "Can you point me to the right place?\n\nThanks"
            ),
            "sender_email": "user123@yahoo.com",
            "created_at": "2024-01-15T15:00:00Z",
            "attachments": [],
            "_ground_truth": {
                "category": "general",
                "urgency": "low",
                "assign_to": "general_support",
                "needs_escalation": False,
                "key_topics": ["export", "csv", "how-to"]
            }
        }
    ]
}


TASK_MEDIUM: Dict[str, Any] = {
    "task_id": "task_medium",
    "name": "Triage with Partial Information",
    "difficulty": "medium",
    "description": (
        "Handle 5 tickets with ambiguous signals. Agent must infer context "
        "from limited information and correctly route to specialized teams."
    ),
    "tickets": [
        {
            "id": "TKT-101",
            "subject": "Problem with the thing I bought",
            "body": (
                "Hi,\n\nI have a problem with the thing I bought last week. "
                "It says error code E-445 when I try to use it. I've tried restarting. "
                "Please fix this. My order was #ORD-9982.\n\nThanks"
            ),
            "sender_email": "vague.user@email.com",
            "created_at": "2024-01-16T09:00:00Z",
            "attachments": [],
            "_ground_truth": {
                "category": "technical",
                "urgency": "medium",
                "assign_to": "technical_team",
                "needs_escalation": False,
                "key_topics": ["error code", "technical issue"]
            }
        },
        {
            "id": "TKT-102",
            "subject": "My colleague keeps sending me inappropriate messages through your platform",
            "body": (
                "I work at GlobalTech and a colleague has been using the company workspace "
                "to send me uncomfortable messages. I have screenshots. This has been going on "
                "for two weeks and I'm not sure who to report this to internally vs here. "
                "I just want it to stop. The person's username is @james_g_2024."
            ),
            "sender_email": "worried.employee@globaltech.com",
            "created_at": "2024-01-16T10:15:00Z",
            "attachments": ["screenshots.zip"],
            "_ground_truth": {
                "category": "abuse",
                "urgency": "high",
                "assign_to": "trust_safety",
                "needs_escalation": True,
                "key_topics": ["harassment", "workplace", "inappropriate", "abuse report"]
            }
        },
        {
            "id": "TKT-103",
            "subject": "Invoice question",
            "body": (
                "Hello,\n\nI'm looking at invoice #INV-20240112 and the line item for "
                "'Professional Services - Q4' doesn't match what was agreed in our contract. "
                "The contract says $2,500 but we were charged $3,200. "
                "Could be a mistake on our end but want to verify. Not urgent, just want "
                "this resolved before end of month.\n\nBest,\nLinda - Finance Dept"
            ),
            "sender_email": "linda.finance@enterprise-co.com",
            "created_at": "2024-01-16T11:00:00Z",
            "attachments": ["invoice.pdf", "contract_excerpt.pdf"],
            "_ground_truth": {
                "category": "billing",
                "urgency": "medium",
                "assign_to": "billing_team",
                "needs_escalation": False,
                "key_topics": ["invoice dispute", "contract", "overcharge"]
            }
        },
        {
            "id": "TKT-104",
            "subject": "API rate limits seem wrong",
            "body": (
                "We're on the Business plan which advertises 10,000 API calls/hour. "
                "Our monitoring shows we're being throttled at around 3,000/hour. "
                "This started happening about 3 days ago. We haven't changed anything on our end. "
                "Team ID: BIZ-44521. This is impacting our customers."
            ),
            "sender_email": "devops@startupxyz.io",
            "created_at": "2024-01-16T13:00:00Z",
            "attachments": ["api_logs.json"],
            "_ground_truth": {
                "category": "technical",
                "urgency": "high",
                "assign_to": "technical_team",
                "needs_escalation": False,
                "key_topics": ["api", "rate limit", "throttling", "regression"]
            }
        },
        {
            "id": "TKT-105",
            "subject": "Can you delete my account and all my data?",
            "body": (
                "I want to delete my account and have all my personal data permanently removed "
                "per GDPR Article 17 (right to erasure). My account email is jane.smith@email.com. "
                "Please confirm once this is done and provide a deletion certificate."
            ),
            "sender_email": "jane.smith@email.com",
            "created_at": "2024-01-16T14:30:00Z",
            "attachments": [],
            "_ground_truth": {
                "category": "account",
                "urgency": "medium",
                "assign_to": "account_team",
                "needs_escalation": False,
                "key_topics": ["gdpr", "data deletion", "right to erasure", "account closure"]
            }
        }
    ]
}


TASK_HARD: Dict[str, Any] = {
    "task_id": "task_hard",
    "name": "Crisis Triage with Reply Drafting",
    "difficulty": "hard",
    "description": (
        "Handle 5 complex tickets including potential abuse reports, multi-issue "
        "tickets, and angry customers. Must triage correctly AND draft appropriate "
        "professional replies. Quality of the reply is scored."
    ),
    "tickets": [
        {
            "id": "TKT-201",
            "subject": "I WANT A REFUND NOW OR I'M DISPUTING WITH MY BANK",
            "body": (
                "I am FURIOUS. I cancelled my subscription on December 30th — I have the "
                "confirmation email — and you STILL charged me $149 on January 1st. "
                "I have spent 3 hours on your chat bot getting nowhere. This is THEFT. "
                "I am going to dispute this charge with my bank, leave 1-star reviews "
                "everywhere, and contact consumer protection agencies unless this is resolved "
                "TODAY. Account: angry.customer@mail.com. DO SOMETHING."
            ),
            "sender_email": "angry.customer@mail.com",
            "created_at": "2024-01-17T08:00:00Z",
            "attachments": ["cancellation_confirmation.png"],
            "_ground_truth": {
                "category": "billing",
                "urgency": "critical",
                "assign_to": "billing_team",
                "needs_escalation": True,
                "key_topics": ["refund", "cancellation", "chargeback", "escalation"],
                "reply_required": True,
                "reply_tone": "apologetic, empathetic, action-oriented",
                "reply_must_include": ["acknowledge frustration", "confirm review", "specific next step", "timeline"]
            }
        },
        {
            "id": "TKT-202",
            "subject": "Security breach - someone accessed my account",
            "body": (
                "I just received a notification that my account was logged into from "
                "IP address 45.33.32.156 in Russia at 3:47 AM. I did not do this. "
                "I have 2FA enabled but it somehow got through. My account has sensitive "
                "business documents and client contracts. I've already changed my password "
                "but I'm scared the attacker may have downloaded files. "
                "Account: ceo@smallbiz.com"
            ),
            "sender_email": "ceo@smallbiz.com",
            "created_at": "2024-01-17T09:30:00Z",
            "attachments": [],
            "_ground_truth": {
                "category": "technical",
                "urgency": "critical",
                "assign_to": "technical_team",
                "needs_escalation": True,
                "key_topics": ["security breach", "unauthorized access", "2fa bypass", "data exposure"],
                "reply_required": True,
                "reply_tone": "urgent, reassuring, action-focused",
                "reply_must_include": ["acknowledge severity", "immediate steps taken", "security team involvement", "contact for follow-up"]
            }
        },
        {
            "id": "TKT-203",
            "subject": "Multiple issues: billing wrong, feature broken, and need to upgrade",
            "body": (
                "Hi, I have a few things:\n\n"
                "1. My last invoice (#INV-5544) shows 10 seats but I only have 8 users - "
                "please correct this and refund for 2 unused seats.\n\n"
                "2. The bulk export feature has been broken for our team since the Jan 10th "
                "update. We export 50+ reports daily and this is blocking our workflow.\n\n"
                "3. We want to upgrade from Business to Enterprise. Who do we talk to about pricing?\n\n"
                "We're a happy customer overall, just need these sorted. - David, Ops Manager"
            ),
            "sender_email": "david.ops@techfirm.com",
            "created_at": "2024-01-17T10:00:00Z",
            "attachments": ["invoice_5544.pdf"],
            "_ground_truth": {
                "category": "technical",
                "urgency": "high",
                "assign_to": "technical_team",
                "needs_escalation": False,
                "key_topics": ["multi-issue", "billing error", "broken feature", "upgrade inquiry"],
                "reply_required": True,
                "reply_tone": "organized, professional, acknowledging all points",
                "reply_must_include": ["address all 3 issues", "routing for each", "account management for upgrade"]
            }
        },
        {
            "id": "TKT-204",
            "subject": "Report: User posting harmful content targeting minors",
            "body": (
                "I need to report a user on your platform who has been posting what appears "
                "to be grooming content targeting children in the community forums. "
                "Username: @shadow_user_99. I've seen at least 5 posts over the last 2 days. "
                "I have screenshots. I'm reporting this here but also to NCMEC. "
                "This needs immediate action - please don't let this person continue."
            ),
            "sender_email": "concerned.parent@email.com",
            "created_at": "2024-01-17T11:00:00Z",
            "attachments": ["evidence_screenshots.zip"],
            "_ground_truth": {
                "category": "abuse",
                "urgency": "critical",
                "assign_to": "trust_safety",
                "needs_escalation": True,
                "key_topics": ["csam", "child safety", "grooming", "abuse report", "ncmec"],
                "reply_required": True,
                "reply_tone": "serious, reassuring, action-confirming",
                "reply_must_include": ["acknowledge report", "confirm immediate action", "reference to safety team", "thank for reporting"]
            }
        },
        {
            "id": "TKT-205",
            "subject": "Need help migrating 5TB of data before contract ends in 48 hours",
            "body": (
                "We are ending our contract on Jan 19th (48 hours from now) and we need "
                "to export and migrate approximately 5TB of data including databases, "
                "file storage, and user records. Our technical team has tried using the "
                "standard export tool but it keeps timing out after ~100GB. "
                "We have a strict legal obligation to retain this data. "
                "We're willing to pay for expedited support. Enterprise account #ENT-7701."
            ),
            "sender_email": "it.director@departing-corp.com",
            "created_at": "2024-01-17T12:00:00Z",
            "attachments": [],
            "_ground_truth": {
                "category": "technical",
                "urgency": "critical",
                "assign_to": "technical_team",
                "needs_escalation": True,
                "key_topics": ["data migration", "export", "deadline", "enterprise", "offboarding"],
                "reply_required": True,
                "reply_tone": "urgent, solution-focused, professional",
                "reply_must_include": ["acknowledge urgency", "technical escalation", "alternative export method", "dedicated support contact"]
            }
        }
    ]
}


TASKS: Dict[str, Dict] = {
    "task_easy": TASK_EASY,
    "task_medium": TASK_MEDIUM,
    "task_hard": TASK_HARD,
}
