from types import SimpleNamespace

from app.core.config import settings
from app.services import llm_service
from app.services.llm_service import generate_llm_answer, get_llm_provider_name


class FakeCompletions:
    def __init__(self, answer: str = "Generated answer") -> None:
        self.answer = answer
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self.answer)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class FakeOpenAI:
    instances = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)
        self.__class__.instances.append(self)


def _clear_keys(monkeypatch) -> None:
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "groq_api_key", None)


def test_llm_returns_template_when_no_provider_key(monkeypatch) -> None:
    _clear_keys(monkeypatch)

    assert get_llm_provider_name() is None
    assert generate_llm_answer(context={}, fallback_answer="Template") == "Template"


def test_llm_uses_openai_before_groq(monkeypatch) -> None:
    FakeOpenAI.instances = []
    monkeypatch.setenv("DOORIQ_ALLOW_LLM_DURING_TESTS", "1")
    monkeypatch.setattr(llm_service, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(settings, "openai_api_key", "openai-key")
    monkeypatch.setattr(settings, "groq_api_key", "groq-key")
    monkeypatch.setattr(settings, "openai_chat_model", "openai-model")

    answer = generate_llm_answer(
        context={"intent": "product_match"},
        fallback_answer="Template",
    )

    assert answer == "Generated answer"
    assert get_llm_provider_name() == "openai"
    assert FakeOpenAI.instances[0].kwargs == {"api_key": "openai-key"}
    assert FakeOpenAI.instances[0].completions.calls[0]["model"] == "openai-model"


def test_llm_uses_groq_when_openai_key_is_missing(monkeypatch) -> None:
    FakeOpenAI.instances = []
    monkeypatch.setenv("DOORIQ_ALLOW_LLM_DURING_TESTS", "1")
    monkeypatch.setattr(llm_service, "OpenAI", FakeOpenAI)
    monkeypatch.setattr(settings, "openai_api_key", None)
    monkeypatch.setattr(settings, "groq_api_key", "groq-key")
    monkeypatch.setattr(settings, "groq_chat_model", "groq-model")

    answer = generate_llm_answer(
        context={"intent": "product_match"},
        fallback_answer="Template",
    )

    assert answer == "Generated answer"
    assert get_llm_provider_name() == "groq"
    assert FakeOpenAI.instances[0].kwargs == {
        "api_key": "groq-key",
        "base_url": "https://api.groq.com/openai/v1",
    }
    assert FakeOpenAI.instances[0].completions.calls[0]["model"] == "groq-model"


def test_llm_falls_back_when_provider_call_fails(monkeypatch) -> None:
    class FailingOpenAI:
        def __init__(self, **kwargs) -> None:
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **_: (_ for _ in ()).throw(RuntimeError("boom"))
                )
            )

    monkeypatch.setattr(llm_service, "OpenAI", FailingOpenAI)
    monkeypatch.setenv("DOORIQ_ALLOW_LLM_DURING_TESTS", "1")
    monkeypatch.setattr(settings, "openai_api_key", "openai-key")
    monkeypatch.setattr(settings, "groq_api_key", None)

    assert generate_llm_answer(context={}, fallback_answer="Template") == "Template"
