# -*- coding: utf-8 -*-
"""Naver 뉴스 검색 API 연동 모듈에 대한 테스트입니다."""

import pytest
import respx
from httpx import Response, RequestError
from asset_jun_bot.naver_news import search_naver_news, clean_html_text
from asset_jun_bot.asset_client import AssetClientError


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


def test_clean_html_text():
  """HTML 태그 제거 및 특수 엔티티 변환 기능을 테스트합니다."""
  html_text = "국내 증시, <b>코스피</b> 2,700선 &quot;안착&quot; &lt;성공&gt;"
  expected = '국내 증시, 코스피 2,700선 "안착" <성공>'
  assert clean_html_text(html_text) == expected


@pytest.mark.asyncio
@respx.mock
async def test_search_naver_news_success_with_filtering():
  """네이버 뉴스 API 호출 성공 및 날짜 필터링이 올바르게 동작하는지 테스트합니다."""
  mock_response = {
      "lastBuildDate": "Fri, 19 Jun 2026 18:00:00 +0900",
      "total": 2,
      "start": 1,
      "display": 2,
      "items": [
          {
              "title": "코스피 <b>하락</b> 마감",
              "originallink": "http://yna.co.kr/news1",
              "link": "https://news.naver.com/news1",
              "description": "금일 코스피 지수는 &quot;하락&quot; 마감했습니다.",
              "pubDate": "Fri, 19 Jun 2026 15:30:00 +0900"
          },
          {
              "title": "코스닥 <b>상승</b> 마감",
              "originallink": "http://mk.co.kr/news2",
              "link": "https://news.naver.com/news2",
              "description": "코스닥 지수는 상승했습니다.",
              "pubDate": "Sat, 20 Jun 2026 10:00:00 +0900"
          }
      ]
  }

  respx.get(url__startswith="https://openapi.naver.com/v1/search/news.json").mock(
      return_value=Response(200, json=mock_response)
  )

  # 1. 날짜 필터링 미적용 시 둘 다 나와야 함
  results = await search_naver_news(query="코스피", display=10)
  assert len(results) == 2
  assert results[0]["title"] == "코스피 하락 마감"
  assert results[0]["description"] == '금일 코스피 지수는 "하락" 마감했습니다.'
  assert results[1]["title"] == "코스닥 상승 마감"

  # 2. 2026-06-19 날짜 필터링 적용 시 1개만 나와야 함
  results_filtered = await search_naver_news(query="코스피", display=10, target_date="2026-06-19")
  assert len(results_filtered) == 1
  assert results_filtered[0]["title"] == "코스피 하락 마감"


@pytest.mark.asyncio
@respx.mock
async def test_search_naver_news_http_error():
  """네이버 뉴스 API 호출 시 HTTP 에러가 날 때 AssetClientError를 반환하는지 테스트합니다."""
  respx.get(url__startswith="https://openapi.naver.com/v1/search/news.json").mock(
      return_value=Response(401)
  )

  with pytest.raises(AssetClientError) as excinfo:
    await search_naver_news(query="코스피", display=10)
  assert "네이버 뉴스 API 호출 실패" in str(excinfo.value)
