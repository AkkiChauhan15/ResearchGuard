"""Compatibility entry point; use ``verify_review_provider_live`` for any provider."""
from scripts.verify_review_provider_live import main


if __name__ == "__main__":
    raise SystemExit(main())
