import pytest

from app.services.llm_service import LLMService
from tests.fakes.fake_gemini_client import FakeGeminiClient


@pytest.mark.asyncio
async def test_follow_up_returns_fallback_when_not_configured():
    client = FakeGeminiClient(configured=False)
    service = LLMService(client=client)

    question = await service.generate_follow_up_question("Plan", "kisa yanit", fallback="fallback soru")

    assert question == "fallback soru"
    assert client.generate_text_calls == []


@pytest.mark.asyncio
async def test_follow_up_returns_generated_text_when_configured():
    client = FakeGeminiClient(configured=True, text_response="daha detay verir misiniz?")
    service = LLMService(client=client)

    question = await service.generate_follow_up_question("Plan", "kisa yanit", fallback="fallback")

    assert question == "daha detay verir misiniz?"
    assert len(client.generate_text_calls) == 1


@pytest.mark.asyncio
async def test_follow_up_falls_back_on_error():
    client = FakeGeminiClient(configured=True, raise_error=True)
    service = LLMService(client=client)

    question = await service.generate_follow_up_question("Plan", "yanit", fallback="fallback soru")

    assert question == "fallback soru"


@pytest.mark.asyncio
async def test_follow_up_falls_back_on_timeout():
    client = FakeGeminiClient(configured=True, delay_seconds=0.5)
    service = LLMService(client=client, timeout_seconds=0.05)

    question = await service.generate_follow_up_question("Plan", "yanit", fallback="fallback soru")

    assert question == "fallback soru"


@pytest.mark.asyncio
async def test_summarize_falls_back_to_truncated_description_when_not_configured():
    client = FakeGeminiClient(configured=False)
    service = LLMService(client=client)

    long_description = "x" * 300
    summary = await service.summarize_problem(long_description)

    assert summary == long_description[:200]


@pytest.mark.asyncio
async def test_summarize_returns_generated_summary_when_configured():
    client = FakeGeminiClient(configured=True, text_response="kisa ozet")
    service = LLMService(client=client)

    summary = await service.summarize_problem("uzun bir problem aciklamasi")

    assert summary == "kisa ozet"
