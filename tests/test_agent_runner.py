# -*- coding: utf-8 -*-
"""AgentRunner 테스트 모듈입니다."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from asset_jun_bot.agent_runner import AgentRunner


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
  """테스트 환경 변수를 주입합니다. config.py의 필수값 제약에 의해 추가되었습니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.setenv("STORAGE_DIR", "mock_storage_dir")
  monkeypatch.setenv("MODEL_CHAT", "gemini-3.5-flash")
  monkeypatch.setenv("NAVER_API_CLIENT_ID", "mock_naver_id")
  monkeypatch.setenv("NAVER_API_CLIENT_SECRET", "mock_naver_secret")


@pytest.mark.asyncio
async def test_agent_runner_ask_success(mocker):
  """에이전트가 단일 모델과 로컬 스킬 설정을 바탕으로 정상적으로 답변하는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_chat = "gemini-3.5-flash"

  # 에이전트 모킹
  mock_agent = MagicMock()
  mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
  mock_agent.__aexit__ = AsyncMock(return_value=None)
  mock_response = MagicMock()
  mock_response.text = AsyncMock(return_value="성공적인 답변 결과입니다.")
  mock_agent.chat = AsyncMock(return_value=mock_response)

  mock_agent_class = mocker.patch("asset_jun_bot.agent_runner.Agent", return_value=mock_agent)
  mock_local_config = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response_text = await runner.ask("자산 내역 알려줘")

  assert response_text == "성공적인 답변 결과입니다."
  assert mock_agent_class.call_count == 1
  
  # 호출용 설정 확인
  mock_local_config.assert_called_once()
  kwargs = mock_local_config.call_args.kwargs
  
  assert kwargs.get("model") == "gemini-3.5-flash"
  assert kwargs.get("system_instructions") is None
  assert len(kwargs.get("tools", [])) == 0
  assert len(kwargs.get("policies", [])) == 2  # deny_all + run_command allow = 2
  assert any("skills" in path for path in kwargs.get("skills_paths", []))


@pytest.mark.asyncio
async def test_agent_runner_exception(mocker):
  """에이전트 실행 도중 에러가 발생했을 때 적절한 에러 메시지를 반환하는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_chat = "gemini-3.5-flash"

  mock_agent = MagicMock()
  mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
  mock_agent.__aexit__ = AsyncMock(return_value=None)
  mock_agent.chat = AsyncMock(side_effect=RuntimeError("Gemini API Error"))

  mocker.patch("asset_jun_bot.agent_runner.Agent", return_value=mock_agent)
  mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response_text = await runner.ask("오류 테스트")

  assert "에러" in response_text
  assert "Gemini API Error" in response_text


@pytest.mark.asyncio
async def test_agent_runner_asset_client_error(mocker):
  """자산 API 클라이언트 에러 발생 시 지정된 시스템 안내 메시지를 반환하는지 테스트합니다."""
  from asset_jun_bot.asset_client import AssetClientError

  mock_config = MagicMock()
  mock_config.model_chat = "gemini-3.5-flash"

  mock_agent = MagicMock()
  mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
  mock_agent.__aexit__ = AsyncMock(return_value=None)
  mock_agent.chat = AsyncMock(side_effect=AssetClientError("API connection failed"))

  mocker.patch("asset_jun_bot.agent_runner.Agent", return_value=mock_agent)
  mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response_text = await runner.ask("내 자산 어때?")

  assert response_text == "⚠️ API 서버에 연결할 수 없습니다."


@pytest.mark.asyncio
async def test_agent_runner_with_status_updates(mocker):
  """AgentRunner가 훅 실행 시 on_status_update 콜백을 적절한 진행 상황 메시지와 함께 호출하는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_chat = "gemini-3.5-flash"

  mock_agent = MagicMock()
  mock_agent.__aenter__ = AsyncMock(return_value=mock_agent)
  mock_agent.__aexit__ = AsyncMock(return_value=None)
  mock_response = MagicMock()
  mock_response.text = AsyncMock(return_value="성공적인 답변 결과입니다.")
  mock_agent.chat = AsyncMock(return_value=mock_response)

  mocker.patch("asset_jun_bot.agent_runner.Agent", return_value=mock_agent)
  mock_local_config = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  # 비동기 콜백 모킹
  callback_calls = []
  async def mock_callback(status: str):
    callback_calls.append(status)

  runner = AgentRunner(config=mock_config)
  await runner.ask("자산 내역 알려줘", on_status_update=mock_callback)

  # LocalAgentConfig에 전달된 hooks 확인
  mock_local_config.assert_called_once()
  kwargs = mock_local_config.call_args.kwargs
  hooks = kwargs.get("hooks", [])
  assert len(hooks) >= 2

  # 훅 모킹 실행
  from google.antigravity.types import ToolCall, ToolResult
  from google.antigravity.hooks import HookContext

  # pre_tool_call_decide 훅 실행 테스트
  pre_hook = next((h for h in hooks if h.__class__.__name__ == "_FunctionHook" and h.f.__name__ == "pre_tool_call_hook"), None)
  assert pre_hook is not None

  tool_call = ToolCall(name="korea_daily_index_report", args={"date": "2026-06-21"}, canonical_path="korea-daily-index-report/korea_daily_index_report")
  await pre_hook.run(HookContext(), tool_call)
  assert any("korea_daily_index_report" in call for call in callback_calls)
  assert any("korea-daily-index-report" in call for call in callback_calls)

  # post_tool_call 훅 실행 테스트
  post_hook = next((h for h in hooks if h.__class__.__name__ == "_FunctionHook" and h.f.__name__ == "post_tool_call_hook"), None)
  assert post_hook is not None

  tool_result = ToolResult(name="korea_daily_index_report")
  await post_hook.run(HookContext(), tool_result)
  assert any("작성 중" in call for call in callback_calls)


