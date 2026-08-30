import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock, MagicMock, patch
from asset_jun_bot.config import Config
from asset_jun_bot.telegram_bot import TelegramBot
from asset_jun_bot.asset_client import sync_kiwoom_transactions, AssetClientError

@pytest.fixture
def mock_config(monkeypatch):
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_bot_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")
  monkeypatch.setenv("STORAGE_DIR", "mock_storage_dir")

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
@patch("asset_jun_bot.asset_client.Config.load")
async def test_sync_kiwoom_transactions_success(mock_load, mock_config):
  """API 호출 성공 시 올바른 dict 응답을 반환하는지 테스트합니다."""
  mock_load.return_value = mock_config
  mock_data = {
      "status": "success",
      "success_count": 2,
      "pending_count": 1,
      "synced_transactions": [
          {"type": "BUY", "asset_name": "삼성전자", "quantity": 10, "price": 72000, "total_amount": 720000, "currency": "KRW"}
      ],
      "unregistered_assets": [
          {"ticker": "NVDA", "name": "NVIDIA", "type": "BUY", "quantity": 3, "price": 120.0, "total_amount": 360.0, "currency": "USD"}
      ]
  }
  
  respx.post("http://mock-asset-server/api/kiwoom/sync-transactions").mock(
      return_value=Response(200, json=mock_data)
  )
  
  result = await sync_kiwoom_transactions(days=7)
  assert result["status"] == "success"
  assert result["success_count"] == 2
  assert result["pending_count"] == 1
  assert len(result["synced_transactions"]) == 1
  assert len(result["unregistered_assets"]) == 1

@pytest.mark.asyncio
@respx.mock
@patch("asset_jun_bot.asset_client.Config.load")
async def test_sync_kiwoom_transactions_error(mock_load, mock_config):
  """API 호출 에러 시 AssetClientError를 발생시키는지 테스트합니다."""
  mock_load.return_value = mock_config
  respx.post("http://mock-asset-server/api/kiwoom/sync-transactions").mock(
      return_value=Response(500)
  )
  
  with pytest.raises(AssetClientError):
    await sync_kiwoom_transactions(days=7)


@pytest.mark.asyncio
@respx.mock
@patch("asset_jun_bot.telegram_bot.sync_kiwoom_transactions")
async def test_telegram_bot_cli_sync_success(mock_sync, mock_config):
  """/sync 명령어를 보냈을 때 정상적으로 동기화를 수행하고 결과를 보고하는지 테스트합니다."""
  bot = TelegramBot(config=mock_config)
  
  mock_sync.return_value = {
      "status": "success",
      "success_count": 2,
      "pending_count": 1,
      "synced_transactions": [
          {"type": "BUY", "asset_name": "삼성전자", "quantity": 10, "price": 72000, "total_amount": 720000, "currency": "KRW"},
          {"type": "SELL", "asset_name": "Apple", "quantity": 5, "price": 185.0, "total_amount": 925.0, "currency": "USD"}
      ],
      "unregistered_assets": [
          {"ticker": "NVDA", "name": "NVIDIA", "type": "BUY", "quantity": 3, "price": 120.0, "total_amount": 360.0, "currency": "USD"}
      ]
  }

  updates_response = {
      "ok": True,
      "result": [
          {
              "update_id": 700,
              "message": {
                  "message_id": 2,
                  "chat": {"id": 12345, "type": "private"},
                  "text": "/sync 7",
              },
          }
      ],
  }
  respx.get("https://api.telegram.org/botmock_bot_token/getUpdates").mock(
      return_value=Response(200, json=updates_response)
  )

  respx.post("https://api.telegram.org/botmock_bot_token/sendChatAction").mock(
      return_value=Response(200, json={"ok": True})
  )

  send_message_route = respx.post(
      "https://api.telegram.org/botmock_bot_token/sendMessage"
  ).mock(return_value=Response(200, json={"ok": True}))

  next_offset = await bot.poll_once(offset=None)
  assert next_offset == 701
  mock_sync.assert_called_once_with(days=7)
  assert send_message_route.called

  req_body = send_message_route.calls.last.request.read().decode("utf-8")
  assert "키움증권 거래내역 자동 동기화 결과" in req_body
  assert "삼성전자" in req_body
  assert "NVIDIA" in req_body


def test_format_sync_result_message_with_failed_accounts():
  """failed_accounts 정보가 들어왔을 때 메시지에 실패 계좌 및 사유가 노출되는지 검증합니다."""
  from asset_jun_bot.telegram_bot.commands import format_sync_result_message

  result = {
      "status": "success",
      "success_count": 0,
      "pending_count": 0,
      "synced_transactions": [],
      "unregistered_assets": [],
      "failed_accounts": [
          {"account_name": "5526-9093", "error": "could not convert string to float: ''"}
      ]
  }

  msg = format_sync_result_message(result)
  assert "⚠️ **동기화 실패 계좌" in msg
  assert "5526-9093" in msg
  assert "could not convert string to float: ''" in msg

