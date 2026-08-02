# -*- coding: utf-8 -*-
"""자산, 포트폴리오, 거래 및 통계 관련 API 함수 모듈입니다 (AssetApiClient 위임)."""

from .client import get_default_client
from .models import (
    AssetSummaryResponse,
    AssetRatiosResponse,
    AssetRatioItem,
    PortfolioStatusResponse,
    PortfolioHoldingItem,
    YearlyStatsResponse,
    YearlyStatItem,
    DailyStatsResponse,
    DailyStatItem,
    SnapshotsResponse,
    SnapshotItem,
    TransactionsResponse,
    TransactionItem,
)


async def get_asset_summary() -> AssetSummaryResponse:
  """AssetManager API로부터 자산 요약 정보를 조회하여 Pydantic 모델로 반환합니다."""
  client = get_default_client()
  data = await client.get_json("/api/dashboard/summary")

  total_asset = data.get("total_valuation_krw", 0.0)
  total_contribution = data.get("total_contribution", 0.0)
  initial_base = data.get("initial_base_asset", 0.0)
  total_principal = initial_base + total_contribution
  total_profit = data.get("total_profit", 0.0)
  roi = data.get("cumulative_roi", 0.0)
  contribution_ratio = data.get("contribution_ratio", 100.0)
  profit_ratio = data.get("profit_ratio", 0.0)
  exchange_rate = data.get("exchange_rate", {})
  latest_price_date = data.get("latest_price_date", "최근 데이터 없음")

  return AssetSummaryResponse(
      total_valuation_krw=total_asset,
      total_principal=total_principal,
      total_profit=total_profit,
      cumulative_roi=roi,
      contribution_ratio=contribution_ratio,
      profit_ratio=profit_ratio,
      exchange_rate=exchange_rate,
      latest_price_date=latest_price_date,
  )


async def get_asset_ratios() -> AssetRatiosResponse:
  """AssetManager API로부터 자산군별 백분율 비중 및 리밸런싱 정보를 조회하여 Pydantic 모델로 반환합니다."""
  client = get_default_client()
  data = await client.get_json("/api/ratios/rebalancing")

  major_results = [
      AssetRatioItem(
          category=item.get("category", "미분류"),
          parent_category=None,
          current_amt=item.get("current_amt", 0.0),
          current_ratio=item.get("current_ratio", 0.0),
          target_percentage=item.get("target_percentage", 0.0),
          target_amt=item.get("target_amt", 0.0),
          diff_amt=item.get("diff_amt", 0.0),
      )
      for item in data.get("major_results", [])
  ]

  sub_results = [
      AssetRatioItem(
          category=item.get("category", "미분류"),
          parent_category=item.get("parent_category"),
          current_amt=item.get("current_amt", 0.0),
          current_ratio=item.get("current_ratio", 0.0),
          target_percentage=item.get("target_percentage", 0.0),
          target_amt=item.get("target_amt", 0.0),
          diff_amt=item.get("diff_amt", 0.0),
      )
      for item in data.get("sub_results", [])
  ]

  return AssetRatiosResponse(
      total_valuation=data.get("total_valuation", 0.0),
      total_target=data.get("total_target", 0.0),
      additional_cash=data.get("additional_cash", 0.0),
      major_results=major_results,
      sub_results=sub_results,
  )


async def get_portfolio_status(date: str | None = None) -> PortfolioStatusResponse:
  """AssetManager API로부터 전체 포트폴리오 자산 구성 및 보유 종목 현황을 조회하여 반환합니다."""
  client = get_default_client()
  params = {"date": date} if date else None

  data = await client.get_json("/api/portfolio/status", params=params)

  holdings = [
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
      for item in data.get("holdings", [])
  ]

  return PortfolioStatusResponse(
      total_valuation_krw=data.get("total_valuation_krw", 0.0),
      cash_balances=data.get("cash_balances", {}),
      exchange_rate=data.get("exchange_rate", 1.0),
      holdings=holdings,
  )


async def get_yearly_stats() -> YearlyStatsResponse:
  """AssetManager API로부터 연도별 자산 현황 통계를 조회하여 Pydantic 모델로 반환합니다."""
  client = get_default_client()
  data = await client.get_json("/api/dashboard/yearly")

  raw_stats = data.get("stats", []) if isinstance(data, dict) else data
  stats = [
      YearlyStatItem(
          year=item.get("year", 0),
          contribution=item.get("contribution", 0.0),
          profit=item.get("profit", 0.0),
          roi=item.get("roi", 0.0),
          assets=item.get("assets", 0.0),
          increase=item.get("increase", 0.0),
      )
      for item in raw_stats
  ]

  return YearlyStatsResponse(stats=stats)


async def get_daily_stats(
    start_date: str | None = None,
    end_date: str | None = None,
    all_data: bool = False,
) -> DailyStatsResponse:
  """AssetManager API로부터 일자별 자산 현황 통계를 조회하여 Pydantic 모델로 반환합니다."""
  client = get_default_client()
  params = {"all": str(all_data).lower()}
  if start_date:
    params["start_date"] = start_date
  if end_date:
    params["end_date"] = end_date

  data = await client.get_json("/api/dashboard/daily", params=params)

  raw_stats = data.get("stats", []) if isinstance(data, dict) else data
  stats = [
      DailyStatItem(
          date=item.get("date", ""),
          contribution=item.get("contribution", 0.0),
          profit=item.get("profit", 0.0),
          roi=item.get("roi", 0.0),
          assets=item.get("assets", 0.0),
          increase=item.get("increase", 0.0),
      )
      for item in raw_stats
  ]

  return DailyStatsResponse(stats=stats)


async def get_snapshots() -> SnapshotsResponse:
  """AssetManager API로부터 계좌별 스냅샷 정보를 조회하여 Pydantic 모델로 반환합니다."""
  client = get_default_client()
  data = await client.get_json("/api/db/snapshots")

  raw_snapshots = data.get("snapshots", []) if isinstance(data, dict) else data
  snapshots = [
      SnapshotItem(
          id=item.get("id", 0),
          account_id=item.get("account_id", 0),
          snapshot_date=item.get("snapshot_date", ""),
          period_deposit=item.get("period_deposit", 0.0),
          total_valuation=item.get("total_valuation", 0.0),
          total_profit=item.get("total_profit", 0.0),
      )
      for item in raw_snapshots
  ]

  return SnapshotsResponse(snapshots=snapshots)


async def get_transactions(
    start_date: str | None = None,
    end_date: str | None = None,
) -> TransactionsResponse:
  """AssetManager API로부터 거래 내역 목록을 조회하여 Pydantic 모델로 반환합니다."""
  client = get_default_client()
  params = {}
  if start_date:
    params["start_date"] = start_date
  if end_date:
    params["end_date"] = end_date

  data = await client.get_json("/api/db/transactions", params=params if params else None)

  raw_txs = data.get("transactions", []) if isinstance(data, dict) else data
  transactions = []
  for item in raw_txs:
    asset = item.get("asset") or {}
    asset_name = item.get("asset_name") or asset.get("name")
    asset_ticker = item.get("asset_ticker") or asset.get("ticker")

    transactions.append(
        TransactionItem(
            id=item.get("id"),
            account_id=item.get("account_id", 0),
            asset_id=item.get("asset_id", 0),
            transaction_date=item.get("transaction_date", ""),
            type=item.get("type", ""),
            quantity=item.get("quantity", 0.0),
            price=item.get("price", 0.0),
            total_amount=item.get("total_amount", 0.0),
            currency=item.get("currency", "KRW"),
            exchange_rate=item.get("exchange_rate"),
            memo=item.get("memo"),
            asset_name=asset_name,
            asset_ticker=asset_ticker,
            account_display_name=item.get("account_display_name"),
        )
    )

  return TransactionsResponse(transactions=transactions)


async def sync_kiwoom_transactions(days: int = 7) -> dict:
  """키움증권 거래내역 자동 동기화 앤드포인트를 호출하여 결과를 딕셔너리로 반환합니다."""
  client = get_default_client()
  params = {"days": days}
  return await client.post_json("/api/kiwoom/sync-transactions", params=params)
