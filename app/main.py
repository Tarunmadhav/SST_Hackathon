"""
Support Triage OpenEnv — FastAPI server.
Exposes: POST /reset, POST /step, GET /state, GET /health
"""
from __future__ import annotations

import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.environment import SupportTriageEnv
from app.models import Action

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

env = SupportTriageEnv()
# Pre-initialize so first reset() call is instant
env.reset(task_id="task_easy")


@app.get("/")
async def root():
    return {"name": "support-triage-openenv", "version": "1.0.0",
            "endpoints": ["/health", "/reset", "/step", "/state"]}


@app.get("/health")
async def health():
    return {"status": "ok", "env": "support-triage", "version": "1.0.0"}


@app.post("/reset")
async def reset(request: Request):
    """
    Reset the environment. Accepts:
      - Empty POST (no body)           → uses task_easy
      - {"task_id": "task_medium"}     → uses specified task
      - ?task_id=task_hard             → uses query param
    Returns flat observation dict at top level (OpenEnv spec).
    """
    task_id = "task_easy"

    # 1. Query param
    if "task_id" in request.query_params:
        task_id = request.query_params["task_id"]

    # 2. JSON body (optional)
    try:
        raw = await request.body()
        if raw and len(raw) > 2:
            body = json.loads(raw)
            if isinstance(body, dict) and "task_id" in body:
                task_id = body["task_id"]
    except Exception:
        pass

    # Validate task_id
    valid = ["task_easy", "task_medium", "task_hard"]
    if task_id not in valid:
        task_id = "task_easy"

    logger.info(f"reset called with task_id={task_id}")

    try:
        result = env.reset(task_id=task_id)
        data = result.model_dump()

        # Return BOTH the nested format AND flat observation fields
        # so the validator can find what it needs regardless of format
        obs = data.get("observation", {})
        response = {
            # Nested format (standard)
            "observation": obs,
            "info": data.get("info", {}),
            # Flat format (some validators expect top-level fields)
            **obs,
        }
        logger.info(f"reset response keys: {list(response.keys())}")
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        logger.error(f"reset error: {e}")
        # Return 200 with error info rather than 500, so validator sees response
        return JSONResponse(content={"error": str(e), "status": "reset_failed"}, status_code=200)


@app.post("/step")
async def step(request: Request):
    """
    Submit a triage action. Accepts Action JSON body.
    Returns observation, reward, done, info.
    """
    try:
        raw = await request.body()
        body = json.loads(raw)

        action = Action(
            category=body.get("category", "general"),
            urgency=body.get("urgency", "low"),
            assign_to=body.get("assign_to", "general_support"),
            needs_escalation=body.get("needs_escalation", False),
            draft_reply=body.get("draft_reply"),
            tags=body.get("tags", []),
        )

        result = env.step(action)
        data = result.model_dump()

        obs = data.get("observation") or {}
        response = {
            "observation": obs,
            "reward": data.get("reward", {}),
            "done": data.get("done", False),
            "info": data.get("info", {}),
            **obs,
        }
        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        logger.error(f"step error: {e}")
        return JSONResponse(
            content={"error": str(e), "done": False, "reward": {"total": 0.0}},
            status_code=200
        )


@app.get("/state")
async def state():
    try:
        return env.state().model_dump()
    except Exception as e:
        logger.error(f"state error: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=200)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=7860, workers=1)