# -*- coding: utf-8 -*-
"""시장 휴장일 정보 및 지수 데이터를 조회하는 CLI 스크립트입니다."""

import asyncio
import sys
import argparse
from asset_jun_bot.asset_client import check_market_holiday, get_market_indices, AssetClientError


async def run_check_holiday(date: str, country: str):
  try:
    res = await check_market_holiday(date_str=date, country=country)
    print(f"DATE: {res.date}")
    print(f"COUNTRY: {res.country}")
    print(f"IS_HOLIDAY: {res.is_holiday}")
    print(f"DESCRIPTION: {res.description}")
  except AssetClientError as err:
    print(f"Error checking market holiday: {err}", file=sys.stderr)
    sys.exit(1)


async def run_get_indices():
  try:
    res = await get_market_indices()
    for item in res.indices:
      print(f"INDEX_{item.index_name.upper()}_PRICE: {item.current_price}")
      print(f"INDEX_{item.index_name.upper()}_CHANGE: {item.change_rate}")
  except AssetClientError as err:
    print(f"Error getting market indices: {err}", file=sys.stderr)
    sys.exit(1)


def main():
  parser = argparse.ArgumentParser(description="Query market holiday status and indices.")
  parser.add_argument("--action", choices=["holiday", "indices"], required=True, help="Action to perform")
  parser.add_argument("--date", default="", help="Date for holiday check (YYYY-MM-DD), defaults to today")
  parser.add_argument("--country", default="KR", help="Country code for holiday check, defaults to KR")
  
  args = parser.parse_args()
  
  if args.action == "holiday":
    asyncio.run(run_check_holiday(args.date, args.country))
  elif args.action == "indices":
    asyncio.run(run_get_indices())


if __name__ == "__main__":
  main()
