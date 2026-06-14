# -*- coding: utf-8 -*-
"""AssetManager API 클라이언트 테스트 모듈입니다."""

import pytest
import respx
from httpx import Response, RequestError
from asset_jun_bot.config import Config
from asset_jun_bot.asset_client import (
    get_asset_summary,
    get_asset_ratios,
    get_watchlist_prices,
    get_market_indices,
    check_market_holiday,
    AssetSummaryResponse,
    AssetRatiosResponse,
    WatchlistPricesResponse,
    MarketIndicesResponse,
    MarketHolidayResponse,
    AssetClientError,
)


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
  """테스트용 환경 변수 및 설정을 주입합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")
  monkeypatch.setenv("STORAGE_DIR", "mock_storage_dir")
  monkeypatch.setenv("MODEL_ROUTER", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_GENERAL_CONVERSATION", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_ASSET_INQUIRY", "gemini-1.5-flash")


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_summary_success():
  """API 호출 성공 시 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
  # Mock API response (자산 서버의 dashboard summary 실제 규격 반영)
  mock_data = {
      "total_valuation_krw": 120000000.0,
      "total_contribution": 80000000.0,
      "initial_base_asset": 20000000.0,
      "total_profit": 20000000.0,
      "cumulative_roi": 20.0,
      "contribution_ratio": 83.33,
      "profit_ratio": 16.67
  }
  respx.get("http://mock-asset-server/api/dashboard/summary").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_asset_summary()
  assert isinstance(result, AssetSummaryResponse)
  assert result.total_valuation_krw == 120000000.0
  assert result.total_principal == 100000000.0  # initial_base_asset (20M) + total_contribution (80M)
  assert result.total_profit == 20000000.0
  assert result.cumulative_roi == 20.0
  assert result.contribution_ratio == 83.33
  assert result.profit_ratio == 16.67


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_summary_http_error():
  """API 호출 시 HTTP 에러가 발생했을 때 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/dashboard/summary").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError) as exc_info:
    await get_asset_summary()
  assert "HTTP 오류" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_summary_network_error():
  """API 서버 연결 실패 시 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/dashboard/summary").mock(
      side_effect=RequestError("Connection refused")
  )

  with pytest.raises(AssetClientError) as exc_info:
    await get_asset_summary()
  assert "네트워크 오류" in str(exc_info.value) or "연결" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_ratios_success():
  """자산 비중 조회 API가 성공할 때 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
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
  assert isinstance(result, AssetRatiosResponse)
  assert len(result.major_results) == 2
  assert result.major_results[0].category == "현금"
  assert result.major_results[0].current_ratio == 40.0
  assert result.major_results[0].current_amt == 40000000.0
  assert result.major_results[1].category == "주식"
  assert result.major_results[1].current_ratio == 60.0
  assert result.major_results[1].current_amt == 60000000.0


@pytest.mark.asyncio
@respx.mock
async def test_get_asset_ratios_http_error():
  """자산 비중 조회 API 호출 실패 시 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/ratios/rebalancing").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await get_asset_ratios()


@pytest.mark.asyncio
@respx.mock
async def test_get_watchlist_prices_success():
  """관심종목 가격 조회 API가 성공할 때 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
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
  assert isinstance(result, WatchlistPricesResponse)
  assert result.country == "KR"
  assert len(result.prices) == 2
  assert result.prices[0].stock_name == "삼성전자"
  assert result.prices[0].stock_code == "005930"
  assert result.prices[0].current_price == 75000.0
  assert result.prices[0].change_rate == 1.25
  assert result.prices[1].stock_name == "SK하이닉스"
  assert result.prices[1].stock_code == "000660"
  assert result.prices[1].current_price == 142000.0
  assert result.prices[1].change_rate == -0.52


@pytest.mark.asyncio
@respx.mock
async def test_get_watchlist_prices_http_error():
  """관심종목 가격 조회 API 호출 실패 시 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/watchlist/prices?country=KR").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await get_watchlist_prices(country="KR")


@pytest.mark.asyncio
@respx.mock
async def test_get_market_indices_success():
  """시장 지수 조회 API 호출 성공 시 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
  mock_data = [
      {
          "index_name": "KOSPI",
          "current_price": 2700.50,
          "change_rate": 1.25
      },
      {
          "index_name": "KOSDAQ",
          "current_price": 850.20,
          "change_rate": -0.45
      }
  ]
  respx.get("http://mock-asset-server/api/market/indices").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_market_indices()
  assert isinstance(result, MarketIndicesResponse)
  assert len(result.indices) == 2
  assert result.indices[0].index_name == "KOSPI"
  assert result.indices[0].current_price == 2700.50
  assert result.indices[0].change_rate == 1.25
  assert result.indices[1].index_name == "KOSDAQ"
  assert result.indices[1].current_price == 850.20
  assert result.indices[1].change_rate == -0.45


@pytest.mark.asyncio
@respx.mock
async def test_get_market_indices_http_error():
  """시장 지수 조회 API 호출 시 HTTP 에러가 발생했을 때 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/market/indices").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await get_market_indices()


@pytest.mark.asyncio
@respx.mock
async def test_get_market_indices_network_error():
  """시장 지수 조회 API 호출 시 네트워크 에러가 발생했을 때 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/market/indices").mock(
      side_effect=RequestError("Connection refused")
  )

  with pytest.raises(AssetClientError):
    await get_market_indices()


@pytest.mark.asyncio
@respx.mock
async def test_check_market_holiday_success_holiday():
  """시장 휴장일 여부 조회 API 호출 성공 시 휴일 정보를 올바르게 반환하는지 테스트합니다."""
  mock_data = {
      "date": "2026-06-14",
      "country": "KR",
      "is_holiday": True,
      "description": "주말"
  }
  respx.get("http://mock-asset-server/api/market/holiday?date=2026-06-14&country=KR").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await check_market_holiday("2026-06-14", country="KR")
  assert isinstance(result, MarketHolidayResponse)
  assert result.date == "2026-06-14"
  assert result.country == "KR"
  assert result.is_holiday is True
  assert result.description == "주말"


@pytest.mark.asyncio
@respx.mock
async def test_check_market_holiday_success_workday():
  """시장 휴장일 여부 조회 API 호출 성공 시 영업일 정보를 올바르게 반환하는지 테스트합니다."""
  mock_data = {
      "date": "2026-06-15",
      "country": "KR",
      "is_holiday": False,
      "description": "영업일"
  }
  respx.get("http://mock-asset-server/api/market/holiday?date=2026-06-15&country=KR").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await check_market_holiday("2026-06-15", country="KR")
  assert isinstance(result, MarketHolidayResponse)
  assert result.date == "2026-06-15"
  assert result.country == "KR"
  assert result.is_holiday is False
  assert result.description == "영업일"


@pytest.mark.asyncio
@respx.mock
async def test_check_market_holiday_http_error():
  """시장 휴장일 여부 조회 API 호출 시 HTTP 에러 발생할 때 AssetClientError를 반환하는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/market/holiday?date=2026-06-14&country=KR").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await check_market_holiday("2026-06-14", country="KR")


