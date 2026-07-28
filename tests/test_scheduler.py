# -*- coding: utf-8 -*-
"""TelegramScheduler 자동 동기화 메시지 미발송 조건에 대한 단위 테스트입니다."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from asset_jun_bot.telegram_bot.scheduler import TelegramScheduler


@pytest.fixture
def mock_client():
  client = MagicMock()
  client.send_message = AsyncMock()
  return client


@pytest.fixture
def mock_config():
  config = MagicMock()
  config.telegram_allowed_user_ids = {12345}
  return config


@pytest.mark.asyncio
async def test_execute_auto_sync_no_transactions_does_not_send_telegram_message(
    mock_client, mock_config
):
  """자동 동기화 결과 성공건수 및 미등록건수가 모두 0일 때 텔레그램 메시지를 전송하지 않는지 검증합니다."""
  scheduler = TelegramScheduler(client=mock_client, config=mock_config)

  empty_result = {
      "success_count": 0,
      "pending_count": 0,
      "synced_transactions": [],
      "unregistered_assets": [],
  }

  with patch(
      "asset_jun_bot.telegram_bot.scheduler.sync_kiwoom_transactions",
      new_callable=AsyncMock,
      return_value=empty_result,
  ):
    await scheduler._execute_auto_sync()

  # 거래건수가 0일 때 텔레그램 메시지가 전송되지 않아야 함
  mock_client.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_execute_auto_sync_with_success_transactions_sends_telegram_message(
    mock_client, mock_config
):
  """성공 내역(success_count > 0)이 있을 때는 텔레그램 메시지를 전송하는지 검증합니다."""
  scheduler = TelegramScheduler(client=mock_client, config=mock_config)

  success_result = {
      "success_count": 1,
      "pending_count": 0,
      "synced_transactions": [
          {
              "type": "BUY",
              "asset_name": "애플",
              "quantity": 10,
              "price": 150.0,
              "total_amount": 1500.0,
              "currency": "USD",
          }
      ],
      "unregistered_assets": [],
  }

  with patch(
      "asset_jun_bot.telegram_bot.scheduler.sync_kiwoom_transactions",
      new_callable=AsyncMock,
      return_value=success_result,
  ):
    await scheduler._execute_auto_sync()

  # 텔레그램 메시지가 전송되어야 함
  mock_client.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_execute_auto_sync_with_pending_transactions_sends_telegram_message(
    mock_client, mock_config
):
  """자산 마스터 미등록 거래(pending_count > 0)가 있을 때도 텔레그램 메시지를 전송하는지 검증합니다."""
  scheduler = TelegramScheduler(client=mock_client, config=mock_config)

  pending_result = {
      "success_count": 0,
      "pending_count": 1,
      "synced_transactions": [],
      "unregistered_assets": [
          {
              "type": "BUY",
              "asset_name": "신규종목",
              "quantity": 5,
              "price": 10000.0,
              "total_amount": 50000.0,
              "currency": "KRW",
          }
      ],
  }

  with patch(
      "asset_jun_bot.telegram_bot.scheduler.sync_kiwoom_transactions",
      new_callable=AsyncMock,
      return_value=pending_result,
  ):
    await scheduler._execute_auto_sync()

  # 텔레그램 메시지가 전송되어야 함
  mock_client.send_message.assert_called_once()
