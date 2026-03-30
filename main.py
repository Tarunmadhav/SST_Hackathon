"""
Support Triage OpenEnv — FastAPI server.
Exposes: POST /reset, POST /step, GET /state, GET /health
"""
from __future__ import annotations

from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.environment import SupportTriageEnv
from app.models import (
    Action, EnvironmentState, ResetResult, StepResult
)

app = FastAPI(
    title="Support Triage OpenEnv",
    description=(
        "Customer support ticket triage environment. "
        "An AI agent reads support tickets and makes triage decisions: "
        "categorize, set urgency, route to the correct team, and optionally "
        "draft a reply. Full OpenEnv spec compliance."
    ),
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single global environment instance (stateful)
env = SupportTriageEnv()


# ── Request schemas ────────────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = "task_easy"


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Ping endpoint. Must return 200 for pre-submission check."""
    return {"status": "ok", "env": "support-triage", "version": "1.0.0"}


@app.post("/reset", response_model=ResetResult)
def reset(request: ResetRequest):
    """
    Reset the environment for a given task.
    Returns the first observation.

    task_id: one of ['task_easy', 'task_medium', 'task_hard']
    """
    try:
        result = env.reset(task_id=request.task_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResult)
def step(action: Action):
    """
    Submit a triage action for the current ticket.
    Returns the next observation, reward breakdown, done flag, and info.
    """
    result = env.step(action)
    return result


@app.get("/state", response_model=EnvironmentState)
def state():
    """Return the full internal environment state."""
    return env.state()


# ── Gradio UI (optional, for HF Space) ────────────────────────────────────

try:
    import gradio as gr
    import json

    def gradio_reset(task_id: str):
        result = env.reset(task_id=task_id)
        return json.dumps(result.model_dump(), indent=2)

    def gradio_step(
        category, urgency, assign_to, draft_reply, needs_escalation, tags_str
    ):
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        action = Action(
            category=category,
            urgency=urgency,
            assign_to=assign_to,
            draft_reply=draft_reply or None,
            needs_escalation=needs_escalation,
            tags=tags,
        )
        result = env.step(action)
        return json.dumps(result.model_dump(), indent=2)

    def gradio_state():
        return json.dumps(env.state().model_dump(), indent=2)

    with gr.Blocks(title="Support Triage OpenEnv") as demo:
        gr.Markdown("# 🎫 Support Triage OpenEnv")
        gr.Markdown(
            "A customer support ticket triage environment. "
            "Reset to start a task, then submit triage actions ticket by ticket."
        )

        with gr.Tab("Reset"):
            task_dd = gr.Dropdown(
                choices=["task_easy", "task_medium", "task_hard"],
                value="task_easy",
                label="Task ID",
            )
            reset_btn = gr.Button("Reset")
            reset_out = gr.Code(label="First Observation", language="json")
            reset_btn.click(gradio_reset, inputs=[task_dd], outputs=[reset_out])

        with gr.Tab("Step"):
            with gr.Row():
                cat_dd = gr.Dropdown(
                    choices=["billing", "technical", "account", "feature_request", "abuse", "general"],
                    label="Category",
                )
                urg_dd = gr.Dropdown(
                    choices=["critical", "high", "medium", "low"],
                    label="Urgency",
                )
                assign_dd = gr.Dropdown(
                    choices=["billing_team", "technical_team", "account_team",
                             "trust_safety", "product_team", "general_support"],
                    label="Assign To",
                )
            draft_tb = gr.Textbox(label="Draft Reply (optional)", lines=4)
            esc_cb = gr.Checkbox(label="Needs Escalation")
            tags_tb = gr.Textbox(label="Tags (comma-separated)", value="")
            step_btn = gr.Button("Submit Action")
            step_out = gr.Code(label="Step Result", language="json")
            step_btn.click(
                gradio_step,
                inputs=[cat_dd, urg_dd, assign_dd, draft_tb, esc_cb, tags_tb],
                outputs=[step_out],
            )

        with gr.Tab("State"):
            state_btn = gr.Button("Get State")
            state_out = gr.Code(label="Environment State", language="json")
            state_btn.click(gradio_state, inputs=[], outputs=[state_out])

    # Mount Gradio on FastAPI
    from gradio.routes import mount_gradio_app
    app = mount_gradio_app(app, demo, path="/ui")

except ImportError:
    pass  # Gradio optional


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=7860, reload=False)
