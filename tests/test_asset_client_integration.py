# -*- coding: utf-8 -*-
"""AssetManager API 실제 연동 통합 테스트 모듈입니다."""

import pytest
from asset_jun_bot.asset_client import get_asset_ratios, AssetRatiosResponse, AssetClientError


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
