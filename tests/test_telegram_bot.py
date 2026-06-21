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
      model_chat="gemini-3.5-flash",
      naver_client_id="mock_naver_id",
      naver_client_secret="mock_naver_secret",
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

  # sendMessage 모킹 (임시 메시지 성공 및 message_id: 777 리턴)
  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True, "result": {"message_id": 777}}))

  # editMessageText 모킹
  edit_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/editMessageText"
  ).mock(return_value=Response(200, json={"ok": True}))

  # sendChatAction 모킹
  respx.post(
      "https://api.telegram.org/botmock_bot_token/sendChatAction"
  ).mock(return_value=Response(200, json={"ok": True}))

  next_offset = await bot.poll_once(offset=None)

  # 검증
  assert next_offset == 101
  assert mock_agent_runner.ask.call_count == 1
  assert mock_agent_runner.ask.call_args[0][0] == "내 자산 얼마야?"
  
  # 대화 내역 저장 검증 (사용자 메시지 1회, 봇 응답 메시지 1회)
  assert mock_chat_history_manager.save_message.call_count == 2
  mock_chat_history_manager.save_message.assert_any_call(
      user_id=12345, role="user", message="내 자산 얼마야?"
  )
  mock_chat_history_manager.save_message.assert_any_call(
      user_id=12345, role="bot", message="에이전트 답변입니다."
  )

  # 임시 메시지가 발송되었는지 확인
  assert send_message_route.called
  req_send_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "🔄 AI 답변을 준비 중입니다..." in req_send_body

  # editMessageText를 통해 최종 답변이 갔는지 확인
  assert edit_message_route.called
  req_edit_body = edit_message_route.calls.last.request.read().decode("utf-8")
  assert "12345" in req_edit_body
  assert "에이전트 답변입니다." in req_edit_body


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

  # sendMessage 모킹 (성공 및 message_id: 888 반환)
  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True, "result": {"message_id": 888}}))

  # editMessageText 호출에 대해 순차적으로 응답 모킹 (1차: 400 Bad Request, 2차: 200 OK)
  edit_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/editMessageText"
  ).mock(side_effect=[
      Response(400, json={"ok": False, "description": "Bad Request: can't parse entities"}),
      Response(200, json={"ok": True})
  ])

  # sendChatAction 모킹
  respx.post(
      "https://api.telegram.org/botmock_bot_token/sendChatAction"
  ).mock(return_value=Response(200, json={"ok": True}))

  next_offset = await bot.poll_once(offset=None)

  assert next_offset == 301
  # editMessageText가 총 2번 호출되어야 함 (1차 실패 후 2차 fallback 수정)
  assert edit_message_route.call_count == 2

  # 1차 호출 데이터 검증
  req1_body = edit_message_route.calls[0].request.read().decode("utf-8")
  assert "HTML" in req1_body

  # 2차 호출 데이터 검증
  req2_body = edit_message_route.calls[1].request.read().decode("utf-8")
  assert "메시지 수정 중 오류가 발생했습니다" in req2_body
  assert "Bad Request: can't parse entities" in req2_body
  assert "오류날 답변: [!NOTE] 에러" in req2_body  # 마크다운 태그(**)가 지워진 채 전달되는지 검증


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_progress_flow(mock_config, mock_agent_runner):
  """진행 상태에 따른 실시간 메시지 수정 및 typing 액션 전송 흐름을 통합 테스트합니다."""
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
              "update_id": 400,
              "message": {
                  "message_id": 1,
                  "chat": {"id": 12345, "type": "private"},
                  "text": "내 자산 얼마야?",
              },
          }
      ],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(
      return_value=Response(200, json=updates_response)
  )

  # sendMessage 모킹 (성공 시 message_id를 포함한 결과 반환)
  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True, "result": {"message_id": 777}}))

  # editMessageText 모킹
  edit_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/editMessageText"
  ).mock(return_value=Response(200, json={"ok": True}))

  # sendChatAction 모킹
  chat_action_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendChatAction"
  ).mock(return_value=Response(200, json={"ok": True}))

  # AgentRunner.ask 모킹
  mock_agent_runner.ask.return_value = "최종 자산 분석 결과입니다."

  next_offset = await bot.poll_once(offset=None)

  assert next_offset == 401

  # 1. 초기 임시 메시지 전송 확인
  assert send_message_route.called
  req_send_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "🔄 AI 답변을 준비 중입니다..." in req_send_body

  # 2. sendChatAction이 호출되었는지 확인
  assert chat_action_route.call_count >= 1
  req_action_body = chat_action_route.calls[0].request.read().decode("utf-8")
  assert '"action":"typing"' in req_action_body

  # 3. editMessageText가 한 번 호출되었는지 확인 (최종 답변 수정)
  assert edit_message_route.call_count == 1
  
  # 3.1 최종 수정 내용 확인
  req_edit_body = edit_message_route.calls[0].request.read().decode("utf-8")
  assert '"message_id":777' in req_edit_body
  assert "최종 자산 분석 결과입니다." in req_edit_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_realtime_status_updates(mock_config, mock_agent_runner):
  """에이전트가 동작하며 콜백을 호출할 때 텔레그램 진행 상태 메시지가 순차적으로 수정되는지 테스트합니다."""
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
              "update_id": 500,
              "message": {
                  "message_id": 1,
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
  ).mock(return_value=Response(200, json={"ok": True, "result": {"message_id": 777}}))

  # editMessageText 모킹
  edit_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/editMessageText"
  ).mock(return_value=Response(200, json={"ok": True}))

  # sendChatAction 모킹
  respx.post(
      "https://api.telegram.org/botmock_bot_token/sendChatAction"
  ).mock(return_value=Response(200, json={"ok": True}))

  # AgentRunner.ask 모킹: 실행 중 콜백을 시뮬레이션
  async def mock_ask(prompt, on_status_update=None):
    if on_status_update:
      await on_status_update("🔧 도구 실행 중: test_tool")
      await on_status_update("✍️ AI 답변을 작성 중입니다...")
    return "최종 자산 분석 결과입니다."
  mock_agent_runner.ask.side_effect = mock_ask

  next_offset = await bot.poll_once(offset=None)

  assert next_offset == 501

  # editMessageText가 총 3회 호출되어야 함 (도구 실행 중, 답변 작성 중, 최종 답변)
  assert edit_message_route.call_count == 3

  # 각 호출 내용 검증
  body_1 = edit_message_route.calls[0].request.read().decode("utf-8")
  body_2 = edit_message_route.calls[1].request.read().decode("utf-8")
  body_3 = edit_message_route.calls[2].request.read().decode("utf-8")

  assert "🔧 도구 실행 중: test_tool" in body_1
  assert "✍️ AI 답변을 작성 중입니다..." in body_2
  assert "최종 자산 분석 결과입니다." in body_3



