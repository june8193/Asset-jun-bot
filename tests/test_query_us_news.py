# -*- coding: utf-8 -*-
"""scripts/query_us_news.py 스크립트의 단위 테스트 모듈입니다."""

import os
import sys
import pytest

# scripts 폴더를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unittest.mock import patch, MagicMock
from scripts.query_us_news import main


def test_query_us_news_success(capsys):
  """yfinance 뉴스 조회 성공 시 포맷팅된 마크다운을 출력하는지 테스트합니다."""
  mock_news = [
      {
          "title": "US Stocks Surge",
          "link": "https://finance.yahoo.com/news/1",
          "publisher": "Bloomberg"
      },
      {
          "title": "Fed Rate Decision",
          "link": "https://finance.yahoo.com/news/2",
          "publisher": "Reuters"
      }
  ]

  with patch("scripts.query_us_news.yf.Ticker") as mock_ticker_cls:
    mock_ticker = MagicMock()
    mock_ticker.news = mock_news
    mock_ticker_cls.return_value = mock_ticker

    with patch("sys.argv", ["query_us_news.py", "--limit", "2"]):
      main()

    captured = capsys.readouterr()
    assert "- [US Stocks Surge](https://finance.yahoo.com/news/1) (Bloomberg)" in captured.out
    assert "- [Fed Rate Decision](https://finance.yahoo.com/news/2) (Reuters)" in captured.out


def test_query_us_news_empty(capsys):
  """뉴스가 없는 경우 메세지를 출력하는지 테스트합니다."""
  with patch("scripts.query_us_news.yf.Ticker") as mock_ticker_cls:
    mock_ticker = MagicMock()
    mock_ticker.news = []
    mock_ticker_cls.return_value = mock_ticker

    with patch("sys.argv", ["query_us_news.py"]):
      main()

    captured = capsys.readouterr()
    assert "No news found for US market" in captured.out


def test_query_us_news_error(capsys):
  """예외 발생 시 sys.exit(1)을 던지고 에러 로그를 출력하는지 테스트합니다."""
  with patch("scripts.query_us_news.yf.Ticker", side_effect=Exception("Connection Error")):
    with patch("sys.argv", ["query_us_news.py"]):
      with pytest.raises(SystemExit) as exc_info:
        main()
      assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Error querying US news from yfinance: Connection Error" in captured.err
