from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from app.core.config import settings


GROQ_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"
ALLOW_LLM_DURING_TESTS_ENV = "DOORIQ_ALLOW_LLM_DURING_TESTS"

SYSTEM_PROMPT = """You write concise answers for DoorIQ, a commercial door and hardware chatbot.
Use only the supplied structured context.
Do not invent exact code sections, local amendments, product specs, prices, or approvals.
Keep the answer practical for contractors, architects, property owners, and developers.
Mention human/AHJ review when the context says it is needed.
You may receive background facts from previous turns in the conversation. Focus your answer on the user's newest question. Do not awkwardly repeat previous answers. If the user shifts the topic to a completely new building type or scenario, ignore conflicting background facts from the old scenario.
When answering code or compliance questions, you MUST explicitly cite the exact Source Document and Page Number if it is provided in your context.
CRITICAL RULE: If your context already contains enough information to answer the question, give the direct answer FIRST with the code citation. Only AFTER giving the answer, you may optionally ask for jurisdiction or other details to refine further. Never block the answer just because jurisdiction is missing — provide the general code answer and note that local amendments may vary."""


def _provider_config() -> tuple[str, str, str, str | None] | None:
    if os.getenv("PYTEST_CURRENT_TEST") and not os.getenv(ALLOW_LLM_DURING_TESTS_ENV):
        return None

    if settings.openai_api_key:
        return ("openai", settings.openai_api_key, settings.openai_chat_model, None)

    if settings.groq_api_key:
        return ("groq", settings.groq_api_key, settings.groq_chat_model, GROQ_OPENAI_BASE_URL)

    return None


def get_llm_provider_name() -> str | None:
    provider_config = _provider_config()
    return provider_config[0] if provider_config else None


def _client_for_provider(api_key: str, base_url: str | None) -> OpenAI:
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)

    return OpenAI(api_key=api_key)


def generate_llm_answer(
    *,
    context: dict[str, Any],
    fallback_answer: str,
) -> str:
    provider_config = _provider_config()
    if provider_config is None:
        return fallback_answer

    _, api_key, model, base_url = provider_config
    client = _client_for_provider(api_key, base_url)

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(context, ensure_ascii=False, indent=2),
                },
            ],
            temperature=0.2,
            max_completion_tokens=550,
        )
    except Exception:
        return fallback_answer

    answer = completion.choices[0].message.content
    if not answer:
        return fallback_answer

    return answer.strip()
