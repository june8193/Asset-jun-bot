# -*- coding: utf-8 -*-
"""TelegramBot 테스트 모듈입니다."""

import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock, MagicMock
from asset_jun_bot.config import Config
from asset_jun_bot.telegram_bot import TelegramBot


@pytest.fixture
def mock_config():
  """테스트용 Config 인스턴스를 반환합니다."""
  return Config(
      telegram_bot_token="mock_bot_token",
      telegram_allowed_user_ids={12345},
      asset_manager_api_url="http://mock-asset-server",
      gemini_api_key="mock_gemini_key",
      storage_dir="mock_storage_dir",
  )


@pytest.fixture
def mock_agent_runner():
  """모킹된 AgentRunner 인스턴스를 반환합니다."""
  runner = MagicMock()
  runner.ask = AsyncMock(return_value="에이전트 답변입니다.")
  return runner


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_authorized_user(mock_config, mock_agent_runner):
  """허용된 사용자의 메시지를 받아 AI 답변을 전송하는지 테스트합니다."""
  bot = TelegramBot(config=mock_config, agent_runner=mock_agent_runner)

  # getUpdates 모킹
  updates_response = {
      "ok": True,
      "result": [
          {
              "update_id": 100,
              "message": {
                  "message_id": 1,
                  "from": {"id": 12345, "is_bot": False, "first_name": "TestUser"},
                  "chat": {"id": 12345, "type": "private"},
                  "text": "내 자산 얼마야?",
              },
          }
      ],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(
      return_value=Response(200, json=updates_response)
  )

  # sendMessage 모킹
  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True}))

  next_offset = await bot.poll_once(offset=None)

  # 검증
  assert next_offset == 101
  mock_agent_runner.ask.assert_called_once_with("내 자산 얼마야?")
  assert send_message_route.called
  # 전송된 데이터 바디 확인
  request_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "12345" in request_body
  assert "에이전트 답변입니다." in request_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_unauthorized_user(mock_config, mock_agent_runner):
  """비인가 사용자의 메시지를 받았을 때 AI를 호출하지 않고 차단 메시지를 보내는지 테스트합니다."""
  bot = TelegramBot(config=mock_config, agent_runner=mock_agent_runner)

  # 비인가 사용자(99999)가 보낸 getUpdates 모킹
  updates_response = {
      "ok": True,
      "result": [
          {
              "update_id": 200,
              "message": {
                  "message_id": 1,
                  "chat": {"id": 99999, "type": "private"},
                  "text": "비밀번호가 뭐야?",
              },
          }
      ],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(
      return_value=Response(200, json=updates_response)
  )

  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True}))

  next_offset = await bot.poll_once(offset=None)

  # 검증: 에이전트는 절대 호출되지 않아야 함
  assert next_offset == 201
  mock_agent_runner.ask.assert_not_called()
  assert send_message_route.called
  
  # 비인가 사용자에게 거부 메시지가 전송되었는지 확인
  request_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "99999" in request_body
  assert "허가되지 않은" in request_body or "접근" in request_body
