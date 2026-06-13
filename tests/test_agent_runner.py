# -*- coding: utf-8 -*-
"""AgentRunner 테스트 모듈입니다."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from asset_jun_bot.agent_runner import AgentRunner


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
  """테스트 환경 변수를 주입합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")


@pytest.mark.asyncio
async def test_agent_runner_ask_success(mocker):
  """AgentRunner.ask()가 정상적으로 에이전트와 대화하고 응답을 반환하는지 테스트합니다."""
  # google.antigravity.Agent 모킹
  mock_agent_instance = MagicMock()
  mock_chat_response = MagicMock()
  
  # async context manager __aenter__ 모킹
  mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
  mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
  
  # agent.chat() 비동기 메서드 모킹
  mock_agent_instance.chat = AsyncMock(return_value=mock_chat_response)
  
  # response.text() 비동기 메서드 모킹
  mock_chat_response.text = AsyncMock(return_value="안녕하세요! 모킹된 답변입니다.")

  # Agent 생성자 모킹
  mock_agent_class = mocker.patch("asset_jun_bot.agent_runner.Agent", return_value=mock_agent_instance)
  mock_config_class = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner()
  response_text = await runner.ask("안녕?")

  # 검증: config와 agent가 올바르게 생성되고 chat이 호출되었는지 확인
  mock_config_class.assert_called_once()
  mock_agent_class.assert_called_once()
  mock_agent_instance.chat.assert_called_once_with("안녕?")
  assert response_text == "안녕하세요! 모킹된 답변입니다."


@pytest.mark.asyncio
async def test_agent_runner_exception(mocker):
  """Agent 실행 도중 에러가 발생했을 때 적절한 에러 메시지를 반환하는지 테스트합니다."""
  mock_agent_instance = MagicMock()
  mock_agent_instance.__aenter__ = AsyncMock(return_value=mock_agent_instance)
  mock_agent_instance.__aexit__ = AsyncMock(return_value=None)
  mock_agent_instance.chat = AsyncMock(side_effect=RuntimeError("Gemini API Error"))

  mocker.patch("asset_jun_bot.agent_runner.Agent", return_value=mock_agent_instance)
  mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner()
  response_text = await runner.ask("오류 테스트")

  assert "에러" in response_text
  assert "Gemini API Error" in response_text
