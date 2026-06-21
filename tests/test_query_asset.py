# -*- coding: utf-8 -*-
"""scripts/query_asset.py 스크립트의 단위 테스트 모듈입니다."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# scripts 폴더를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.query_asset import main
from asset_jun_bot.asset_client import (
    AssetSummaryResponse,
    AssetRatiosResponse,
    WatchlistPricesResponse,
    AssetClientError,
)


def test_query_asset_summary_success(capsys):
  """--action summary가 주어졌을 때 자산 요약 정보가 JSON으로 정상 출력되는지 테스트합니다."""
  mock_response = AssetSummaryResponse(
      total_valuation_krw=100000000.0,
      total_principal=80000000.0,
      total_profit=20000000.0,
      cumulative_roi=25.0,
      contribution_ratio=80.0,
      profit_ratio=20.0,
  )

  with patch("scripts.query_asset.get_asset_summary", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_asset.py", "--action", "summary"]):
      main()

    captured = capsys.readouterr()
    assert '"total_valuation_krw": 100000000.0' in captured.out
    assert '"cumulative_roi": 25.0' in captured.out


def test_query_asset_ratios_success(capsys):
  """--action ratios가 주어졌을 때 자산 비중 정보가 JSON으로 정상 출력되는지 테스트합니다."""
  mock_response = AssetRatiosResponse(major_results=[])

  with patch("scripts.query_asset.get_asset_ratios", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_asset.py", "--action", "ratios"]):
      main()

    captured = capsys.readouterr()
    assert '"major_results"' in captured.out


def test_query_asset_watchlist_success(capsys):
  """--action watchlist와 country가 주어졌을 때 시세 정보가 JSON으로 정상 출력되는지 테스트합니다."""
  mock_response = WatchlistPricesResponse(country="KR", prices=[])

  with patch("scripts.query_asset.get_watchlist_prices", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_asset.py", "--action", "watchlist", "--country", "KR"]):
      main()

    captured = capsys.readouterr()
    assert '"country": "KR"' in captured.out
    assert '"prices"' in captured.out


def test_query_asset_api_error(capsys):
  """API 에러 발생 시 exit code 1을 리턴하고 에러를 출력하는지 테스트합니다."""
  with patch("scripts.query_asset.get_asset_summary", new_callable=AsyncMock, side_effect=AssetClientError("Connection Failed")):
    with patch("sys.argv", ["query_asset.py", "--action", "summary"]):
      with pytest.raises(SystemExit) as exc_info:
        main()
      assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "API Error: Connection Failed" in captured.err
