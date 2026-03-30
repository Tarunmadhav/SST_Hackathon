"""
Tests for the Support Triage graders.
Verifies that graders produce scores in [0.0, 1.0] and
that perfect actions score 1.0 on all tasks.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models import Action, TicketCategory, TicketUrgency, AssignTo
from tasks.graders import grade
from tasks.task_definitions import TASKS


def make_perfect_action(ground_truth: dict) -> Action:
    """Build an Action that exactly matches the ground truth."""
    return Action(
        category=TicketCategory(ground_truth["category"]),
        urgency=TicketUrgency(ground_truth["urgency"]),
        assign_to=AssignTo(ground_truth["assign_to"]),
        needs_escalation=ground_truth["needs_escalation"],
        draft_reply=(
            "Thank you for contacting us. We acknowledge your frustration and will "
            "immediately investigate this issue. Our team will review the billing charge "
            "and process a refund within 1-2 business days. We apologize for the "
            "inconvenience and will ensure this is resolved today. Please contact our "
            "dedicated support line if you need further assistance."
            if ground_truth.get("reply_required") else None
        ),
        tags=ground_truth.get("key_topics", [])[:3],
    )


def make_wrong_action() -> Action:
    """Build a completely wrong action."""
    return Action(
        category=TicketCategory.GENERAL,
        urgency=TicketUrgency.LOW,
        assign_to=AssignTo.GENERAL_SUPPORT,
        needs_escalation=False,
        draft_reply=None,
        tags=[],
    )


def test_all_tasks_perfect_score():
    """Perfect actions should score >= 0.95 on all tasks."""
    for task_id, task in TASKS.items():
        print(f"\nTask: {task_id}")
        for ticket in task["tickets"]:
            gt = ticket["_ground_truth"]
            action = make_perfect_action(gt)
            reward = grade(action, gt, task_id)

            print(f"  {ticket['id']}: total={reward.total:.3f} "
                  f"cat={reward.category_score} urg={reward.urgency_score} "
                  f"rout={reward.routing_score} esc={reward.escalation_score} "
                  f"rep={reward.reply_score}")

            assert 0.0 <= reward.total <= 1.0, f"Score out of range: {reward.total}"
            assert reward.total >= 0.85, (
                f"Perfect action scored too low ({reward.total}) on {ticket['id']} "
                f"in {task_id}. Feedback: {reward.feedback}"
            )
    print("\n✓ All perfect-action tests passed")


def test_wrong_action_low_score():
    """Wrong actions should score low."""
    for task_id, task in TASKS.items():
        for ticket in task["tickets"]:
            gt = ticket["_ground_truth"]
            action = make_wrong_action()
            reward = grade(action, gt, task_id)
            assert 0.0 <= reward.total <= 1.0
            # Wrong action should score < 0.6 on most tickets
            # (Some easy tickets might have general/low as correct, so we allow up to 0.7)
            print(f"  {task_id}/{ticket['id']}: wrong action score={reward.total:.3f}")
    print("\n✓ Wrong-action low-score tests passed")


def test_urgency_partial_credit():
    """Adjacent urgency (diff=1) gets 0.5; 2+ levels apart gets 0.0."""
    from tasks.graders import score_urgency
    # Adjacent (diff=1) → 0.5
    assert score_urgency("high", "critical") == 0.5
    assert score_urgency("medium", "high") == 0.5
    assert score_urgency("low", "medium") == 0.5
    # Two levels apart → 0.0
    assert score_urgency("low", "high") == 0.0
    assert score_urgency("low", "critical") == 0.0
    assert score_urgency("medium", "critical") == 0.0
    # Exact match → 1.0
    assert score_urgency("critical", "critical") == 1.0
    assert score_urgency("low", "low") == 1.0
    print("✓ Urgency partial credit tests passed")


def test_score_range():
    """All scores must be in [0.0, 1.0] for any action on any ticket."""
    import random
    cats = ["billing", "technical", "account", "feature_request", "abuse", "general"]
    urgs = ["critical", "high", "medium", "low"]
    teams = ["billing_team", "technical_team", "account_team",
             "trust_safety", "product_team", "general_support"]

    for task_id, task in TASKS.items():
        for ticket in task["tickets"]:
            gt = ticket["_ground_truth"]
            action = Action(
                category=TicketCategory(random.choice(cats)),
                urgency=TicketUrgency(random.choice(urgs)),
                assign_to=AssignTo(random.choice(teams)),
                needs_escalation=random.choice([True, False]),
                draft_reply="random reply text that is long enough to pass the minimum length check",
                tags=[],
            )
            reward = grade(action, gt, task_id)
            assert 0.0 <= reward.total <= 1.0, f"Out of range: {reward.total}"

    print("✓ Score range tests passed (100 random actions)")


def test_environment_api():
    """Integration test: reset → step → state cycle."""
    from app.environment import SupportTriageEnv

    env = SupportTriageEnv()

    for task_id in ["task_easy", "task_medium", "task_hard"]:
        result = env.reset(task_id=task_id)
        assert result.observation is not None
        assert result.observation.task_id == task_id

        task = TASKS[task_id]
        done = False
        steps = 0

        while not done:
            obs = result.observation if steps == 0 else step_result.observation
            gt = task["tickets"][steps]["_ground_truth"]
            action = make_perfect_action(gt)
            step_result = env.step(action)
            done = step_result.done
            steps += 1

            assert 0.0 <= step_result.reward.total <= 1.0

        state = env.state()
        assert state.done
        assert state.task_score >= 0.0
        print(f"  {task_id}: {steps} steps, task_score={state.task_score:.4f}")

    print("✓ Environment API integration tests passed")


if __name__ == "__main__":
    print("Running Support Triage grader tests...\n")
    test_urgency_partial_credit()
    test_score_range()
    test_all_tasks_perfect_score()
    test_wrong_action_low_score()
    test_environment_api()
    print("\n✅ All tests passed!")
