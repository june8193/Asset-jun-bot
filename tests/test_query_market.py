# -*- coding: utf-8 -*-
"""scripts/query_market.py 스크립트의 단위 테스트 모듈입니다."""

import os
import sys
import pytest
from unittest.mock import patch, AsyncMock
from pydantic import BaseModel

# scripts 폴더를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.query_market import main
from asset_jun_bot.asset_client import MarketHistoryItem


def test_query_market_history_success(capsys):
  """--action history가 주어졌을 때 지수 변동 분석 결과 및 변동률이 올바르게 계산되어 출력되는지 테스트합니다."""
  mock_response = {
      "^KS11": [
          MarketHistoryItem(date="2026-06-22", close_price=2700.0),
          MarketHistoryItem(date="2026-06-23", close_price=2710.0),
          MarketHistoryItem(date="2026-06-26", close_price=2750.0),
      ]
  }

  with patch("scripts.query_market.get_market_history", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_market.py", "--action", "history", "--tickers", "^KS11"]):
      main()

    captured = capsys.readouterr()
    # 기존 가격 정보 출력 검증
    assert "[^KS11 지수 역사적 가격 정보]" in captured.out
    assert "DATE: 2026-06-22 | CLOSE_PRICE: 2700.0" in captured.out
    assert "DATE: 2026-06-26 | CLOSE_PRICE: 2750.0" in captured.out

    # 신규 지수 변동 분석 출력 검증 (TDD Red 지점)
    assert "[^KS11 지수 변동 분석]" in captured.out
    assert "START: 2026-06-22 (2700.0)" in captured.out
    assert "END: 2026-06-26 (2750.0)" in captured.out
    assert "CHANGE: +50.00 (+1.85%)" in captured.out


def test_query_market_history_single_data(capsys):
  """조회 데이터가 1개만 있을 때 변동률 분석 출력을 생략하거나 0.00%로 올바르게 예외 처리하는지 테스트합니다."""
  mock_response = {
      "^KS11": [
          MarketHistoryItem(date="2026-06-22", close_price=2700.0),
      ]
  }

  with patch("scripts.query_market.get_market_history", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_market.py", "--action", "history", "--tickers", "^KS11"]):
      main()

    captured = capsys.readouterr()
    assert "[^KS11 지수 역사적 가격 정보]" in captured.out
    # 데이터가 1개인 경우 변동률 계산을 수행하지 않거나 0.00% 보합 처리
    assert "CHANGE: 0.00 (0.00%)" in captured.out or "[^KS11 지수 변동 분석]" not in captured.out


def test_query_market_history_empty_data(capsys):
  """데이터가 아예 존재하지 않는 경우 변동 분석을 출력하지 않는지 테스트합니다."""
  mock_response = {
      "^KS11": []
  }

  with patch("scripts.query_market.get_market_history", new_callable=AsyncMock) as mock_get:
    mock_get.return_value = mock_response

    with patch("sys.argv", ["query_market.py", "--action", "history", "--tickers", "^KS11"]):
      main()

    captured = capsys.readouterr()
    assert "해당 기간의 데이터가 존재하지 않습니다." in captured.out
    assert "[^KS11 지수 변동 분석]" not in captured.out
