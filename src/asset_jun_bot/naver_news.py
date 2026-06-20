# -*- coding: utf-8 -*-
"""네이버 뉴스 검색 API와 연동하여 뉴스를 수집하고 가공하는 모듈입니다."""

import re
import html
from typing import List, Dict, Any
import httpx
from email.utils import parsedate_to_datetime
from .config import Config
from .asset_client import AssetClientError


def clean_html_text(text: str) -> str:
  """HTML 태그(예: <b>)를 제거하고 특수 HTML 엔티티를 문자로 복원합니다.

  Args:
      text: 원본 문자열

  Returns:
      정제된 순수 텍스트 문자열
  """
  if not text:
    return ""
  # HTML 태그 제거
  clean = re.sub(r"<[^>]*>", "", text)
  # HTML 엔티티(&quot;, &lt;, &gt;, &amp; 등) 복원
  clean = html.unescape(clean)
  return clean


def _match_pub_date(pub_date_str: str, target_date_str: str) -> bool:
  """뉴스 발행일(RFC 822)이 지정한 특정 날짜(YYYY-MM-DD)와 일치하는지 비교합니다.

  Args:
      pub_date_str: RFC 822 형식의 뉴스 발행 일시 (예: "Fri, 19 Jun 2026 15:30:00 +0900")
      target_date_str: 비교 대상 날짜 문자열 (YYYY-MM-DD)

  Returns:
      날짜가 일치하면 True, 그렇지 않거나 에러 발생 시 False
  """
  if not pub_date_str or not target_date_str:
    return True
  try:
    dt = parsedate_to_datetime(pub_date_str)
    extracted_date = dt.strftime("%Y-%m-%d")
    return extracted_date == target_date_str
  except Exception:
    return False


async def search_naver_news(
    query: str,
    display: int = 10,
    sort: str = "date",
    target_date: str = None
) -> List[Dict[str, Any]]:
  """네이버 뉴스 검색 API를 호출하고 가공한 뉴스 목록을 반환합니다.

  Args:
      query: 검색 키워드
      display: 가져올 최대 기사 개수
      sort: 정렬 방식 (date, sim)
      target_date: 특정 날짜 필터 (YYYY-MM-DD, 생략 시 필터 없음)

  Returns:
      정제된 뉴스 항목 리스트. 각 항목은 title, link, description, pubDate 키를 포함합니다.

  Raises:
      AssetClientError: 설정 로드 실패, HTTP 호출 실패 또는 네트워크 오류 발생 시
  """
  try:
    config = Config.load()
  except ValueError as err:
    raise AssetClientError(f"설정 로드 중 오류 발생: {err}") from err

  url = "https://openapi.naver.com/v1/search/news.json"
  headers = {
      "X-Naver-Client-Id": config.naver_client_id,
      "X-Naver-Client-Secret": config.naver_client_secret,
  }
  
  # 날짜 필터가 지정된 경우 필터링 후에도 충분한 개수를 보장하기 위해
  # API 요청 display 개수를 늘립니다.
  api_display = display
  if target_date:
    api_display = min(100, max(50, display * 3))

  params = {
      "query": query,
      "display": api_display,
      "sort": sort,
  }

  try:
    async with httpx.AsyncClient(timeout=10.0) as client:
      response = await client.get(url, headers=headers, params=params)
      response.raise_for_status()
      data = response.json()
      
      items = data.get("items", [])
      results = []
      
      for item in items:
        pub_date_str = item.get("pubDate", "")
        
        # 1. 날짜 필터 적용
        if target_date and not _match_pub_date(pub_date_str, target_date):
          continue
        
        results.append({
            "title": clean_html_text(item.get("title", "")),
            "link": item.get("link", ""),
            "originallink": item.get("originallink", ""),
            "description": clean_html_text(item.get("description", "")),
            "pubDate": pub_date_str
        })
        
        # 원하는 display 개수를 모두 채우면 조기 종료
        if len(results) >= display:
          break
          
      return results

  except httpx.HTTPStatusError as exc:
    raise AssetClientError(
        f"네이버 뉴스 API 호출 실패 (HTTP 오류 코드: {exc.response.status_code})"
    ) from exc
  except httpx.RequestError as exc:
    raise AssetClientError(
        f"네이버 뉴스 API 서버 연결 네트워크 오류: {exc}"
    ) from exc
  except Exception as exc:
    raise AssetClientError(f"네이버 뉴스 조회 중 알 수 없는 오류 발생: {exc}") from exc
