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


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_ratios_success():
  """자산 비중 조회 API가 성공할 때 올바르게 포맷팅된 문자열을 반환하는지 테스트합니다."""
  from asset_jun_bot.asset_client import get_asset_ratios

  mock_data = {
      "total_valuation": 100000000.0,
      "total_target": 100000000.0,
      "additional_cash": 0.0,
      "major_results": [
          {
              "category": "현금",
              "current_amt": 40000000.0,
              "current_ratio": 40.0,
              "target_percentage": 30.0,
              "target_amt": 30000000.0,
              "diff_amt": -10000000.0
          },
          {
              "category": "주식",
              "current_amt": 60000000.0,
              "current_ratio": 60.0,
              "target_percentage": 70.0,
              "target_amt": 70000000.0,
              "diff_amt": 10000000.0
          }
      ],
      "sub_results": []
  }
  respx.get("http://mock-asset-server/api/ratios/rebalancing").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_asset_ratios()
  assert "자산군별 비중" in result
  assert "현금" in result
  assert "40.00%" in result
  assert "40,000,000" in result
  assert "주식" in result
  assert "60.00%" in result
  assert "60,000,000" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_ratios_http_error():
  """자산 비중 조회 API 호출 실패 시 에러 메시지를 반환하는지 테스트합니다."""
  from asset_jun_bot.asset_client import get_asset_ratios

  respx.get("http://mock-asset-server/api/ratios/rebalancing").mock(
      return_value=Response(500)
  )

  result = await get_asset_ratios()
  assert "오류" in result or "실패" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_watchlist_prices_success():
  """관심종목 가격 조회 API가 성공할 때 올바르게 포맷팅된 문자열을 반환하는지 테스트합니다."""
  from asset_jun_bot.asset_client import get_watchlist_prices

  mock_data = [
      {
          "stock_code": "005930",
          "stock_name": "삼성전자",
          "current_price": 75000.0,
          "change_rate": 1.25
      },
      {
          "stock_code": "000660",
          "stock_name": "SK하이닉스",
          "current_price": 142000.0,
          "change_rate": -0.52
      }
  ]
  respx.get("http://mock-asset-server/api/watchlist/prices?country=KR").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_watchlist_prices(country="KR")
  assert "관심종목 시세" in result
  assert "삼성전자" in result
  assert "75,000" in result
  assert "+1.25%" in result
  assert "SK하이닉스" in result
  assert "142,000" in result
  assert "-0.52%" in result


@pytest.mark.asyncio
@respx.mock
async def test_get_watchlist_prices_http_error():
  """관심종목 가격 조회 API 호출 실패 시 에러 메시지를 반환하는지 테스트합니다."""
  from asset_jun_bot.asset_client import get_watchlist_prices

  respx.get("http://mock-asset-server/api/watchlist/prices?country=KR").mock(
      return_value=Response(500)
  )

  result = await get_watchlist_prices(country="KR")
  assert "오류" in result or "실패" in result

