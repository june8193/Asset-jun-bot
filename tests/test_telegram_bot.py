# -*- coding: utf-8 -*-
"""TelegramBot 테스트 모듈입니다."""

import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock, MagicMock
from asset_jun_bot.config import Config
from asset_jun_bot.telegram_bot import TelegramBot
from asset_jun_bot.chat_history_manager import ChatHistoryManager


@pytest.fixture
def mock_config():
  """테스트용 Config 인스턴스를 반환합니다."""
  return Config(
      telegram_bot_token="mock_bot_token",
      telegram_allowed_user_ids={12345},
      asset_manager_api_url="http://mock-asset-server",
      gemini_api_key="mock_gemini_key",
      storage_dir="mock_storage_dir",
      model_router="gemini-2.5-flash",
      model_general_conversation="gemini-2.5-flash",
      model_asset_inquiry="gemini-1.5-flash",
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
  mock_chat_history_manager = AsyncMock(spec=ChatHistoryManager)
  bot = TelegramBot(
      config=mock_config,
      agent_runner=mock_agent_runner,
      chat_history_manager=mock_chat_history_manager,
  )

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
  
  # 대화 내역 저장 검증 (사용자 메시지 1회, 봇 응답 메시지 1회)
  assert mock_chat_history_manager.save_message.call_count == 2
  mock_chat_history_manager.save_message.assert_any_call(
      user_id=12345, role="user", message="내 자산 얼마야?"
  )
  mock_chat_history_manager.save_message.assert_any_call(
      user_id=12345, role="bot", message="에이전트 답변입니다."
  )

  assert send_message_route.called
  # 전송된 데이터 바디 확인
  request_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "12345" in request_body
  assert "에이전트 답변입니다." in request_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_unauthorized_user(mock_config, mock_agent_runner):
  """비인가 사용자의 메시지를 받았을 때 AI를 호출하지 않고 차단 메시지를 보내는지 테스트합니다."""
  mock_chat_history_manager = AsyncMock(spec=ChatHistoryManager)
  bot = TelegramBot(
      config=mock_config,
      agent_runner=mock_agent_runner,
      chat_history_manager=mock_chat_history_manager,
  )

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
  
  # 대화 내역 저장은 비인가자 차단 시 호출되지 않아야 함
  mock_chat_history_manager.save_message.assert_not_called()
  
  assert send_message_route.called
  
  # 비인가 사용자에게 거부 메시지가 전송되었는지 확인
  request_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "99999" in request_body
  assert "허가되지 않은" in request_body or "접근" in request_body


def test_markdown_to_html():
  """마크다운 형식을 텔레그램 친화적인 HTML 형식으로 올바르게 변환하는지 테스트합니다."""
  from asset_jun_bot.telegram_bot import markdown_to_html

  # 1. 일반 강조 및 태그 이스케이프 테스트
  text = "안녕하세요 & 반가워요 <준> 님. **강조** 및 *강조2* 테스트."
  expected = "안녕하세요 &amp; 반가워요 &lt;준&gt; 님. <b>강조</b> 및 <b>강조2</b> 테스트."
  assert markdown_to_html(text) == expected

  # 2. 코드 및 코드블록 테스트
  text_code = "이것은 `코드` 이며,\n```\n코드 블록\n```\n입니다."
  expected_code = "이것은 <code>코드</code> 이며,\n<pre>\n코드 블록\n</pre>\n입니다."
  assert markdown_to_html(text_code) == expected_code

  # 3. 링크 테스트
  text_link = "[구글](https://google.com) 링크 테스트"
  expected_link = '<a href="https://google.com">구글</a> 링크 테스트'
  assert markdown_to_html(text_link) == expected_link

  # 4. 수평선 및 헤더, 인용구 테스트
  text_complex = "### 제목\n---\n> 인용구 내용"
  expected_complex = "<b>제목</b>\n━━━━━━━━━━━━━━━━━━━━\n<blockquote>인용구 내용</blockquote>"
  assert markdown_to_html(text_complex) == expected_complex


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_send_message_failure_fallback(mock_config, mock_agent_runner):
  """마크다운(HTML) 송신 시 400 에러가 나면, 서식을 제거한 일반 텍스트로 에러와 함께 재전송하는지 테스트합니다."""
  mock_chat_history_manager = AsyncMock(spec=ChatHistoryManager)
  bot = TelegramBot(
      config=mock_config,
      agent_runner=mock_agent_runner,
      chat_history_manager=mock_chat_history_manager,
  )

  # getUpdates 모킹
  updates_response = {
      "ok": True,
      "result": [
          {
              "update_id": 300,
              "message": {
                  "message_id": 1,
                  "chat": {"id": 12345, "type": "private"},
                  "text": "에러 유도 요청",
              },
          }
      ],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(
      return_value=Response(200, json=updates_response)
  )

  # AI 에이전트 답변이 마크다운 에러를 유발할 법한 텍스트라고 가정
  mock_agent_runner.ask.return_value = "오류날 답변: [!NOTE] **에러**"

  # sendMessage 호출에 대해 순차적으로 응답 모킹 (1차: 400 Bad Request, 2차: 200 OK)
  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(side_effect=[
      Response(400, json={"ok": False, "description": "Bad Request: can't parse entities"}),
      Response(200, json={"ok": True})
  ])

  next_offset = await bot.poll_once(offset=None)

  assert next_offset == 301
  # 총 2번 호출되어야 함 (1차 실패 후 2차 fallback)
  assert send_message_route.call_count == 2

  # 1차 호출 데이터 검증
  req1_body = send_message_route.calls[0].request.read().decode("utf-8")
  assert "HTML" in req1_body

  # 2차 호출 데이터 검증
  req2_body = send_message_route.calls[1].request.read().decode("utf-8")
  assert "메시지 전송 중 오류가 발생했습니다" in req2_body
  assert "Bad Request: can't parse entities" in req2_body
  assert "오류날 답변: [!NOTE] 에러" in req2_body  # 마크다운 태그(**)가 지워진 채 전달되는지 검증

