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
    PortfolioStatusResponse,
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
  mock_response = AssetRatiosResponse(
      total_valuation=100000000.0,
      total_target=100000000.0,
      additional_cash=0.0,
      major_results=[],
      sub_results=[]
  )

  with patch("scripts.query_asset.get_asset_ratios", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_asset.py", "--action", "ratios"]):
      main()

    captured = capsys.readouterr()
    assert '"major_results"' in captured.out
    assert '"total_valuation": 100000000.0' in captured.out



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


def test_query_asset_portfolio_success(capsys):
  """--action portfolio가 주어졌을 때 포트폴리오 자산 정보가 JSON으로 정상 출력되는지 테스트합니다."""
  mock_response = PortfolioStatusResponse(
      total_valuation_krw=150000000.0,
      cash_balances={"KRW": 10000000.0, "USD": 5000.0},
      exchange_rate=1350.0,
      holdings=[]
  )

  with patch("scripts.query_asset.get_portfolio_status", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_asset.py", "--action", "portfolio"]):
      main()

    captured = capsys.readouterr()
    assert '"total_valuation_krw": 150000000.0' in captured.out
    assert '"cash_balances"' in captured.out
    assert '"holdings"' in captured.out


def test_query_asset_portfolio_with_date_success(capsys):
  """--action portfolio와 --date가 주어졌을 때 해당 날짜의 포트폴리오 정보가 정상 출력되는지 테스트합니다."""
  mock_response = PortfolioStatusResponse(
      total_valuation_krw=140000000.0,
      cash_balances={"KRW": 9000000.0, "USD": 4500.0},
      exchange_rate=1340.0,
      holdings=[]
  )

  with patch("scripts.query_asset.get_portfolio_status", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_asset.py", "--action", "portfolio", "--date", "2026-06-01"]):
      main()

    mock_get.assert_called_once_with(date="2026-06-01")
    captured = capsys.readouterr()
    assert '"total_valuation_krw": 140000000.0' in captured.out

