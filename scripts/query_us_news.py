# -*- coding: utf-8 -*-
"""yfinance를 사용하여 미국 시장 뉴스를 수집하고 마크다운 형태로 출력하는 CLI 스크립트입니다."""

import sys
import argparse
import yfinance as yf


def main():
  parser = argparse.ArgumentParser(
      description="Query Yahoo Finance news for US market and output formatted Markdown."
  )
  parser.add_argument(
      "--limit", "-l", type=int, default=5, help="Maximum number of news items to return"
  )

  args = parser.parse_args()

  try:
    ticker = yf.Ticker("^GSPC")
    news_list = ticker.news
    if not news_list:
      print("No news found for US market (^GSPC).")
      return

    for item in news_list[:args.limit]:
      title = item.get("title", "")
      link = item.get("link", "")
      publisher = item.get("publisher", "Yahoo Finance")
      print(f"- [{title}]({link}) ({publisher})")

  except Exception as err:
    print(f"Error querying US news from yfinance: {err}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
