# -*- coding: utf-8 -*-
"""AssetManager API 클라이언트 테스트 모듈입니다."""

import pytest
import respx
from httpx import Response, HTTPStatusError, RequestError
from asset_jun_bot.config import Config
from asset_jun_bot.asset_client import get_asset_summary


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
  """테스트용 환경 변수 및 설정을 주입합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")
  monkeypatch.setenv("STORAGE_DIR", "mock_storage_dir")


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_summary_success():
  """API 호출 성공 시 올바른 텍스트를 반환하는지 테스트합니다."""
  # Mock API response
  mock_data = {
      "total_asset": 120000000,
      "total_debt": 20000000,
      "net_worth": 100000000,
      "roi": 12.5,
  }
  respx.get("http://mock-asset-server/api/dashboard/summary").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_asset_summary()
  assert "총 자산" in result
  assert "120,000,000" in result
  assert "순자산" in result
  assert "100,000,000" in result
  assert "수익률" in result
  assert "12.50%" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_summary_http_error():
  """API 호출 시 HTTP 에러가 발생했을 때 에러 메시지를 반환하는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/dashboard/summary").mock(
      return_value=Response(500)
  )

  result = await get_asset_summary()
  assert "오류" in result
  assert "500" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_summary_network_error():
  """API 서버가 다운되었거나 네트워크 오류 발생 시 에러 메시지를 반환하는지 테스트합니다."""
  # RequestError 발생 상황 모킹
  respx.get("http://mock-asset-server/api/dashboard/summary").mock(
      side_effect=RequestError("Connection refused")
  )

  result = await get_asset_summary()
  assert "네트워크 오류" in result or "연결" in result
