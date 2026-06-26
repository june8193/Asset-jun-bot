# -*- coding: utf-8 -*-
"""자산 데이터를 조회하여 출력하는 CLI 스크립트입니다."""

import asyncio
import sys
import argparse



from asset_jun_bot.asset_client import (
    get_asset_summary,
    get_asset_ratios,
    get_watchlist_prices,
    get_portfolio_status,
    AssetClientError,
)


async def main_async():
  parser = argparse.ArgumentParser(description="Query asset data from AssetManager API.")
  parser.add_argument(
      "--action",
      required=True,
      choices=["summary", "ratios", "watchlist", "portfolio"],
      help="Action to perform",
  )
  parser.add_argument(
      "--country",
      default="KR",
      choices=["KR", "US"],
      help="Country for watchlist inquiry",
  )
  parser.add_argument(
      "--date",
      default=None,
      help="Inquiry standard date (YYYY-MM-DD)",
  )

  args = parser.parse_args()

  try:
    if args.action == "summary":
      res = await get_asset_summary()
      print(res.model_dump_json(indent=2))
    elif args.action == "ratios":
      res = await get_asset_ratios()
      print(res.model_dump_json(indent=2))
    elif args.action == "watchlist":
      res = await get_watchlist_prices(country=args.country)
      print(res.model_dump_json(indent=2))
    elif args.action == "portfolio":
      res = await get_portfolio_status(date=args.date)
      print(res.model_dump_json(indent=2))
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
