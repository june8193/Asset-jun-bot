# -*- coding: utf-8 -*-
"""개별 종목 주가 데이터를 조회하여 출력하는 CLI 스크립트입니다."""

import asyncio
import sys
import argparse
from asset_jun_bot.asset_client import get_stock_prices, AssetClientError


async def main_async():
  parser = argparse.ArgumentParser(description="Query stock historical and current prices.")
  parser.add_argument(
      "--ticker",
      required=True,
      help="Stock code or ticker (e.g., 005930, AAPL)",
  )
  parser.add_argument(
      "--start-date",
      required=True,
      help="Start date for price history (YYYY-MM-DD)",
  )
  parser.add_argument(
      "--end-date",
      default=None,
      help="End date for price history (YYYY-MM-DD), defaults to today",
  )

  args = parser.parse_args()

  try:
    res = await get_stock_prices(
        ticker=args.ticker,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print(f"[{res.name} ({res.ticker}) {res.market} 주가 정보]")
    if not res.prices:
      print("해당 기간의 데이터가 존재하지 않습니다.")
      return
    for item in res.prices:
      print(f"DATE: {item.date} | CLOSE_PRICE: {item.close_price}")
  except AssetClientError as err:
    print(f"API Error: {err}", file=sys.stderr)
    sys.exit(1)
  except Exception as err:
    print(f"Unexpected Error: {err}", file=sys.stderr)
    sys.exit(1)


def main():
  asyncio.run(main_async())


if __name__ == "__main__":
  main()
