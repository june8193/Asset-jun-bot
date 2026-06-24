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
    send_telegram_message,
    resolve_redirect_url,
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
  monkeypatch.setenv("NAVER_API_CLIENT_ID", "mock_naver_id")
  monkeypatch.setenv("NAVER_API_CLIENT_SECRET", "mock_naver_secret")


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
async def test_get_market_indices_us_success():
  """미국 시장 지수 조회 API 호출 성공 시 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
  mock_data = [
      {
          "index_name": "S&P 500",
          "current_price": 5400.50,
          "change_rate": 0.85
      },
      {
          "index_name": "NASDAQ",
          "current_price": 17850.20,
          "change_rate": 1.15
      },
      {
          "index_name": "DOW JONES",
          "current_price": 39500.10,
          "change_rate": 0.25
      }
  ]
  respx.get("http://mock-asset-server/api/market/indices?country=US").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_market_indices(country="US")
  assert isinstance(result, MarketIndicesResponse)
  assert len(result.indices) == 3
  assert result.indices[0].index_name == "S&P 500"
  assert result.indices[0].current_price == 5400.50
  assert result.indices[0].change_rate == 0.85
  assert result.indices[1].index_name == "NASDAQ"
  assert result.indices[1].current_price == 17850.20
  assert result.indices[1].change_rate == 1.15
  assert result.indices[2].index_name == "DOW JONES"
  assert result.indices[2].current_price == 39500.10
  assert result.indices[2].change_rate == 0.25


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


@pytest.mark.asyncio
@respx.mock
async def test_send_telegram_message_success_specific_chat():
  """지정된 특정 chat_id로 텔레그램 메시지가 성공적으로 전송되는지 테스트합니다."""
  respx.post("https://api.telegram.org/botmock_token/sendMessage").mock(
      return_value=Response(200, json={"ok": True, "result": {"message_id": 999}})
  )

  result = await send_telegram_message("테스트 메시지", chat_id=12345)
  assert "successfully" in result
  assert "12345" in result


@pytest.mark.asyncio
@respx.mock
async def test_send_telegram_message_success_all_allowed_users():
  """chat_id 미지정 시 허용된 모든 사용자에게 텔레그램 메시지가 성공적으로 전송되는지 테스트합니다."""
  route = respx.post("https://api.telegram.org/botmock_token/sendMessage").mock(
      return_value=Response(200, json={"ok": True, "result": {"message_id": 999}})
  )

  # Config에 정의된 TELEGRAM_ALLOWED_USER_IDS는 {12345} 임 (mock_config fixture 기준)
  result = await send_telegram_message("테스트 메시지")
  assert "successfully" in result
  assert "12345" in result
  assert route.call_count == 1


@pytest.mark.asyncio
@respx.mock
async def test_send_telegram_message_http_error():
  """텔레그램 API 호출 시 HTTP 에러가 발생하면 AssetClientError를 발생시키는지 테스트합니다."""
  respx.post("https://api.telegram.org/botmock_token/sendMessage").mock(
      return_value=Response(400, json={"ok": False, "description": "Bad Request"})
  )

  with pytest.raises(AssetClientError) as exc_info:
    await send_telegram_message("테스트 메시지", chat_id=12345)
  assert "HTTP" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_resolve_redirect_url_success():
  """리다이렉트 URL 추적에 성공하여 최종 URL을 잘 반환하는지 테스트합니다."""
  mock_redirect_url = "http://mock-asset-server/redirect"
  mock_final_url = "https://www.yna.co.kr/view/AKR12345"
  
  respx.get(mock_redirect_url).mock(
      return_value=Response(302, headers={"Location": mock_final_url})
  )
  respx.get(mock_final_url).mock(
      return_value=Response(200)
  )

  result = await resolve_redirect_url(mock_redirect_url)
  assert result == mock_final_url


@pytest.mark.asyncio
@respx.mock
async def test_resolve_redirect_url_failure():
  """리다이렉트 추적 중 네트워크 에러 등이 발생 시 원본 URL을 반환하는지 테스트합니다."""
  mock_redirect_url = "http://mock-redirect-fail"
  respx.get(mock_redirect_url).mock(
      side_effect=RequestError("Connection refused")
  )

  result = await resolve_redirect_url(mock_redirect_url)
  assert result == mock_redirect_url


@pytest.mark.asyncio
@respx.mock
async def test_check_market_holiday_no_date_kr_success():
  """date 파라미터가 없을 때 KR 국가 코드에 대해 타임존이 적용되어 동작하는지 테스트합니다."""
  mock_data = {
      "date": "2026-06-22",
      "country": "KR",
      "is_holiday": False,
      "description": "영업일"
  }
  respx.get("http://mock-asset-server/api/market/holiday?country=KR").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await check_market_holiday("", country="KR")
  assert isinstance(result, MarketHolidayResponse)
  assert result.date == "2026-06-22"
  assert result.country == "KR"
  assert result.is_holiday is False
  assert result.description == "영업일"


@pytest.mark.asyncio
@respx.mock
async def test_check_market_holiday_no_date_us_success():
  """date 파라미터가 없을 때 US 국가 코드에 대해 타임존이 적용되어 동작하는지 테스트합니다."""
  mock_data = {
      "date": "2026-06-21",
      "country": "US",
      "is_holiday": True,
      "description": "주말"
  }
  respx.get("http://mock-asset-server/api/market/holiday?country=US").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await check_market_holiday("", country="US")
  assert isinstance(result, MarketHolidayResponse)
  assert result.date == "2026-06-21"
  assert result.country == "US"
  assert result.is_holiday is True
  assert result.description == "주말"






