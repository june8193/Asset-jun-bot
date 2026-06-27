# -*- coding: utf-8 -*-
"""AssetManager API 실제 연동 통합 테스트 모듈입니다."""

import pytest
from asset_jun_bot.asset_client import (
    get_asset_ratios,
    get_yearly_stats,
    get_daily_stats,
    get_snapshots,
    get_transactions,
    AssetRatiosResponse,
    YearlyStatsResponse,
    DailyStatsResponse,
    SnapshotsResponse,
    TransactionsResponse,
    AssetClientError,
)


@pytest.mark.asyncio
async def test_get_asset_ratios_integration():
  """실제 가동 중인 AssetManager API 서버로부터 자산 비중 데이터를 받아 검증합니다."""
  try:
    result = await get_asset_ratios()
  except AssetClientError as exc:
    pytest.fail(f"AssetManager API 실제 연동 실패: {exc}")

  assert isinstance(result, AssetRatiosResponse)
  # 응답 필드 타입 검증
  assert isinstance(result.total_valuation, float)
  assert isinstance(result.total_target, float)
  assert isinstance(result.additional_cash, float)
  assert isinstance(result.major_results, list)
  assert isinstance(result.sub_results, list)

  # 데이터가 존재하는 경우 세부 필드 검증
  for item in result.major_results:
    assert isinstance(item.category, str)
    assert isinstance(item.current_amt, float)
    assert isinstance(item.current_ratio, float)
    assert isinstance(item.target_percentage, float)
    assert isinstance(item.target_amt, float)
    assert isinstance(item.diff_amt, float)

  for item in result.sub_results:
    assert isinstance(item.category, str)
    assert item.parent_category is None or isinstance(item.parent_category, str)
    assert isinstance(item.current_amt, float)
    assert isinstance(item.current_ratio, float)
    assert isinstance(item.target_percentage, float)
    assert isinstance(item.target_amt, float)
    assert isinstance(item.diff_amt, float)


@pytest.mark.asyncio
async def test_get_yearly_stats_integration():
  """실제 가동 중인 AssetManager API 서버로부터 연간 자산 통계 데이터를 받아 검증합니다."""
  try:
    result = await get_yearly_stats()
  except AssetClientError as exc:
    pytest.fail(f"AssetManager API 연간 자산 통계 실제 연동 실패: {exc}")

  assert isinstance(result, YearlyStatsResponse)
  assert isinstance(result.stats, list)
  for item in result.stats:
    assert isinstance(item.year, int)
    assert isinstance(item.contribution, float)
    assert isinstance(item.profit, float)
    assert isinstance(item.roi, float)
    assert isinstance(item.assets, float)
    assert isinstance(item.increase, float)


@pytest.mark.asyncio
async def test_get_daily_stats_integration():
  """실제 가동 중인 AssetManager API 서버로부터 일자별 자산 통계 데이터를 받아 검증합니다."""
  try:
    result = await get_daily_stats()
  except AssetClientError as exc:
    pytest.fail(f"AssetManager API 일간 자산 통계 실제 연동 실패: {exc}")

  assert isinstance(result, DailyStatsResponse)
  assert isinstance(result.stats, list)
  for item in result.stats:
    assert isinstance(item.date, str)
    assert isinstance(item.contribution, float)
    assert isinstance(item.profit, float)
    assert isinstance(item.roi, float)
    assert isinstance(item.assets, float)
    assert isinstance(item.increase, float)


@pytest.mark.asyncio
async def test_get_snapshots_integration():
  """실제 가동 중인 AssetManager API 서버로부터 자산 스냅샷 데이터를 받아 검증합니다."""
  try:
    result = await get_snapshots()
  except AssetClientError as exc:
    pytest.fail(f"AssetManager API 스냅샷 실제 연동 실패: {exc}")

  assert isinstance(result, SnapshotsResponse)
  assert isinstance(result.snapshots, list)
  for item in result.snapshots:
    assert isinstance(item.id, int)
    assert isinstance(item.account_id, int)
    assert isinstance(item.snapshot_date, str)
    assert isinstance(item.period_deposit, float)
    assert isinstance(item.total_valuation, float)
    assert isinstance(item.total_profit, float)


@pytest.mark.asyncio
async def test_get_transactions_integration():
  """실제 가동 중인 AssetManager API 서버로부터 거래 내역 데이터를 받아 검증합니다."""
  try:
    result = await get_transactions()
  except AssetClientError as exc:
    pytest.fail(f"AssetManager API 거래 내역 실제 연동 실패: {exc}")

  assert isinstance(result, TransactionsResponse)
  assert isinstance(result.transactions, list)
  for item in result.transactions:
    assert isinstance(item.id, (int, type(None)))
    assert isinstance(item.account_id, int)
    assert isinstance(item.asset_id, int)
    assert isinstance(item.transaction_date, str)
    assert isinstance(item.type, str)
    assert isinstance(item.quantity, float)
    assert isinstance(item.price, float)
    assert isinstance(item.total_amount, float)
    assert isinstance(item.currency, str)
    assert item.exchange_rate is None or isinstance(item.exchange_rate, float)
    assert item.memo is None or isinstance(item.memo, str)
    assert item.asset_name is None or isinstance(item.asset_name, str)
    assert item.asset_ticker is None or isinstance(item.asset_ticker, str)
