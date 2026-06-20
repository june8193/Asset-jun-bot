# -*- coding: utf-8 -*-
"""scripts/query_news.py 에 대한 테스트 모듈입니다."""

import os
import sys
import pytest
from unittest.mock import AsyncMock, patch

# scripts 폴더를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.query_news import main


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
  """네이버 API 환경 변수 설정을 주입합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://mock-asset-server")
  monkeypatch.setenv("STORAGE_DIR", "mock_storage_dir")
  monkeypatch.setenv("MODEL_ROUTER", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_GENERAL_CONVERSATION", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_ASSET_INQUIRY", "gemini-1.5-flash")
  monkeypatch.setenv("NAVER_API_CLIENT_ID", "mock_naver_id")
  monkeypatch.setenv("NAVER_API_CLIENT_SECRET", "mock_naver_secret")


@pytest.mark.asyncio
@patch("scripts.query_news.search_naver_news")
async def test_query_news_cli_success(mock_search, capsys):
  """CLI 스크립트가 인자를 받아 마크다운 포맷으로 뉴스 검색 결과를 표준출력에 잘 보여주는지 테스트합니다."""
  # Mock API 응답 설정
  mock_search.return_value = [
      {
          "title": "뉴스 제목 1",
          "link": "https://news.naver.com/1",
          "originallink": "http://original.1",
          "description": "뉴스 요약 1",
          "pubDate": "Fri, 19 Jun 2026 15:30:00 +0900"
      }
  ]

  # sys.argv 모킹
  test_args = ["query_news.py", "--query", "코스피", "--date", "2026-06-19", "--display", "5"]
  with patch.object(sys, "argv", test_args):
    await main()

  # 표준 출력 캡처 및 검증
  captured = capsys.readouterr()
  assert "- [뉴스 제목 1](https://news.naver.com/1): 뉴스 요약 1" in captured.out
  mock_search.assert_called_once_with(
      query="코스피",
      display=5,
      sort="date",
      target_date="2026-06-19"
  )
