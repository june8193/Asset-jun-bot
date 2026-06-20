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
  monkeypatch.setenv("MODEL_ROUTER", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_GENERAL_CONVERSATION", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_ASSET_INQUIRY", "gemini-1.5-flash")
  monkeypatch.setenv("NAVER_API_CLIENT_ID", "mock_naver_id")
  monkeypatch.setenv("NAVER_API_CLIENT_SECRET", "mock_naver_secret")


@pytest.mark.asyncio
async def test_agent_runner_ask_asset_inquiry(mocker):
  """ASSET_INQUIRY 의도로 분류되어 해당 모델과 도구들이 정상 호출되는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_router = "gemini-2.5-flash"
  mock_config.model_general_conversation = "gemini-2.5-flash"
  mock_config.model_asset_inquiry = "gemini-1.5-flash"

  # 1차 라우터 에이전트 모킹
  mock_router_agent = MagicMock()
  mock_router_agent.__aenter__ = AsyncMock(return_value=mock_router_agent)
  mock_router_agent.__aexit__ = AsyncMock(return_value=None)
  mock_router_response = MagicMock()
  mock_router_response.structured_output = AsyncMock(return_value={"task_type": "ASSET_INQUIRY"})
  mock_router_agent.chat = AsyncMock(return_value=mock_router_response)

  # 2차 자산조회 실제 에이전트 모킹
  mock_actual_agent = MagicMock()
  mock_actual_agent.__aenter__ = AsyncMock(return_value=mock_actual_agent)
  mock_actual_agent.__aexit__ = AsyncMock(return_value=None)
  mock_actual_response = MagicMock()
  mock_actual_response.text = AsyncMock(return_value="자산 조회 완료 결과입니다.")
  mock_actual_agent.chat = AsyncMock(return_value=mock_actual_response)

  # 생성 순서대로 모킹 인스턴스 반환
  mock_agent_class = mocker.patch("asset_jun_bot.agent_runner.Agent", side_effect=[mock_router_agent, mock_actual_agent])
  mock_local_config = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response_text = await runner.ask("자산 내역 알려줘")

  assert response_text == "자산 조회 완료 결과입니다."
  assert mock_agent_class.call_count == 2
  
  # 라우터용 설정 확인
  mock_local_config.assert_any_call(
      model="gemini-2.5-flash",
      system_instructions=runner.router_instructions,
      response_schema=mocker.ANY,
      tools=[],
      policies=mocker.ANY
  )
  # 실제 호출용 설정 확인
  mock_local_config.assert_any_call(
      model="gemini-1.5-flash",
      system_instructions=runner.system_instructions_asset,
      tools=mocker.ANY,
      policies=mocker.ANY
  )


@pytest.mark.asyncio
async def test_agent_runner_ask_general_conversation(mocker):
  """GENERAL_CONVERSATION 의도로 분류되어 해당 모델이 정상 호출되는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_router = "gemini-2.5-flash"
  mock_config.model_general_conversation = "gemini-2.5-flash"
  mock_config.model_asset_inquiry = "gemini-1.5-flash"

  mock_router_agent = MagicMock()
  mock_router_agent.__aenter__ = AsyncMock(return_value=mock_router_agent)
  mock_router_agent.__aexit__ = AsyncMock(return_value=None)
  mock_router_response = MagicMock()
  mock_router_response.structured_output = AsyncMock(return_value={"task_type": "GENERAL_CONVERSATION"})
  mock_router_agent.chat = AsyncMock(return_value=mock_router_response)

  mock_actual_agent = MagicMock()
  mock_actual_agent.__aenter__ = AsyncMock(return_value=mock_actual_agent)
  mock_actual_agent.__aexit__ = AsyncMock(return_value=None)
  mock_actual_response = MagicMock()
  mock_actual_response.text = AsyncMock(return_value="안녕하세요! 반갑습니다.")
  mock_actual_agent.chat = AsyncMock(return_value=mock_actual_response)

  mock_agent_class = mocker.patch("asset_jun_bot.agent_runner.Agent", side_effect=[mock_router_agent, mock_actual_agent])
  mock_local_config = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response_text = await runner.ask("안녕?")

  assert response_text == "안녕하세요! 반갑습니다."
  assert mock_agent_class.call_count == 2
  
  mock_local_config.assert_any_call(
      model="gemini-2.5-flash",
      system_instructions=runner.system_instructions_chat,
      tools=[],
      policies=mocker.ANY
  )


@pytest.mark.asyncio
async def test_agent_runner_routing_fallback_on_error(mocker):
  """의도 분류 과정에서 에러가 발생해도 GENERAL_CONVERSATION으로 폴백 작동하는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_router = "gemini-2.5-flash"
  mock_config.model_general_conversation = "gemini-2.5-flash"
  mock_config.model_asset_inquiry = "gemini-1.5-flash"

  # 1차 라우터에서 예외가 나는 에이전트 반환
  mock_router_agent = MagicMock()
  mock_router_agent.__aenter__ = AsyncMock(return_value=mock_router_agent)
  mock_router_agent.__aexit__ = AsyncMock(return_value=None)
  mock_router_agent.chat = AsyncMock(side_effect=RuntimeError("Routing engine failure"))

  # 2차 일반대화 에이전트 정상 반환
  mock_actual_agent = MagicMock()
  mock_actual_agent.__aenter__ = AsyncMock(return_value=mock_actual_agent)
  mock_actual_agent.__aexit__ = AsyncMock(return_value=None)
  mock_actual_response = MagicMock()
  mock_actual_response.text = AsyncMock(return_value="폴백 정상 대화")
  mock_actual_agent.chat = AsyncMock(return_value=mock_actual_response)

  mock_agent_class = mocker.patch("asset_jun_bot.agent_runner.Agent", side_effect=[mock_router_agent, mock_actual_agent])
  mock_local_config = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response_text = await runner.ask("분류 실패 유도")

  assert response_text == "폴백 정상 대화"
  assert mock_agent_class.call_count == 2
  mock_local_config.assert_any_call(
      model="gemini-2.5-flash",
      system_instructions=runner.system_instructions_chat,
      tools=[],
      policies=mocker.ANY
  )


@pytest.mark.asyncio
async def test_agent_runner_exception(mocker):
  """2차 에이전트 실행 도중 에러가 발생했을 때 적절한 에러 메시지를 반환하는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_router = "gemini-2.5-flash"
  mock_config.model_general_conversation = "gemini-2.5-flash"
  mock_config.model_asset_inquiry = "gemini-1.5-flash"

  # 1차 정상 분류
  mock_router_agent = MagicMock()
  mock_router_agent.__aenter__ = AsyncMock(return_value=mock_router_agent)
  mock_router_agent.__aexit__ = AsyncMock(return_value=None)
  mock_router_response = MagicMock()
  mock_router_response.structured_output = AsyncMock(return_value={"task_type": "GENERAL_CONVERSATION"})
  mock_router_agent.chat = AsyncMock(return_value=mock_router_response)

  # 2차 에러 발생
  mock_actual_agent = MagicMock()
  mock_actual_agent.__aenter__ = AsyncMock(return_value=mock_actual_agent)
  mock_actual_agent.__aexit__ = AsyncMock(return_value=None)
  mock_actual_agent.chat = AsyncMock(side_effect=RuntimeError("Gemini API Error"))

  mocker.patch("asset_jun_bot.agent_runner.Agent", side_effect=[mock_router_agent, mock_actual_agent])
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
  mock_config.model_router = "gemini-2.5-flash"
  mock_config.model_general_conversation = "gemini-2.5-flash"
  mock_config.model_asset_inquiry = "gemini-1.5-flash"

  # 1차 정상 분류
  mock_router_agent = MagicMock()
  mock_router_agent.__aenter__ = AsyncMock(return_value=mock_router_agent)
  mock_router_agent.__aexit__ = AsyncMock(return_value=None)
  mock_router_response = MagicMock()
  mock_router_response.structured_output = AsyncMock(return_value={"task_type": "ASSET_INQUIRY"})
  mock_router_agent.chat = AsyncMock(return_value=mock_router_response)

  # 2차 자산 API 클라이언트 에러
  mock_actual_agent = MagicMock()
  mock_actual_agent.__aenter__ = AsyncMock(return_value=mock_actual_agent)
  mock_actual_agent.__aexit__ = AsyncMock(return_value=None)
  mock_actual_agent.chat = AsyncMock(side_effect=AssetClientError("API connection failed"))

  mocker.patch("asset_jun_bot.agent_runner.Agent", side_effect=[mock_router_agent, mock_actual_agent])
  mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  response_text = await runner.ask("내 자산 어때?")

  assert response_text == "⚠️ API 서버에 연결할 수 없습니다."


@pytest.mark.asyncio
async def test_agent_runner_ask_with_status_callback(mocker):
  """ask 호출 시 status 콜백이 올바른 매개변수로 호출되는지 테스트합니다."""
  mock_config = MagicMock()
  mock_config.model_router = "gemini-2.5-flash"
  mock_config.model_general_conversation = "gemini-2.5-flash"
  mock_config.model_asset_inquiry = "gemini-1.5-flash"

  # 1차 라우터에서 ASSET_INQUIRY 반환
  mock_router_agent = MagicMock()
  mock_router_agent.__aenter__ = AsyncMock(return_value=mock_router_agent)
  mock_router_agent.__aexit__ = AsyncMock(return_value=None)
  mock_router_response = MagicMock()
  mock_router_response.structured_output = AsyncMock(return_value={"task_type": "ASSET_INQUIRY"})
  mock_router_agent.chat = AsyncMock(return_value=mock_router_response)

  # 2차 실제 에이전트 반환
  mock_actual_agent = MagicMock()
  mock_actual_agent.__aenter__ = AsyncMock(return_value=mock_actual_agent)
  mock_actual_agent.__aexit__ = AsyncMock(return_value=None)
  mock_actual_response = MagicMock()
  mock_actual_response.text = AsyncMock(return_value="자산 조회 완료")
  mock_actual_agent.chat = AsyncMock(return_value=mock_actual_response)

  mocker.patch("asset_jun_bot.agent_runner.Agent", side_effect=[mock_router_agent, mock_actual_agent])
  mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)

  callback_calls = []
  async def mock_callback(status):
    callback_calls.append(status)

  response_text = await runner.ask("내 자산 어때?", on_status_update=mock_callback)

  assert response_text == "자산 조회 완료"
  assert callback_calls == ["ASSET_INQUIRY"]


@pytest.mark.asyncio
async def test_agent_runner_router_policies_include_finish(mocker):
  """의도 분류 라우터가 finish 도구 호출을 정책상 허용하고 있는지 확인합니다."""
  mock_config = MagicMock()
  mock_config.model_router = "gemini-2.5-flash"
  mock_config.model_general_conversation = "gemini-2.5-flash"
  mock_config.model_asset_inquiry = "gemini-1.5-flash"

  # 라우터 에이전트 모킹
  mock_router_agent = MagicMock()
  mock_router_agent.__aenter__ = AsyncMock(return_value=mock_router_agent)
  mock_router_agent.__aexit__ = AsyncMock(return_value=None)
  mock_router_response = MagicMock()
  mock_router_response.structured_output = AsyncMock(return_value={"task_type": "ASSET_INQUIRY"})
  mock_router_agent.chat = AsyncMock(return_value=mock_router_response)

  # 실제 에이전트 모킹
  mock_actual_agent = MagicMock()
  mock_actual_agent.__aenter__ = AsyncMock(return_value=mock_actual_agent)
  mock_actual_agent.__aexit__ = AsyncMock(return_value=None)
  mock_actual_response = MagicMock()
  mock_actual_response.text = AsyncMock(return_value="자산 조회 완료")
  mock_actual_agent.chat = AsyncMock(return_value=mock_actual_response)

  mocker.patch("asset_jun_bot.agent_runner.Agent", side_effect=[mock_router_agent, mock_actual_agent])
  mock_local_config = mocker.patch("asset_jun_bot.agent_runner.LocalAgentConfig")

  runner = AgentRunner(config=mock_config)
  await runner.ask("내 관심종목 알려줘")

  # 첫 번째 LocalAgentConfig 호출의 인자 가져오기
  router_call_kwargs = mock_local_config.call_args_list[0].kwargs
  policies = router_call_kwargs.get("policies", [])

  # 정책의 길이가 2여야 합니다 (policy.deny_all() 및 policy.allow("finish"))
  assert len(policies) == 2


