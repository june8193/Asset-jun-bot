# -*- coding: utf-8 -*-
"""TelegramBot 테스트 모듈입니다."""

import os
import pytest
import respx
from httpx import Response
from unittest.mock import MagicMock
from asset_jun_bot.config import Config
from asset_jun_bot.telegram_bot import TelegramBot


@pytest.fixture
def mock_config():
  """테스트용 Config 인스턴스를 반환합니다."""
  return Config(
      telegram_bot_token="mock_bot_token",
      telegram_allowed_user_ids={12345},
      asset_manager_api_url="http://mock-asset-server",
      asset_manager_dir="mock_asset_dir",
      storage_dir="mock_storage_dir",
      naver_client_id="mock_naver_id",
      naver_client_secret="mock_naver_secret",
  )


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_plain_text_message(mock_config):
  """일반 텍스트 메시지 수신 시 자연어 대화 종료 및 CLI 안내 메시지를 전송하는지 테스트합니다."""
  bot = TelegramBot(config=mock_config)

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
  ).mock(return_value=Response(200, json={"ok": True, "result": {"message_id": 777}}))

  next_offset = await bot.poll_once(offset=None)

  # 검증
  assert next_offset == 101
  assert send_message_route.called
  req_send_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "12345" in req_send_body
  assert "자연어 대화 기능은 종료되었습니다" in req_send_body
  assert "/help" in req_send_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_unauthorized_user(mock_config):
  """비인가 사용자의 메시지를 받았을 때 차단 메시지를 보내는지 테스트합니다."""
  bot = TelegramBot(config=mock_config)

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

  assert next_offset == 201
  assert send_message_route.called
  
  # 비인가 사용자에게 거부 메시지가 전송되었는지 확인
  request_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "99999" in request_body
  assert "접근 권한이 없습니다" in request_body


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
async def test_telegram_bot_send_message_failure_fallback(mock_config):
  """마크다운(HTML) 송신 시 400 에러가 나면, 서식을 제거한 일반 텍스트로 에러와 함께 재전송하는지 테스트합니다."""
  bot = TelegramBot(config=mock_config)

  # sendMessage 호출에 대해 순차적으로 응답 모킹 (1차: 400 Bad Request, 2차: 200 OK)
  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(side_effect=[
      Response(400, json={"ok": False, "description": "Bad Request: can't parse entities"}),
      Response(200, json={"ok": True})
  ])

  await bot._send_message(12345, "오류날 메시지: [!NOTE] **에러**")

  assert send_message_route.call_count == 2
  req1_body = send_message_route.calls[0].request.read().decode("utf-8")
  assert "HTML" in req1_body

  req2_body = send_message_route.calls[1].request.read().decode("utf-8")
  assert "메시지 전송 중 오류가 발생했습니다" in req2_body
  assert "Bad Request: can't parse entities" in req2_body
  assert "오류날 메시지: [!NOTE] 에러" in req2_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_cli_help(mock_config):
  """/help 명령어를 보냈을 때 도움말 메시지를 즉시 전송하는지 테스트합니다."""
  bot = TelegramBot(config=mock_config)

  # getUpdates 모킹
  updates_response = {
      "ok": True,
      "result": [
          {
              "update_id": 600,
              "message": {
                  "message_id": 1,
                  "chat": {"id": 12345, "type": "private"},
                  "text": "/help",
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

  assert next_offset == 601
  assert send_message_route.called

  req_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "/help" in req_body
  assert "/restart" in req_body
  assert "/asset" in req_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_cli_restart(mock_config, tmp_path):
  """/restart 명령어를 받았을 때 플래그 파일을 기록하고 시스템 종료 메서드를 수행하는지 테스트합니다."""
  # 임시 storage_dir 설정
  mock_config.storage_dir = str(tmp_path)

  bot = TelegramBot(config=mock_config)

  # exit_system 모킹
  bot.exit_system = MagicMock()

  updates_response = {
      "ok": True,
      "result": [
          {
              "update_id": 700,
              "message": {
                  "message_id": 1,
                  "chat": {"id": 12345, "type": "private"},
                  "text": "/restart",
              },
          }
      ],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(
      return_value=Response(200, json=updates_response)
  )

  respx.post("https://api.telegram.org/botmock_bot_token/sendMessage").mock(
      return_value=Response(200, json={"ok": True})
  )
  respx.post("https://api.telegram.org/botmock_bot_token/sendChatAction").mock(
      return_value=Response(200, json={"ok": True})
  )

  import os
  flag_file = os.path.join(mock_config.storage_dir, ".restart_pending")
  assert not os.path.exists(flag_file)

  await bot.poll_once(offset=None)

  # 플래그 파일 생성 완료 검증
  assert os.path.exists(flag_file)
  bot.exit_system.assert_called_once()


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_cli_asset(mock_config, monkeypatch):
  """/asset 명령어를 받았을 때 요약 및 비중 API를 조회해 올바른 레이아웃의 자산 보고서를 전송하는지 테스트합니다."""
  # 환경 변수를 통해 Config.load()가 모킹 URL을 사용하도록 재설정
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")

  bot = TelegramBot(config=mock_config)

  updates_response = {
      "ok": True,
      "result": [
          {
              "update_id": 800,
              "message": {
                  "message_id": 1,
                  "chat": {"id": 12345, "type": "private"},
                  "text": "/asset",
              },
          }
      ],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(
      return_value=Response(200, json=updates_response)
  )

  # get_asset_summary & get_asset_ratios 모의 API 응답
  summary_json = {
      "total_valuation_krw": 443152244.98,
      "total_contribution": 320057785.0,
      "initial_base_asset": 17452155.0,
      "total_profit": 105642304.98,
      "cumulative_roi": 31.3,
      "contribution_ratio": 76.16,
      "profit_ratio": 23.84,
      "exchange_rate": {
          "rate": 1484.1,
          "date": "2026-07-12",
          "created_at": "2026-07-12T10:52:41.366166",
          "currency": "USD"
      },
      "latest_price_date": "2026-06-06"
  }
  respx.get("http://mock-asset-server/api/dashboard/summary").mock(
      return_value=Response(200, json=summary_json)
  )

  ratios_json = {
      "total_valuation": 443152244.98,
      "total_target": 443000000.0,
      "additional_cash": 0.0,
      "major_results": [
          {
              "category": "일반주식",
              "current_amt": 193852402.33,
              "current_ratio": 43.7,
              "target_percentage": 45.0,
              "target_amt": 199418510.0,
              "diff_amt": -5566108.0
          }
      ],
      "sub_results": []
  }
  respx.get("http://mock-asset-server/api/ratios/rebalancing").mock(
      return_value=Response(200, json=ratios_json)
  )

  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True}))

  respx.post("https://api.telegram.org/botmock_bot_token/sendChatAction").mock(
      return_value=Response(200, json={"ok": True})
  )

  await bot.poll_once(offset=None)

  assert send_message_route.called

  req_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "통합 자산 현황" in req_body
  assert "443,152,245" in req_body
  assert "2026-07-12" in req_body
  assert "2026-06-06" in req_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_restart_notification(mock_config, tmp_path):
  """봇 가동 시작 단계에서 재시작 플래그가 발견되면, 안내 메시지를 쏘고 플래그 파일을 삭제하는지 테스트합니다."""
  mock_config.storage_dir = str(tmp_path)
  bot = TelegramBot(config=mock_config)

  # 플래그 파일 임의 사전 생성
  import os
  flag_file = os.path.join(mock_config.storage_dir, ".restart_pending")
  with open(flag_file, "w") as f:
    f.write("restart")

  # sendMessage 모킹
  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True}))

  # 감지 함수 실행
  await bot.check_restart_flag()

  # 검증: 메시지 발송 완료 및 파일 삭제 완료
  assert send_message_route.called
  req_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "재시작이 완료되었습니다" in req_body
  assert not os.path.exists(flag_file)


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_cli_ratio(mock_config, monkeypatch):
  """/ratio 명령어를 보냈을 때 대분류/소분류 비중 리밸런싱 정보를 정상 수신하여 조립하는지 테스트합니다."""
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")
  bot = TelegramBot(config=mock_config)

  updates_response = {
      "ok": True,
      "result": [{
          "update_id": 900,
          "message": {
              "message_id": 1,
              "chat": {"id": 12345, "type": "private"},
              "text": "/ratio",
          },
      }],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(return_value=Response(200, json=updates_response))

  ratios_json = {
      "total_valuation": 443152244.98,
      "total_target": 443000000.0,
      "additional_cash": 0.0,
      "major_results": [{
          "category": "일반주식",
          "current_amt": 193852402.33,
          "current_ratio": 43.7,
          "target_percentage": 45.0,
          "target_amt": 199418510.0,
          "diff_amt": -5566108.0
      }],
      "sub_results": [{
          "category": "국내주식",
          "parent_category": "일반주식",
          "current_amt": 93852402.33,
          "current_ratio": 21.2,
          "target_percentage": 20.0,
          "target_amt": 88600000.0,
          "diff_amt": 5252402.0
      }]
  }
  respx.get("http://mock-asset-server/api/ratios/rebalancing").mock(return_value=Response(200, json=ratios_json))

  send_message_route = respx.post("https://api.telegram.org/botmock_bot_token/sendMessage").mock(return_value=Response(200, json={"ok": True}))
  respx.post("https://api.telegram.org/botmock_bot_token/sendChatAction").mock(return_value=Response(200, json={"ok": True}))

  await bot.poll_once(offset=None)
  assert send_message_route.called
  req_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "대분류 비중" in req_body
  assert "소분류 비중" in req_body
  assert "일반주식" in req_body
  assert "국내주식" in req_body
  assert "차액: -5,566,108" in req_body
  assert "차액: +5,252,402" in req_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_cli_tx(mock_config, monkeypatch):
  """/tx 명령어를 보냈을 때 최근 거래내역을 계좌명과 함께 수신하고 슬라이싱 표시하는지 테스트합니다."""
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")
  bot = TelegramBot(config=mock_config)

  updates_response = {
      "ok": True,
      "result": [{
          "update_id": 910,
          "message": {
              "message_id": 1,
              "chat": {"id": 12345, "type": "private"},
              "text": "/tx 2",
          },
      }],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(return_value=Response(200, json=updates_response))

  txs_json = [
      {
          "id": 1,
          "account_id": 10,
          "asset_id": 20,
          "transaction_date": "2026-07-19",
          "type": "BUY",
          "quantity": 10.0,
          "price": 75000.0,
          "total_amount": 750000.0,
          "currency": "KRW",
          "exchange_rate": 1.0,
          "memo": "삼성전자 매수",
          "asset_name": "삼성전자",
          "asset_ticker": "005930",
          "account_display_name": "KB증권 (일반 주식)"
      }
  ]
  respx.get("http://mock-asset-server/api/db/transactions").mock(return_value=Response(200, json=txs_json))

  send_message_route = respx.post("https://api.telegram.org/botmock_bot_token/sendMessage").mock(return_value=Response(200, json={"ok": True}))
  respx.post("https://api.telegram.org/botmock_bot_token/sendChatAction").mock(return_value=Response(200, json={"ok": True}))

  await bot.poll_once(offset=None)
  assert send_message_route.called
  req_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "최근 거래 내역" in req_body
  assert "삼성전자" in req_body
  assert "KB증권 (일반 주식)" in req_body
  assert "750,000" in req_body


@pytest.mark.asyncio
@respx.mock
async def test_telegram_bot_cli_yearly_daily(mock_config, monkeypatch):
  """/yearly 및 /daily 명령어를 보냈을 때 연도별/일별 수익률 및 스냅샷 자산 상태를 표시하는지 테스트합니다."""
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")
  bot = TelegramBot(config=mock_config)

  # 1. /yearly 테스트
  updates_yearly = {
      "ok": True,
      "result": [{
          "update_id": 920,
          "message": {
              "message_id": 1,
              "chat": {"id": 12345, "type": "private"},
              "text": "/yearly",
          },
      }],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(return_value=Response(200, json=updates_yearly))

  yearly_json = [
      {
          "year": 2026,
          "contribution": 10000000.0,
          "profit": 5000000.0,
          "roi": 5.0,
          "assets": 150000000.0,
          "increase": 15000000.0
      }
  ]
  respx.get("http://mock-asset-server/api/dashboard/yearly").mock(return_value=Response(200, json=yearly_json))

  send_message_route = respx.post("https://api.telegram.org/botmock_bot_token/sendMessage").mock(return_value=Response(200, json={"ok": True}))
  respx.post("https://api.telegram.org/botmock_bot_token/sendChatAction").mock(return_value=Response(200, json={"ok": True}))

  await bot.poll_once(offset=None)
  assert send_message_route.called
  req_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "연도별 자산 및 투자 수익" in req_body
  assert "2026년" in req_body
  assert "150,000,000" in req_body

  # 2. /daily 테스트
  respx.clear()
  updates_daily = {
      "ok": True,
      "result": [{
          "update_id": 930,
          "message": {
              "message_id": 2,
              "chat": {"id": 12345, "type": "private"},
              "text": "/daily 3",
          },
      }],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(return_value=Response(200, json=updates_daily))

  daily_json = [
      {
          "date": "2026-07-19",
          "contribution": 0.0,
          "profit": 1200000.0,
          "roi": 0.8,
          "assets": 150000000.0,
          "increase": 1200000.0
      }
  ]
  respx.get("http://mock-asset-server/api/dashboard/daily").mock(return_value=Response(200, json=daily_json))
  send_message_route_daily = respx.post("https://api.telegram.org/botmock_bot_token/sendMessage").mock(return_value=Response(200, json={"ok": True}))
  respx.post("https://api.telegram.org/botmock_bot_token/sendChatAction").mock(return_value=Response(200, json={"ok": True}))

  await bot.poll_once(offset=None)
  assert send_message_route_daily.called
  req_body_daily = send_message_route_daily.calls.last.request.read().decode("utf-8")
  assert "일별 자산 및 투자 수익" in req_body_daily
  assert "150,000,000" in req_body_daily




