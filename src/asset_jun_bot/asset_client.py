# -*- coding: utf-8 -*-
"""AssetManager API와 통신하여 자산 정보를 가져오는 클라이언트 모듈입니다.

이 모듈은 API 호출 결과를 마크다운 스트링이 아닌 Pydantic 모델 형태의 구조화된 데이터로
반환하며, 통신 실패 시 명시적인 AssetClientError 예외를 발생시킵니다.
"""

from typing import List, Dict
import httpx
from pydantic import BaseModel, Field
from .config import Config


class AssetClientError(Exception):
  """AssetManager API 클라이언트 에러를 나타내는 예외 클래스입니다."""
  pass


class AssetSummaryResponse(BaseModel):
  """자산 요약 정보 응답 Pydantic 모델입니다.

  Attributes:
      total_valuation_krw: 총 평가자산 (원화 환산)
      total_principal: 총 투자 원금 (최초 기초 자산 + 누적 추가액)
      total_profit: 누적 투자 수익
      cumulative_roi: 누적 투자수익률 (%)
      contribution_ratio: 투자원금 비율 (%)
      profit_ratio: 투자수익 비율 (%)
  """
  total_valuation_krw: float = Field(..., description="총 평가자산 (KRW)")
  total_principal: float = Field(..., description="총 투자 원금 (최초 기초 자산 + 누적 추가액)")
  total_profit: float = Field(..., description="누적 투자 수익")
  cumulative_roi: float = Field(..., description="누적 투자수익률 (%)")
  contribution_ratio: float = Field(..., description="투자원금 비율 (%)")
  profit_ratio: float = Field(..., description="투자수익 비율 (%)")


class AssetRatioItem(BaseModel):
  """자산 분류별 세부 비중 및 리밸런싱 정보 모델입니다.

  Attributes:
      category: 자산 분류 명칭 (대분류 또는 소분류)
      parent_category: 상위 대분류 명칭 (소분류인 경우)
      current_amt: 현재 평가액
      current_ratio: 현재 비중 (%)
      target_percentage: 목표 비중 (%)
      target_amt: 목표 평가액 (KRW)
      diff_amt: 목표 비중 대비 차액 (조정 필요 금액, KRW)
  """
  category: str = Field(..., description="자산 분류 명칭")
  parent_category: str | None = Field(None, description="상위 대분류 명칭 (소분류인 경우)")
  current_amt: float = Field(..., description="현재 평가액 (KRW)")
  current_ratio: float = Field(..., description="현재 비중 (%)")
  target_percentage: float = Field(..., description="목표 비중 (%)")
  target_amt: float = Field(..., description="목표 평가액 (KRW)")
  diff_amt: float = Field(..., description="목표 비중 대비 차액 (조정 필요 금액, KRW)")


class AssetRatiosResponse(BaseModel):
  """자산군별 비중 현황 및 리밸런싱 가이드 응답 Pydantic 모델입니다.

  Attributes:
      total_valuation: 현재 총 평가액 (KRW)
      total_target: 목표 총액 (KRW)
      additional_cash: 추가 투자금 (KRW)
      major_results: 자산 대분류별 비중 및 리밸런싱 결과 목록
      sub_results: 자산 소분류별 비중 및 리밸런싱 결과 목록
  """
  total_valuation: float = Field(..., description="현재 총 평가액 (KRW)")
  total_target: float = Field(..., description="목표 총액 (KRW)")
  additional_cash: float = Field(..., description="추가 투자금 (KRW)")
  major_results: List[AssetRatioItem] = Field(..., description="자산 대분류별 비중 목록")
  sub_results: List[AssetRatioItem] = Field(..., description="자산 소분류별 비중 목록")


class WatchlistItemPrice(BaseModel):
  """관심종목의 시세 정보 모델입니다.

  Attributes:
      stock_name: 종목명
      stock_code: 종목코드
      current_price: 현재가
      change_rate: 전일 대비 등락률 (%)
  """
  stock_name: str = Field(..., description="종목명")
  stock_code: str = Field(..., description="종목코드")
  current_price: float = Field(..., description="현재가")
  change_rate: float = Field(..., description="등락률 (%)")


class WatchlistPricesResponse(BaseModel):
  """관심종목 시세 현황 응답 Pydantic 모델입니다.

  Attributes:
      country: 국가 구분 (KR/US)
      prices: 관심종목 시세 목록
  """
  country: str = Field(..., description="국가 구분 (KR/US)")
  prices: List[WatchlistItemPrice] = Field(..., description="관심종목 목록")


class MarketIndexItem(BaseModel):
  """시장 지수 세부 정보 모델입니다.

  Attributes:
      index_name: 지수 명칭 (예: KOSPI, KOSDAQ 등)
      current_price: 현재 지수 포인트 값
      change_rate: 전일 대비 등락률 (%)
  """
  index_name: str = Field(..., description="지수 명칭")
  current_price: float = Field(..., description="현재 지수 값")
  change_rate: float = Field(..., description="등락률 (%)")


class MarketIndicesResponse(BaseModel):
  """시장 지수 목록 응답 Pydantic 모델입니다.

  Attributes:
      indices: 시장 지수 목록
  """
  indices: List[MarketIndexItem] = Field(..., description="시장 지수 목록")


class MarketHolidayResponse(BaseModel):
  """시장 휴장일 여부 응답 Pydantic 모델입니다.

  Attributes:
      date: 검증 대상 날짜 (YYYY-MM-DD)
      country: 국가 코드 (KR, US 등)
      is_holiday: 휴장일 여부 (True인 경우 휴장일)
      description: 휴장 사유 (예: 주말, 설 연휴, 영업일 등)
  """
  date: str = Field(..., description="검증 대상 날짜")
  country: str = Field(..., description="국가 코드")
  is_holiday: bool = Field(..., description="휴장일 여부")
  description: str = Field(..., description="휴장 사유")


class MarketHistoryItem(BaseModel):
  """시장 지수 일자별 가격 정보를 나타내는 Pydantic 모델입니다.

  Attributes:
      date: 날짜 (YYYY-MM-DD)
      close_price: 종가 또는 실시간 현재가
  """
  date: str = Field(..., description="날짜 (YYYY-MM-DD)")
  close_price: float = Field(..., description="종가 또는 실시간 현재가")


class StockPriceItem(BaseModel):
  """주식의 일자별 가격 정보를 나타내는 Pydantic 모델입니다.

  Attributes:
      date: 날짜 (YYYY-MM-DD)
      close_price: 종가 또는 실시간 현재가
  """
  date: str = Field(..., description="날짜 (YYYY-MM-DD)")
  close_price: float = Field(..., description="종가 또는 실시간 현재가")


class StockPricesResponse(BaseModel):
  """주식 가격 조회 응답 Pydantic 모델입니다.

  Attributes:
      ticker: 종목코드 또는 티커
      name: 종목명
      market: 상장 시장 (KOSPI, KOSDAQ, US 등)
      prices: 일자별 주가 목록
  """
  ticker: str = Field(..., description="종목코드 또는 티커")
  name: str = Field(..., description="종목명")
  market: str = Field(..., description="상장 시장 (KOSPI, KOSDAQ, US 등)")
  prices: List[StockPriceItem] = Field(..., description="일자별 주가 목록")


class PortfolioHoldingItem(BaseModel):
  """포트폴리오 내 개별 보유 자산 정보 모델입니다.

  Attributes:
      ticker: 종목코드 또는 티커
      name: 종목명
      major_category: 자산 대분류 (예: 주식, 현금 등)
      sub_category: 자산 소분류 (예: 대형주, 배당주 등)
      country: 국가 구분 (KR/US)
      quantity: 보유 수량
      current_price: 현재 가격
      valuation: 평가액 (해당 통화 기준)
      valuation_krw: 원화 환산 평가액
  """
  ticker: str = Field(..., description="종목코드 또는 티커")
  name: str = Field(..., description="종목명")
  major_category: str = Field(..., description="자산 대분류")
  sub_category: str = Field(..., description="자산 소분류")
  country: str = Field(..., description="국가 구분 (KR/US)")
  quantity: float = Field(..., description="보유 수량")
  current_price: float = Field(..., description="현재 가격")
  valuation: float = Field(..., description="평가액 (해당 통화)")
  valuation_krw: float = Field(..., description="원화 환산 평가액 (KRW)")


class PortfolioStatusResponse(BaseModel):
  """포트폴리오 자산 구성 및 보유 종목 현황 응답 Pydantic 모델입니다.

  Attributes:
      total_valuation_krw: 총 평가자산 (원화 환산)
      cash_balances: 예수금 잔고 (통화별 매핑)
      exchange_rate: 적용 기준 환율
      holdings: 보유 종목 목록
  """
  total_valuation_krw: float = Field(..., description="총 평가자산 (KRW)")
  cash_balances: Dict[str, float] = Field(..., description="예수금 잔고 (통화별 매핑)")
  exchange_rate: float = Field(..., description="적용 기준 환율")
  holdings: List[PortfolioHoldingItem] = Field(..., description="보유 종목 목록")





async def get_asset_summary() -> AssetSummaryResponse:
  """AssetManager API로부터 자산 요약 정보를 조회하여 Pydantic 모델로 반환합니다.

  Returns:
      AssetSummaryResponse: 자산 총액, 총 투자원금, 투자수익 등의 데이터를 담은 Pydantic 객체

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  url = f"{config.asset_manager_api_url}/api/dashboard/summary"

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url)
      response.raise_for_status()
      data = response.json()

      total_asset = data.get("total_valuation_krw", 0.0)
      total_contribution = data.get("total_contribution", 0.0)
      initial_base = data.get("initial_base_asset", 0.0)
      total_principal = initial_base + total_contribution
      total_profit = data.get("total_profit", 0.0)
      roi = data.get("cumulative_roi", 0.0)
      contribution_ratio = data.get("contribution_ratio", 100.0)
      profit_ratio = data.get("profit_ratio", 0.0)

      return AssetSummaryResponse(
          total_valuation_krw=total_asset,
          total_principal=total_principal,
          total_profit=total_profit,
          cumulative_roi=roi,
          contribution_ratio=contribution_ratio,
          profit_ratio=profit_ratio,
      )

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc


async def get_asset_ratios() -> AssetRatiosResponse:
  """AssetManager API로부터 자산군별 백분율 비중 및 리밸런싱 정보를 조회하여 Pydantic 모델로 반환합니다.

  Returns:
      AssetRatiosResponse: 자산군별 백분율 비중 및 리밸런싱 현황을 담은 Pydantic 객체

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  url = f"{config.asset_manager_api_url}/api/ratios/rebalancing"

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url)
      response.raise_for_status()
      data = response.json()

      major_results = data.get("major_results", [])
      major_items = []
      for item in major_results:
        major_items.append(
            AssetRatioItem(
                category=item.get("category", "미분류"),
                parent_category=None,
                current_amt=item.get("current_amt", 0.0),
                current_ratio=item.get("current_ratio", 0.0),
                target_percentage=item.get("target_percentage", 0.0),
                target_amt=item.get("target_amt", 0.0),
                diff_amt=item.get("diff_amt", 0.0),
            )
        )

      sub_results = data.get("sub_results", [])
      sub_items = []
      for item in sub_results:
        sub_items.append(
            AssetRatioItem(
                category=item.get("category", "미분류"),
                parent_category=item.get("parent_category"),
                current_amt=item.get("current_amt", 0.0),
                current_ratio=item.get("current_ratio", 0.0),
                target_percentage=item.get("target_percentage", 0.0),
                target_amt=item.get("target_amt", 0.0),
                diff_amt=item.get("diff_amt", 0.0),
            )
        )

      return AssetRatiosResponse(
          total_valuation=data.get("total_valuation", 0.0),
          total_target=data.get("total_target", 0.0),
          additional_cash=data.get("additional_cash", 0.0),
          major_results=major_items,
          sub_results=sub_items,
      )

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc


async def get_watchlist_prices(country: str = "KR") -> WatchlistPricesResponse:
  """AssetManager API로부터 특정 국가의 관심종목 실시간 시세를 조회하여 Pydantic 모델로 반환합니다.

  Args:
      country: 조회할 국가 구분 ("KR" 또는 "US", 기본값 "KR")

  Returns:
      WatchlistPricesResponse: 관심종목별 현재가 및 등락률 목록을 담은 Pydantic 객체

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  url = f"{config.asset_manager_api_url}/api/watchlist/prices"
  params = {"country": country.upper()}

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      prices = []
      for item in data:
        prices.append(
            WatchlistItemPrice(
                stock_name=item.get("stock_name", ""),
                stock_code=item.get("stock_code", ""),
                current_price=item.get("current_price", 0.0),
                change_rate=item.get("change_rate", 0.0),
            )
        )

      return WatchlistPricesResponse(country=country.upper(), prices=prices)

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc


async def get_market_indices(country: str = "KR") -> MarketIndicesResponse:
  """AssetManager API로부터 KOSPI/KOSDAQ 또는 미국 지수 정보를 조회하여 Pydantic 모델로 반환합니다.

  Args:
      country: 조회할 국가 구분 ("KR" 또는 "US", 기본값 "KR")

  Returns:
      MarketIndicesResponse: 지수 정보를 담은 Pydantic 객체

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  url = f"{config.asset_manager_api_url}/api/market/indices"
  params = {"country": country.upper()}

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      indices = []
      for item in data:
        indices.append(
            MarketIndexItem(
                index_name=item.get("index_name", ""),
                current_price=item.get("current_price", 0.0),
                change_rate=item.get("change_rate", 0.0),
            )
        )

      return MarketIndicesResponse(indices=indices)

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc


async def check_market_holiday(date_str: str = "", country: str = "KR") -> MarketHolidayResponse:
  """AssetManager API로부터 특정 날짜의 특정 국가 시장 휴장일 여부를 조회하여 Pydantic 모델로 반환합니다.

  Args:
      date_str: 조회할 날짜 ("YYYY-MM-DD", 기본값 ""인 경우 오늘 날짜)
      country: 국가 코드 ("KR" 또는 "US", 기본값 "KR")

  Returns:
      MarketHolidayResponse: 시장 휴장일 판정 데이터를 담은 Pydantic 객체

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

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

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc


async def send_telegram_message(message: str, chat_id: int | None = None) -> str:
  """텔레그램을 통해 사용자에게 메시지를 전송합니다.

  Args:
      message: 전송할 메시지 내용 (마크다운 형식 지원)
      chat_id: 전송할 텔레그램 대화방 ID (생략 시 설정된 모든 허용된 사용자에게 전송)

  Returns:
      str: 전송 결과 메시지

  Raises:
      AssetClientError: 설정 로드 실패 또는 텔레그램 API 호출 실패 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  base_url = f"https://api.telegram.org/bot{config.telegram_bot_token}"
  url = f"{base_url}/sendMessage"

  # 전송 대상 chat_id 리스트 결정
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

      # 마크다운 변환 적용
      try:
        from .telegram_bot import markdown_to_html
        payload["text"] = markdown_to_html(message)
        payload["parse_mode"] = "HTML"
      except ImportError:
        pass

      try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        success_targets.append(str(tid))
      except httpx.HTTPStatusError as exc:
        raise AssetClientError(
            f"텔레그램 메시지 전송 실패 (HTTP 오류 코드: {exc.response.status_code}, 상세: {exc.response.text})"
        ) from exc
      except httpx.RequestError as exc:
        raise AssetClientError(
            f"텔레그램 API 서버 연결 네트워크 오류: {exc}"
        ) from exc
      except Exception as exc:
        raise AssetClientError(f"텔레그램 전송 중 알 수 없는 오류 발생: {exc}") from exc

  return f"Telegram message sent successfully to {', '.join(success_targets)}."


async def resolve_redirect_url(url: str) -> str:
  """단축 URL 또는 리다이렉트 URL을 추적하여 최종 도달하는 원본 상세 URL을 반환합니다.

  Args:
      url: 리다이렉션을 추적할 대상 URL

  Returns:
      str: 최종 도달한 원본 URL (에러 발생 시 입력받은 url을 그대로 반환)
  """
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
    # 네트워크 에러 또는 타임아웃 발생 시 입력된 원본 URL을 폴백으로 반환합니다.
    return url


async def get_market_history(
    tickers: List[str],
    start_date: str | None = None,
    end_date: str | None = None
) -> Dict[str, List[MarketHistoryItem]]:
  """AssetManager API로부터 지정된 지수 티커들의 기간별 역사적 가격 및 실시간 현재가를 통합 조회합니다.

  Args:
      tickers: 조회할 지수 티커 리스트 (예: ["^KS11", "^GSPC"])
      start_date: 조회 시작일 ("YYYY-MM-DD", 생략 시 API 기본값인 30일 전)
      end_date: 조회 종료일 ("YYYY-MM-DD", 생략 시 API 기본값인 오늘)

  Returns:
      Dict[str, List[MarketHistoryItem]]: 티커별 일자별 지수 데이터 매핑 딕셔너리

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

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

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc


async def get_stock_prices(
    ticker: str,
    start_date: str,
    end_date: str | None = None
) -> StockPricesResponse:
  """AssetManager API로부터 특정 종목의 현재 및 과거 주가 데이터를 조회하여 Pydantic 모델로 반환합니다.

  Args:
      ticker: 종목코드 또는 티커 (예: "005930", "AAPL")
      start_date: 조회 시작일 ("YYYY-MM-DD")
      end_date: 조회 종료일 ("YYYY-MM-DD", 생략 시 API 기본값인 오늘)

  Returns:
      StockPricesResponse: 종목 정보 및 일자별 주가 데이터를 담은 Pydantic 객체

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

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

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc


async def get_portfolio_status(date: str | None = None) -> PortfolioStatusResponse:
  """AssetManager API로부터 포트폴리오 상태(보유 자산 및 예수금 현황)를 조회하여 Pydantic 모델로 반환합니다.

  Args:
      date: 조회 기준일 ("YYYY-MM-DD", 생략 시 오늘)

  Returns:
      PortfolioStatusResponse: 포트폴리오 상세 데이터를 담은 Pydantic 객체

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  url = f"{config.asset_manager_api_url}/api/portfolio/status"
  params = {}
  if date:
    params["date"] = date

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, params=params)
      response.raise_for_status()
      data = response.json()

      holdings = []
      for item in data.get("holdings", []):
        holdings.append(
            PortfolioHoldingItem(
                ticker=item.get("ticker", ""),
                name=item.get("name", ""),
                major_category=item.get("major_category", ""),
                sub_category=item.get("sub_category", ""),
                country=item.get("country", ""),
                quantity=item.get("quantity", 0.0),
                current_price=item.get("current_price", 0.0),
                valuation=item.get("valuation", 0.0),
                valuation_krw=item.get("valuation_krw", 0.0),
            )
        )

      return PortfolioStatusResponse(
          total_valuation_krw=data.get("total_valuation_krw", 0.0),
          cash_balances=data.get("cash_balances", {}),
          exchange_rate=data.get("exchange_rate", 1.0),
          holdings=holdings,
      )

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"AssetManager API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"AssetManager API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"알 수 없는 오류 발생: {exc}") from exc





