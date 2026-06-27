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
    get_market_history,
    get_stock_prices,
    get_portfolio_status,
    get_yearly_stats,
    get_daily_stats,
    get_snapshots,
    get_transactions,
    AssetSummaryResponse,
    AssetRatiosResponse,
    WatchlistPricesResponse,
    MarketIndicesResponse,
    MarketHolidayResponse,
    MarketHistoryItem,
    StockPricesResponse,
    StockPriceItem,
    PortfolioStatusResponse,
    PortfolioHoldingItem,
    YearlyStatsResponse,
    DailyStatsResponse,
    YearlyStatItem,
    DailyStatItem,
    SnapshotItem,
    SnapshotsResponse,
    TransactionItem,
    TransactionsResponse,
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
      "sub_results": [
          {
              "category": "미국 대형주",
              "parent_category": "주식",
              "current_amt": 30000000.0,
              "current_ratio": 50.0,
              "target_percentage": 50.0,
              "target_amt": 35000000.0,
              "diff_amt": 5000000.0
          }
      ]
  }
  respx.get("http://mock-asset-server/api/ratios/rebalancing").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_asset_ratios()
  assert isinstance(result, AssetRatiosResponse)
  assert result.total_valuation == 100000000.0
  assert result.total_target == 100000000.0
  assert result.additional_cash == 0.0

  assert len(result.major_results) == 2
  assert result.major_results[0].category == "현금"
  assert result.major_results[0].current_ratio == 40.0
  assert result.major_results[0].current_amt == 40000000.0
  assert result.major_results[0].target_percentage == 30.0
  assert result.major_results[0].target_amt == 30000000.0
  assert result.major_results[0].diff_amt == -10000000.0

  assert result.major_results[1].category == "주식"
  assert result.major_results[1].current_ratio == 60.0
  assert result.major_results[1].current_amt == 60000000.0
  assert result.major_results[1].target_percentage == 70.0
  assert result.major_results[1].target_amt == 70000000.0
  assert result.major_results[1].diff_amt == 10000000.0

  assert len(result.sub_results) == 1
  assert result.sub_results[0].category == "미국 대형주"
  assert result.sub_results[0].parent_category == "주식"
  assert result.sub_results[0].current_amt == 30000000.0
  assert result.sub_results[0].current_ratio == 50.0
  assert result.sub_results[0].target_percentage == 50.0
  assert result.sub_results[0].target_amt == 35000000.0
  assert result.sub_results[0].diff_amt == 5000000.0



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


@pytest.mark.asyncio
@respx.mock
async def test_get_market_history_success():
  """지수 과거 시계열 조회 API가 성공할 때 올바른 결과를 반환하는지 테스트합니다."""
  mock_data = {
      "^KS11": [
          {"date": "2026-06-25", "close_price": 2750.0},
          {"date": "2026-06-26", "close_price": 2760.0}
      ]
  }
  respx.get("http://mock-asset-server/api/market/history?tickers=%5EKS11&start_date=2026-06-25").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_market_history(tickers=["^KS11"], start_date="2026-06-25")
  assert isinstance(result, dict)
  assert "^KS11" in result
  assert len(result["^KS11"]) == 2
  assert isinstance(result["^KS11"][0], MarketHistoryItem)
  assert result["^KS11"][0].date == "2026-06-25"
  assert result["^KS11"][0].close_price == 2750.0


@pytest.mark.asyncio
@respx.mock
async def test_get_market_history_http_error():
  """지수 과거 시계열 조회 API 호출 실패 시 AssetClientError가 발생하는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/market/history?tickers=%5EKS11").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await get_market_history(tickers=["^KS11"])


@pytest.mark.asyncio
@respx.mock
async def test_get_stock_prices_success():
  """주식 가격 조회 API가 성공할 때 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
  mock_data = {
      "ticker": "005930",
      "name": "삼성전자",
      "market": "KOSPI",
      "prices": [
          {"date": "2026-06-25", "close_price": 75000.0},
          {"date": "2026-06-26", "close_price": 75200.0}
      ]
  }
  respx.get("http://mock-asset-server/api/stocks/prices?ticker=005930&start_date=2026-06-25").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_stock_prices(ticker="005930", start_date="2026-06-25")
  assert isinstance(result, StockPricesResponse)
  assert result.ticker == "005930"
  assert result.name == "삼성전자"
  assert result.market == "KOSPI"
  assert len(result.prices) == 2
  assert isinstance(result.prices[0], StockPriceItem)
  assert result.prices[0].date == "2026-06-25"
  assert result.prices[0].close_price == 75000.0


@pytest.mark.asyncio
@respx.mock
async def test_get_stock_prices_http_error():
  """주식 가격 조회 API 호출 실패 시 AssetClientError가 발생하는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/stocks/prices?ticker=005930&start_date=2026-06-25").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await get_stock_prices(ticker="005930", start_date="2026-06-25")


@pytest.mark.asyncio
@respx.mock
async def test_get_portfolio_status_success():
  """오늘 기준의 포트폴리오를 성공적으로 반환하는지 테스트합니다."""
  mock_data = {
      "total_valuation_krw": 150000000.0,
      "cash_balances": {"KRW": 10000000.0, "USD": 5000.0},
      "exchange_rate": 1350.0,
      "holdings": [
          {
              "ticker": "005930",
              "name": "삼성전자",
              "major_category": "주식",
              "sub_category": "대형주",
              "country": "KR",
              "quantity": 100.0,
              "current_price": 75000.0,
              "valuation": 7500000.0,
              "valuation_krw": 7500000.0,
          }
      ],
  }
  respx.get("http://mock-asset-server/api/portfolio/status").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_portfolio_status()
  assert isinstance(result, PortfolioStatusResponse)
  assert result.total_valuation_krw == 150000000.0
  assert result.cash_balances["KRW"] == 10000000.0
  assert result.cash_balances["USD"] == 5000.0
  assert result.exchange_rate == 1350.0
  assert len(result.holdings) == 1
  assert isinstance(result.holdings[0], PortfolioHoldingItem)
  assert result.holdings[0].ticker == "005930"
  assert result.holdings[0].name == "삼성전자"


@pytest.mark.asyncio
@respx.mock
async def test_get_portfolio_status_with_date_success():
  """특정 과거 날짜를 명시하여 호출했을 때 성공하는지 테스트합니다."""
  mock_data = {
      "total_valuation_krw": 140000000.0,
      "cash_balances": {"KRW": 9000000.0, "USD": 4500.0},
      "exchange_rate": 1340.0,
      "holdings": [],
  }
  respx.get("http://mock-asset-server/api/portfolio/status?date=2026-06-01").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_portfolio_status(date="2026-06-01")
  assert isinstance(result, PortfolioStatusResponse)
  assert result.total_valuation_krw == 140000000.0
  assert result.exchange_rate == 1340.0
  assert len(result.holdings) == 0


@pytest.mark.asyncio
@respx.mock
async def test_get_portfolio_status_http_error():
  """API 호출 시 HTTP 에러가 발생했을 때 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/portfolio/status").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError) as exc_info:
    await get_portfolio_status()
  assert "HTTP 오류" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_get_portfolio_status_network_error():
  """API 서버 연결 실패 시 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/portfolio/status").mock(
      side_effect=RequestError("Connection refused")
  )

  with pytest.raises(AssetClientError) as exc_info:
    await get_portfolio_status()
  assert "네트워크 오류" in str(exc_info.value) or "연결" in str(exc_info.value)


@pytest.mark.asyncio
@respx.mock
async def test_get_yearly_stats_success():
  """연도별 자산 현황 통계를 성공적으로 조회하는지 테스트합니다."""
  mock_data = [
      {
          "year": 2026,
          "contribution": 1000000.0,
          "profit": 500000.0,
          "roi": 5.0,
          "assets": 10500000.0,
          "increase": 1500000.0
      }
  ]
  respx.get("http://mock-asset-server/api/dashboard/yearly").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_yearly_stats()
  assert isinstance(result, YearlyStatsResponse)
  assert len(result.stats) == 1
  assert isinstance(result.stats[0], YearlyStatItem)
  assert result.stats[0].year == 2026
  assert result.stats[0].roi == 5.0
  assert result.stats[0].assets == 10500000.0


@pytest.mark.asyncio
@respx.mock
async def test_get_daily_stats_success():
  """일자별 자산 현황 통계를 성공적으로 조회하는지 테스트합니다."""
  mock_data = [
      {
          "date": "2026-06-27",
          "contribution": 100000.0,
          "profit": -5000.0,
          "roi": -0.5,
          "assets": 10450000.0,
          "increase": 95000.0
      }
  ]
  respx.get("http://mock-asset-server/api/dashboard/daily?all=false").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_daily_stats()
  assert isinstance(result, DailyStatsResponse)
  assert len(result.stats) == 1
  assert isinstance(result.stats[0], DailyStatItem)
  assert result.stats[0].date == "2026-06-27"
  assert result.stats[0].roi == -0.5


@pytest.mark.asyncio
@respx.mock
async def test_get_daily_stats_with_params_success():
  """일자별 자산 현황 통계를 파라미터와 함께 성공적으로 조회하는지 테스트합니다."""
  mock_data = []
  respx.get("http://mock-asset-server/api/dashboard/daily?all=true&start_date=2026-06-01&end_date=2026-06-27").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_daily_stats(start_date="2026-06-01", end_date="2026-06-27", all_data=True)
  assert isinstance(result, DailyStatsResponse)
  assert len(result.stats) == 0


@pytest.mark.asyncio
@respx.mock
async def test_get_snapshots_success():
  """스냅샷 조회 API가 성공할 때 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
  mock_data = [
      {
          "id": 1,
          "account_id": 10,
          "snapshot_date": "2026-06-26",
          "period_deposit": 50000.0,
          "total_valuation": 1200000.0,
          "total_profit": 150000.0
      }
  ]
  respx.get("http://mock-asset-server/api/db/snapshots").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_snapshots()
  assert isinstance(result, SnapshotsResponse)
  assert len(result.snapshots) == 1
  assert result.snapshots[0].id == 1
  assert result.snapshots[0].account_id == 10
  assert result.snapshots[0].snapshot_date == "2026-06-26"
  assert result.snapshots[0].period_deposit == 50000.0
  assert result.snapshots[0].total_valuation == 1200000.0
  assert result.snapshots[0].total_profit == 150000.0


@pytest.mark.asyncio
@respx.mock
async def test_get_snapshots_http_error():
  """스냅샷 조회 API 호출 실패 시 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/db/snapshots").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await get_snapshots()


@pytest.mark.asyncio
@respx.mock
async def test_get_snapshots_network_error():
  """스냅샷 조회 API 호출 시 네트워크 에러 발생할 때 AssetClientError를 반환하는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/db/snapshots").mock(
      side_effect=RequestError("Connection refused")
  )

  with pytest.raises(AssetClientError):
    await get_snapshots()


@pytest.mark.asyncio
@respx.mock
async def test_get_transactions_success():
  """거래내역 조회 API가 성공할 때 올바른 Pydantic 응답 모델을 반환하는지 테스트합니다."""
  mock_data = [
      {
          "id": 100,
          "account_id": 10,
          "asset_id": 5,
          "transaction_date": "2026-06-26",
          "type": "BUY",
          "quantity": 10.0,
          "price": 150.0,
          "total_amount": 1500.0,
          "currency": "USD",
          "exchange_rate": 1350.0,
          "memo": "Test memo",
          "asset_name": "Apple Inc.",
          "asset_ticker": "AAPL"
      }
  ]
  respx.get("http://mock-asset-server/api/db/transactions").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_transactions()
  assert isinstance(result, TransactionsResponse)
  assert len(result.transactions) == 1
  assert result.transactions[0].id == 100
  assert result.transactions[0].account_id == 10
  assert result.transactions[0].asset_id == 5
  assert result.transactions[0].transaction_date == "2026-06-26"
  assert result.transactions[0].type == "BUY"
  assert result.transactions[0].quantity == 10.0
  assert result.transactions[0].price == 150.0
  assert result.transactions[0].total_amount == 1500.0
  assert result.transactions[0].currency == "USD"
  assert result.transactions[0].exchange_rate == 1350.0
  assert result.transactions[0].memo == "Test memo"
  assert result.transactions[0].asset_name == "Apple Inc."
  assert result.transactions[0].asset_ticker == "AAPL"


@pytest.mark.asyncio
@respx.mock
async def test_get_transactions_with_date_success():
  """기간 파라미터가 포함된 거래내역 조회 API가 성공할 때 올바른 결과를 반환하는지 테스트합니다."""
  mock_data = []
  respx.get("http://mock-asset-server/api/db/transactions?start_date=2026-06-01&end_date=2026-06-26").mock(
      return_value=Response(200, json=mock_data)
  )

  result = await get_transactions(start_date="2026-06-01", end_date="2026-06-26")
  assert isinstance(result, TransactionsResponse)
  assert len(result.transactions) == 0


@pytest.mark.asyncio
@respx.mock
async def test_get_transactions_http_error():
  """거래내역 조회 API 호출 실패 시 AssetClientError 예외를 발생시키는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/db/transactions").mock(
      return_value=Response(500)
  )

  with pytest.raises(AssetClientError):
    await get_transactions()


@pytest.mark.asyncio
@respx.mock
async def test_get_transactions_network_error():
  """거래내역 조회 API 호출 시 네트워크 에러 발생할 때 AssetClientError를 반환하는지 테스트합니다."""
  respx.get("http://mock-asset-server/api/db/transactions").mock(
      side_effect=RequestError("Connection refused")
  )

  with pytest.raises(AssetClientError):
    await get_transactions()









