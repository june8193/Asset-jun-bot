# -*- coding: utf-8 -*-
"""AssetManager API 클라이언트 데이터 모델 및 예외 정의 모듈입니다."""

from typing import List, Dict
from pydantic import BaseModel, Field


class AssetClientError(Exception):
  """AssetManager API 클라이언트 에러를 나타내는 예외 클래스입니다."""
  pass


class AssetSummaryResponse(BaseModel):
  """자산 요약 정보 응답 Pydantic 모델입니다."""
  total_valuation_krw: float = Field(..., description="총 평가자산 (KRW)")
  total_principal: float = Field(..., description="총 투자 원금 (최초 기초 자산 + 누적 추가액)")
  total_profit: float = Field(..., description="누적 투자 수익")
  cumulative_roi: float = Field(..., description="누적 투자수익률 (%)")
  contribution_ratio: float = Field(..., description="투자원금 비율 (%)")
  profit_ratio: float = Field(..., description="투자수익 비율 (%)")
  exchange_rate: dict = Field(..., description="환율 정보")
  latest_price_date: str = Field(..., description="최신 주가 기준일")


class AssetRatioItem(BaseModel):
  """자산 분류별 세부 비중 및 리밸런싱 정보 모델입니다."""
  category: str = Field(..., description="자산 분류 명칭")
  parent_category: str | None = Field(None, description="상위 대분류 명칭 (소분류인 경우)")
  current_amt: float = Field(..., description="현재 평가액 (KRW)")
  current_ratio: float = Field(..., description="현재 비중 (%)")
  target_percentage: float = Field(..., description="목표 비중 (%)")
  target_amt: float = Field(..., description="목표 평가액 (KRW)")
  diff_amt: float = Field(..., description="목표 비중 대비 차액 (조정 필요 금액, KRW)")


class AssetRatiosResponse(BaseModel):
  """자산군별 비중 현황 및 리밸런싱 가이드 응답 Pydantic 모델입니다."""
  total_valuation: float = Field(..., description="현재 총 평가액 (KRW)")
  total_target: float = Field(..., description="목표 총액 (KRW)")
  additional_cash: float = Field(..., description="추가 투자금 (KRW)")
  major_results: List[AssetRatioItem] = Field(..., description="자산 대분류별 비중 목록")
  sub_results: List[AssetRatioItem] = Field(..., description="자산 소분류별 비중 목록")


class WatchlistItemPrice(BaseModel):
  """관심종목의 시세 정보 모델입니다."""
  stock_name: str = Field(..., description="종목명")
  stock_code: str = Field(..., description="종목코드")
  current_price: float = Field(..., description="현재가")
  change_rate: float = Field(..., description="등락률 (%)")


class WatchlistPricesResponse(BaseModel):
  """관심종목 시세 현황 응답 Pydantic 모델입니다."""
  country: str = Field(..., description="국가 구분 (KR/US)")
  prices: List[WatchlistItemPrice] = Field(..., description="관심종목 목록")


class MarketIndexItem(BaseModel):
  """시장 지수 세부 정보 모델입니다."""
  index_name: str = Field(..., description="지수 명칭")
  current_price: float = Field(..., description="현재 지수 값")
  change_rate: float = Field(..., description="등락률 (%)")


class MarketIndicesResponse(BaseModel):
  """시장 지수 목록 응답 Pydantic 모델입니다."""
  indices: List[MarketIndexItem] = Field(..., description="시장 지수 목록")


class MarketHolidayResponse(BaseModel):
  """시장 휴장일 여부 응답 Pydantic 모델입니다."""
  date: str = Field(..., description="검증 대상 날짜")
  country: str = Field(..., description="국가 코드")
  is_holiday: bool = Field(..., description="휴장일 여부")
  description: str = Field(..., description="휴장 사유")


class MarketHistoryItem(BaseModel):
  """시장 지수 일자별 가격 정보를 나타내는 Pydantic 모델입니다."""
  date: str = Field(..., description="날짜 (YYYY-MM-DD)")
  close_price: float = Field(..., description="종가 또는 실시간 현재가")


class StockPriceItem(BaseModel):
  """주식의 일자별 가격 정보를 나타내는 Pydantic 모델입니다."""
  date: str = Field(..., description="날짜 (YYYY-MM-DD)")
  close_price: float = Field(..., description="종가 또는 실시간 현재가")


class StockPricesResponse(BaseModel):
  """주식 가격 조회 응답 Pydantic 모델입니다."""
  ticker: str = Field(..., description="종목코드 또는 티커")
  name: str = Field(..., description="종목명")
  market: str = Field(..., description="상장 시장 (KOSPI, KOSDAQ, US 등)")
  prices: List[StockPriceItem] = Field(..., description="일자별 주가 목록")


class PortfolioHoldingItem(BaseModel):
  """포트폴리오 내 개별 보유 자산 정보 모델입니다."""
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
  """포트폴리오 자산 구성 및 보유 종목 현황 응답 Pydantic 모델입니다."""
  total_valuation_krw: float = Field(..., description="총 평가자산 (KRW)")
  cash_balances: Dict[str, float] = Field(..., description="예수금 잔고 (통화별 매핑)")
  exchange_rate: float = Field(..., description="적용 기준 환율")
  holdings: List[PortfolioHoldingItem] = Field(..., description="보유 종목 목록")


class YearlyStatItem(BaseModel):
  """연도별 자산 현황 통계 아이템 모델입니다."""
  year: int = Field(..., description="연도")
  contribution: float = Field(..., description="순 추가액 (KRW)")
  profit: float = Field(..., description="연간 투자 수익 (KRW)")
  roi: float = Field(..., description="연간 투자수익률 (%)")
  assets: float = Field(..., description="기말 자산 평가액 (KRW)")
  increase: float = Field(..., description="자산 증감액 (KRW)")


class YearlyStatsResponse(BaseModel):
  """연도별 자산 현황 통계 응답 모델입니다."""
  stats: List[YearlyStatItem] = Field(..., description="연도별 자산 현황 목록")


class DailyStatItem(BaseModel):
  """일자별 자산 현황 통계 아이템 모델입니다."""
  date: str = Field(..., description="날짜 (YYYY-MM-DD)")
  contribution: float = Field(..., description="추가액 (KRW)")
  profit: float = Field(..., description="투자 수익 (KRW)")
  roi: float = Field(..., description="투자수익률 (%)")
  assets: float = Field(..., description="자산 평가액 (KRW)")
  increase: float = Field(..., description="자산 증감액 (KRW)")


class DailyStatsResponse(BaseModel):
  """일자별 자산 현황 통계 응답 모델입니다."""
  stats: List[DailyStatItem] = Field(..., description="일자별 자산 현황 목록")


class TransactionItem(BaseModel):
  """개별 거래 내역 정보 모델입니다."""
  id: int | None = Field(None, description="거래 식별자")
  account_id: int = Field(..., description="계좌 식별자")
  asset_id: int = Field(..., description="자산 식별자")
  transaction_date: str = Field(..., description="거래 일자 (YYYY-MM-DD)")
  type: str = Field(..., description="거래 유형 (BUY, SELL 등)")
  quantity: float = Field(0.0, description="수량")
  price: float = Field(0.0, description="단가")
  total_amount: float = Field(..., description="총 거래 금액")
  currency: str = Field(..., description="통화 (KRW, USD)")
  exchange_rate: float | None = Field(None, description="환율")
  memo: str | None = Field(None, description="메모")
  asset_name: str | None = Field(None, description="자산명")
  asset_ticker: str | None = Field(None, description="자산 티커")
  account_display_name: str | None = Field(None, description="계좌 표시 이름")


class TransactionsResponse(BaseModel):
  """거래 내역 목록 응답 모델입니다."""
  transactions: List[TransactionItem] = Field(..., description="거래 내역 목록")


class SnapshotItem(BaseModel):
  """계좌 상태 스냅샷 정보 모델입니다."""
  id: int = Field(..., description="스냅샷 식별자")
  account_id: int = Field(..., description="계좌 식별자")
  snapshot_date: str = Field(..., description="기준 일자 (YYYY-MM-DD)")
  period_deposit: float = Field(..., description="해당 기간 추가 입금액")
  total_valuation: float = Field(..., description="총 평가액")
  total_profit: float = Field(..., description="누적 수익")


class SnapshotsResponse(BaseModel):
  """자산 상태 스냅샷 목록 응답 모델입니다."""
  snapshots: List[SnapshotItem] = Field(..., description="자산 상태 스냅샷 목록")
