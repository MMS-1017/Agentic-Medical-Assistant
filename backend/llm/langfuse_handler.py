"""
Returns a Langfuse callback handler when keys are configured, else None.
Pass the result into graph.invoke(state, config={"callbacks": [cb]}).
"""

import logging

from backend.config import settings

logger = logging.getLogger(__name__)


def get_langfuse_callback():
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    try:
        from langfuse import Langfuse
        from langfuse.langchain import CallbackHandler
        Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        return CallbackHandler()
    except Exception as exc:
        logger.warning("Langfuse unavailable: %s", exc)
        return None
