# -*- coding: utf-8 -*-
"""네이버 뉴스 검색 API를 사용하여 특정 쿼리의 뉴스를 수집하고 마크다운 형태로 출력하는 CLI 스크립트입니다."""

import asyncio
import sys
import argparse
from asset_jun_bot.naver_news import search_naver_news
from asset_jun_bot.asset_client import AssetClientError


async def main():
  parser = argparse.ArgumentParser(
      description="Query Naver News API and output formatted Markdown."
  )
  parser.add_argument(
      "--query", "-q", required=True, help="Search keyword query"
  )
  parser.add_argument(
      "--display", "-d", type=int, default=10, help="Maximum number of items to display"
  )
  parser.add_argument(
      "--sort", "-s", choices=["date", "sim"], default="date", help="Sorting method"
  )
  parser.add_argument(
      "--date", "-t", default="", help="Specific date filter (YYYY-MM-DD), default is empty"
  )

  args = parser.parse_args()

  try:
    results = await search_naver_news(
        query=args.query,
        display=args.display,
        sort=args.sort,
        target_date=args.date if args.date else None
    )

    for item in results:
      title = item.get("title", "")
      link = item.get("link", "")
      description = item.get("description", "")
      print(f"- [{title}]({link}): {description}")

  except AssetClientError as err:
    print(f"Error querying news: {err}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  asyncio.run(main())
