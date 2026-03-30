"""
Support Triage Environment — core logic.
Implements the OpenEnv interface: reset(), step(), state().
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from app.models import (
    Action, EnvironmentState, Observation, Reward, ResetResult, StepResult
)
from tasks.task_definitions import TASKS
from tasks.graders import grade


class SupportTriageEnv:
    """
    Customer support ticket triage environment.

    The agent is presented with tickets one at a time.
    For each ticket it must submit an Action (triage decision).
    The grader scores the action and the next ticket is shown.
    Episode ends when all tickets in the task are processed.
    """

    def __init__(self) -> None:
        self._task_id: str = "task_easy"
        self._tickets: List[Dict] = []
        self._current_index: int = 0
        self._step_count: int = 0
        self._cumulative_reward: float = 0.0
        self._scores_per_ticket: List[float] = []
        self._done: bool = False

    # ── OpenEnv interface ──────────────────────────────────────────────────

    def reset(self, task_id: str = "task_easy") -> ResetResult:
        """
        Reset the environment for the given task.
        Returns the first observation.
        """
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Valid: {list(TASKS.keys())}")

        task = TASKS[task_id]
        self._task_id = task_id
        self._tickets = copy.deepcopy(task["tickets"])
        self._current_index = 0
        self._step_count = 0
        self._cumulative_reward = 0.0
        self._scores_per_ticket = []
        self._done = False

        obs = self._make_observation()
        return ResetResult(
            observation=obs,
            info={
                "task_id": task_id,
                "task_name": task["name"],
                "difficulty": task["difficulty"],
                "total_tickets": len(self._tickets),
                "description": task["description"],
            }
        )

    def step(self, action: Action) -> StepResult:
        """
        Apply the agent's triage action to the current ticket.
        Returns (next_observation | None, reward, done, info).
        """
        if self._done:
            return StepResult(
                observation=None,
                reward=Reward(total=0.0, feedback="Episode already done. Call reset()."),
                done=True,
                info={"warning": "Episode is over"},
            )

        current_ticket = self._tickets[self._current_index]
        ground_truth = current_ticket["_ground_truth"]

        # Grade this action
        reward = grade(action, ground_truth, self._task_id)
        self._scores_per_ticket.append(reward.total)
        self._cumulative_reward += reward.total
        self._step_count += 1

        # Advance
        self._current_index += 1
        done = self._current_index >= len(self._tickets)
        self._done = done

        next_obs = None if done else self._make_observation()

        task_score = self._cumulative_reward / len(self._tickets) if done else None

        info: Dict[str, Any] = {
            "ticket_id": current_ticket["id"],
            "step": self._step_count,
            "ground_truth": {
                k: v for k, v in ground_truth.items()
                if k != "reply_must_include"
            },
        }
        if done:
            info["task_score"] = round(task_score, 4)  # type: ignore[arg-type]
            info["scores_per_ticket"] = self._scores_per_ticket
            info["message"] = "Episode complete."

        return StepResult(
            observation=next_obs,
            reward=reward,
            done=done,
            info=info,
        )

    def state(self) -> EnvironmentState:
        """Return the full internal state of the environment."""
        task_score = (
            self._cumulative_reward / len(self._tickets)
            if self._tickets else 0.0
        )
        return EnvironmentState(
            task_id=self._task_id,
            current_ticket_index=self._current_index,
            total_tickets=len(self._tickets),
            cumulative_reward=round(self._cumulative_reward, 4),
            step_count=self._step_count,
            done=self._done,
            scores_per_ticket=self._scores_per_ticket,
            task_score=round(task_score, 4),
        )

    # ── Private helpers ────────────────────────────────────────────────────

    def _make_observation(self) -> Observation:
        if self._current_index >= len(self._tickets):
            raise IndexError("No more tickets to observe.")

        t = self._tickets[self._current_index]
        return Observation(
            ticket_id=t["id"],
            subject=t["subject"],
            body=t["body"],
            sender_email=t["sender_email"],
            created_at=t["created_at"],
            attachments=t.get("attachments", []),
            history=[],
            step_number=self._step_count,
            task_id=self._task_id,
            tickets_remaining=len(self._tickets) - self._current_index,
            tickets_completed=self._current_index,
        )
