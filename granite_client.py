"""
IBM Granite LLM client using ibm-watsonx-ai SDK (IBM Cloud Lite).
Handles all AI generation requests for the Travel Planner Agent.
"""
import logging
from typing import Optional
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenChatParamsMetaNames as ChatParams
from config import Config

logger = logging.getLogger(__name__)


class GraniteClient:
    """Wrapper around IBM Granite model via watsonx.ai."""

    def __init__(self):
        self._client: Optional[ModelInference] = None
        self._initialized = False

    def _init_client(self):
        """Lazy-initialise the watsonx.ai model client."""
        if self._initialized:
            return
        missing = Config.validate()
        if missing:
            raise EnvironmentError(
                f"Missing IBM watsonx.ai credentials: {', '.join(missing)}. "
                "Please update your .env file."
            )
        credentials = Credentials(
            url=Config.IBM_WATSONX_URL,
            api_key=Config.IBM_WATSONX_API_KEY,
        )
        self._client = ModelInference(
            model_id=Config.IBM_GRANITE_MODEL_ID,
            credentials=credentials,
            project_id=Config.IBM_WATSONX_PROJECT_ID,
            validate=False,
            params={
                ChatParams.MAX_TOKENS: Config.GRANITE_MAX_TOKENS,
                ChatParams.TEMPERATURE: Config.GRANITE_TEMPERATURE,
                ChatParams.TOP_P: Config.GRANITE_TOP_P,
            },
        )
        self._initialized = True
        logger.info("IBM Granite client initialised — model: %s", Config.IBM_GRANITE_MODEL_ID)

    def generate(self, prompt: str, max_tokens: int = None) -> str:
        """
        Generate text from Granite given a prompt string.
        Uses chat_messages API internally (required by granite-4-h-small).
        """
        self._init_client()
        messages = [{"role": "user", "content": prompt}]
        try:
            response = self._client.chat(messages=messages)
            text = (
                response.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )
            return text.strip() if text else ""
        except Exception as exc:
            logger.error("Granite generation error: %s", exc)
            raise

    def chat(self, messages: list[dict]) -> str:
        """
        Chat-style generation using a list of {role, content} dicts.
        Passes messages directly to the chat API.
        """
        self._init_client()
        # granite-4-h-small uses the native chat messages format
        try:
            response = self._client.chat(messages=messages)
            text = (
                response.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
            )
            return text.strip() if text else ""
        except Exception as exc:
            logger.error("Granite generation error: %s", exc)
            raise


    def stream(self, messages: list[dict]):
        """
        Stream chat response token-by-token using the watsonx.ai streaming API.
        Yields text chunks as they arrive.
        """
        self._init_client()
        try:
            for chunk in self._client.chat_stream(messages=messages):
                text = (
                    chunk.get("choices", [{}])[0]
                        .get("delta", {})
                        .get("content", "")
                )
                if text:
                    yield text
        except Exception as exc:
            logger.error("Granite stream error: %s", exc)
            raise


# Module-level singleton
granite = GraniteClient()
