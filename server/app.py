"""
server/app.py — OpenEnv required server entry point.
This is the [project.scripts] server entry point required by openenv validate.
It starts the FastAPI app on port 7860.
"""
import uvicorn


def main():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=7860,
        workers=1,
        log_level="info",
    )


# Also expose the FastAPI app directly for import
from app.main import app

if __name__ == "__main__":
    main()