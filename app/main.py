"""
Support Triage OpenEnv — FastAPI server.
Exposes: POST /reset, POST /step, GET /state, GET /health

OpenEnv spec: reset() must work with NO body (empty POST),
optionally accepting {"task_id": "..."} in the body or as query param.
"""
from __future__ import annotations

import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.environment import SupportTriageEnv
from app.models import Action

app = FastAPI(
    title="Support Triage OpenEnv",
    description="Customer support ticket triage environment. Full OpenEnv spec compliance.",
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


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "support-triage-openenv",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "reset": "POST /reset",
            "step": "POST /step",
            "state": "GET /state",
            "docs": "GET /docs",
        }
    }


@app.get("/health")
async def health():
    """Ping endpoint — must return 200."""
    return {"status": "ok", "env": "support-triage", "version": "1.0.0"}


@app.post("/reset")
async def reset(request: Request):
    """
    Reset the environment.

    Works with:
      POST /reset                         → defaults to task_easy
      POST /reset  {"task_id":"task_hard"} → specified task
      POST /reset?task_id=task_medium     → query param

    Always returns 200 with the first observation JSON.
    """
    task_id = "task_easy"

    # Check query param first
    if "task_id" in request.query_params:
        task_id = request.query_params["task_id"]

    # Try to parse optional JSON body
    try:
        body_bytes = await request.body()
        if body_bytes and len(body_bytes) > 2:
            body = json.loads(body_bytes)
            if isinstance(body, dict) and "task_id" in body:
                task_id = body["task_id"]
    except Exception:
        pass  # Empty or non-JSON body is fine

    try:
        result = env.reset(task_id=task_id)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@app.post("/step")
async def step(action: Action):
    """
    Submit a triage action for the current ticket.
    Returns next observation, reward breakdown, done flag, and info.
    """
    try:
        result = env.step(action)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step failed: {str(e)}")


@app.get("/state")
async def state():
    """Return the full internal environment state."""
    try:
        return env.state().model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"State failed: {str(e)}")


# ── Gradio UI (optional) ───────────────────────────────────────────────────

def _mount_gradio():
    try:
        import gradio as gr
        from gradio.routes import mount_gradio_app

        def gradio_reset(task_id: str):
            result = env.reset(task_id=task_id)
            return json.dumps(result.model_dump(), indent=2)

        def gradio_step(category, urgency, assign_to, draft_reply, needs_escalation, tags_str):
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]
            action = Action(
                category=category, urgency=urgency, assign_to=assign_to,
                draft_reply=draft_reply or None, needs_escalation=needs_escalation, tags=tags,
            )
            result = env.step(action)
            return json.dumps(result.model_dump(), indent=2)

        def gradio_state():
            return json.dumps(env.state().model_dump(), indent=2)

        with gr.Blocks(title="Support Triage OpenEnv") as demo:
            gr.Markdown("# 🎫 Support Triage OpenEnv")
            with gr.Tab("Reset"):
                task_dd = gr.Dropdown(choices=["task_easy","task_medium","task_hard"],
                                      value="task_easy", label="Task ID")
                reset_btn = gr.Button("Reset Environment")
                reset_out = gr.Code(label="First Observation", language="json")
                reset_btn.click(gradio_reset, inputs=[task_dd], outputs=[reset_out])
            with gr.Tab("Step"):
                with gr.Row():
                    cat_dd = gr.Dropdown(
                        choices=["billing","technical","account","feature_request","abuse","general"],
                        label="Category")
                    urg_dd = gr.Dropdown(choices=["critical","high","medium","low"], label="Urgency")
                    assign_dd = gr.Dropdown(
                        choices=["billing_team","technical_team","account_team",
                                 "trust_safety","product_team","general_support"],
                        label="Assign To")
                draft_tb = gr.Textbox(label="Draft Reply (optional)", lines=3)
                with gr.Row():
                    esc_cb = gr.Checkbox(label="Needs Escalation")
                    tags_tb = gr.Textbox(label="Tags (comma-separated)", value="")
                step_btn = gr.Button("Submit Action")
                step_out = gr.Code(label="Step Result", language="json")
                step_btn.click(gradio_step,
                               inputs=[cat_dd, urg_dd, assign_dd, draft_tb, esc_cb, tags_tb],
                               outputs=[step_out])
            with gr.Tab("State"):
                state_btn = gr.Button("Get State")
                state_out = gr.Code(label="Environment State", language="json")
                state_btn.click(gradio_state, inputs=[], outputs=[state_out])

        return mount_gradio_app(app, demo, path="/ui")
    except ImportError:
        return app


app = _mount_gradio()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=7860, reload=False)
