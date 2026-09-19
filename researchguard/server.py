"""Loopback-only Uvicorn launcher for the FastAPI application."""
import argparse

import uvicorn

from .local_env import load_local_env


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser(description="Research Guard AI loopback preview")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run("researchguard.api:app", host="127.0.0.1", port=args.port, access_log=False)


if __name__ == "__main__":
    main()
