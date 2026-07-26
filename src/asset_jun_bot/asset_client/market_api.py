# -*- coding: utf-8 -*-
"""시장 지수, 휴장일, 관심종목, 시세 및 알림 관련 API 함수 모듈입니다."""

from typing import List, Dict
import httpx
from .models import (
    AssetClientError,
    WatchlistPricesResponse,
    WatchlistItemPrice,
    MarketIndicesResponse,
    MarketIndexItem,
    MarketHolidayResponse,
    MarketHistoryItem,
    StockPricesResponse,
    StockPriceItem,
)
from .base import load_config, handle_api_exception


async def get_watchlist_prices(country: str = "KR") -> WatchlistPricesResponse:
  """AssetManager API로부터 특정 국가의 관심종목 실시간 시세를 조회하여 Pydantic 모델로 반환합니다."""
  config = load_config()
  url = f"{config.asset_manager_api_url}/api/watchlist/prices"
  params = {"country": country.upper()}

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      prices = [
          WatchlistItemPrice(
              stock_name=item.get("stock_name", ""),
              stock_code=item.get("stock_code", ""),
              current_price=item.get("current_price", 0.0),
              change_rate=item.get("change_rate", 0.0),
          )
          for item in data
      ]

      return WatchlistPricesResponse(country=country.upper(), prices=prices)
  except Exception as exc:
    handle_api_exception(exc)


async def get_market_indices(country: str = "KR") -> MarketIndicesResponse:
  """AssetManager API로부터 KOSPI/KOSDAQ 또는 미국 지수 정보를 조회하여 Pydantic 모델로 반환합니다."""
  config = load_config()
  url = f"{config.asset_manager_api_url}/api/market/indices"
  params = {"country": country.upper()}

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      indices = [
          MarketIndexItem(
              index_name=item.get("index_name", ""),
              current_price=item.get("current_price", 0.0),
              change_rate=item.get("change_rate", 0.0),
          )
          for item in data
      ]

      return MarketIndicesResponse(indices=indices)
  except Exception as exc:
    handle_api_exception(exc)


async def check_market_holiday(date_str: str = "", country: str = "KR") -> MarketHolidayResponse:
  """AssetManager API로부터 특정 날짜의 특정 국가 시장 휴장일 여부를 조회하여 Pydantic 모델로 반환합니다."""
  config = load_config()
  url = f"{config.asset_manager_api_url}/api/market/holiday"
  params = {"country": country.upper()}
  if date_str:
    params["date"] = date_str

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      return MarketHolidayResponse(
          date=data.get("date", ""),
          country=data.get("country", country.upper()),
          is_holiday=data.get("is_holiday", False),
          description=data.get("description", "영업일"),
      )
  except Exception as exc:
    handle_api_exception(exc)


async def send_telegram_message(message: str, chat_id: int | None = None) -> str:
  """텔레그램을 통해 사용자에게 메시지를 전송합니다."""
  config = load_config()
  base_url = f"https://api.telegram.org/bot{config.telegram_bot_token}"
  url = f"{base_url}/sendMessage"

  if chat_id is not None:
    target_chat_ids = [chat_id]
  else:
    target_chat_ids = list(config.telegram_allowed_user_ids)

  if not target_chat_ids:
    raise AssetClientError("텔레그램 알림을 전송할 수 있는 허용된 사용자 ID가 존재하지 않습니다.")

  success_targets = []
  async with httpx.AsyncClient(timeout=10.0) as client:
    for tid in target_chat_ids:
      payload = {
          "chat_id": tid,
          "text": message,
      }

      try:
        from ..telegram_bot import markdown_to_html
        payload["text"] = markdown_to_html(message)
        payload["parse_mode"] = "HTML"
      except ImportError:
        pass

      try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        success_targets.append(str(tid))
      except Exception as exc:
        handle_api_exception(exc)

  return f"Telegram message sent successfully to {', '.join(success_targets)}."


async def resolve_redirect_url(url: str) -> str:
  """단축 URL 또는 리다이렉트 URL을 추적하여 최종 도달하는 원본 상세 URL을 반환합니다."""
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
          "AppleWebKit/537.36 (KHTML, like Gecko) "
          "Chrome/120.0.0.0 Safari/537.36"
      )
  }
  try:
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
      response = await client.get(url, headers=headers)
      return str(response.url)
  except Exception:
    return url


async def get_market_history(
    tickers: List[str],
    start_date: str | None = None,
    end_date: str | None = None
) -> Dict[str, List[MarketHistoryItem]]:
  """AssetManager API로부터 지정된 지수 티커들의 기간별 역사적 가격 및 실시간 현재가를 통합 조회합니다."""
  config = load_config()
  url = f"{config.asset_manager_api_url}/api/market/history"
  params = {"tickers": ",".join(tickers)}
  if start_date:
    params["start_date"] = start_date
  if end_date:
    params["end_date"] = end_date

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      results = {}
      for ticker, items in data.items():
        results[ticker] = [
            MarketHistoryItem(
                date=item.get("date", ""),
                close_price=item.get("close_price", 0.0)
            ) for item in items
        ]
      return results
  except Exception as exc:
    handle_api_exception(exc)


async def get_stock_prices(
    ticker: str,
    start_date: str,
    end_date: str | None = None
) -> StockPricesResponse:
  """AssetManager API로부터 특정 종목의 현재 및 과거 주가 데이터를 조회하여 Pydantic 모델로 반환합니다."""
  config = load_config()
  url = f"{config.asset_manager_api_url}/api/stocks/prices"
  params = {"ticker": ticker, "start_date": start_date}
  if end_date:
    params["end_date"] = end_date

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      prices = [
          StockPriceItem(
              date=item.get("date", ""),
              close_price=item.get("close_price", 0.0)
          ) for item in data.get("prices", [])
      ]

      return StockPricesResponse(
          ticker=data.get("ticker", ticker),
          name=data.get("name", ""),
          market=data.get("market", ""),
          prices=prices
      )
  except Exception as exc:
    handle_api_exception(exc)
