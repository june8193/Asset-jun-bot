# -*- coding: utf-8 -*-
"""시장 휴장일 정보 및 지수 데이터를 조회하는 CLI 스크립트입니다."""

import asyncio
import sys
import argparse
from asset_jun_bot.asset_client import (
    check_market_holiday,
    get_market_indices,
    get_market_history,
    AssetClientError,
)


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


async def run_get_indices(country: str):
  try:
    res = await get_market_indices(country=country)
    for item in res.indices:
      name_normalized = item.index_name.upper().replace(" ", "_")
      print(f"INDEX_{name_normalized}_PRICE: {item.current_price}")
      print(f"INDEX_{name_normalized}_CHANGE: {item.change_rate}")
  except AssetClientError as err:
    print(f"Error getting market indices: {err}", file=sys.stderr)
    sys.exit(1)


async def run_get_history(tickers_str: str, start_date: str | None, end_date: str | None):
  try:
    tickers = [t.strip() for t in tickers_str.split(",") if t.strip()]
    if not tickers:
      print("Error: 유효한 티커를 입력해주세요.", file=sys.stderr)
      sys.exit(1)
    res = await get_market_history(tickers=tickers, start_date=start_date, end_date=end_date)
    for ticker, items in res.items():
      print(f"[{ticker} 지수 역사적 가격 정보]")
      if not items:
        print("해당 기간의 데이터가 존재하지 않습니다.")
        print()
        continue
      
      # 날짜순으로 정렬하여 신뢰도 확보
      sorted_items = sorted(items, key=lambda x: x.date)
      for item in sorted_items:
        print(f"DATE: {item.date} | CLOSE_PRICE: {item.close_price}")
      print()

      # 지수 변동 분석 수행
      print(f"[{ticker} 지수 변동 분석]")
      start_item = sorted_items[0]
      end_item = sorted_items[-1]

      if len(sorted_items) > 1:
        change_amt = end_item.close_price - start_item.close_price
        change_rate = (change_amt / start_item.close_price) * 100

        if change_rate > 0:
          rate_str = f"+{change_rate:.2f}%"
          amt_str = f"+{change_amt:.2f}"
        elif change_rate < 0:
          rate_str = f"{change_rate:.2f}%"
          amt_str = f"{change_amt:.2f}"
        else:
          rate_str = "0.00%"
          amt_str = "0.00"
      else:
        amt_str = "0.00"
        rate_str = "0.00%"

      print(f"START: {start_item.date} ({start_item.close_price:.1f}) | END: {end_item.date} ({end_item.close_price:.1f})")
      print(f"CHANGE: {amt_str} ({rate_str})")
      print()
  except AssetClientError as err:
    print(f"Error getting market history: {err}", file=sys.stderr)
    sys.exit(1)


def main():
  # Windows 환경이며, pytest 테스트 실행 환경이 아닌 경우에만 표준 출력 인코딩을 UTF-8로 강제 설정합니다.
  if sys.platform == "win32" and "pytest" not in sys.modules:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

  parser = argparse.ArgumentParser(description="Query market holiday status and indices.")
  parser.add_argument(
      "--action",
      choices=["holiday", "indices", "history"],
      required=True,
      help="Action to perform",
  )
  parser.add_argument(
      "--date",
      default="",
      help="Date for holiday check (YYYY-MM-DD), defaults to today",
  )
  parser.add_argument(
      "--country",
      default="KR",
      help="Country code for holiday check, defaults to KR",
  )
  parser.add_argument(
      "--tickers",
      default="",
      help="Comma-separated tickers for history inquiry (e.g., ^KS11,^GSPC)",
  )
  parser.add_argument(
      "--start-date",
      default=None,
      help="Start date for history inquiry (YYYY-MM-DD)",
  )
  parser.add_argument(
      "--end-date",
      default=None,
      help="End date for history inquiry (YYYY-MM-DD)",
  )

  args = parser.parse_args()

  if args.action == "holiday":
    asyncio.run(run_check_holiday(args.date, args.country))
  elif args.action == "indices":
    asyncio.run(run_get_indices(args.country))
  elif args.action == "history":
    if not args.tickers:
      print("Error: --tickers 파라미터는 history 액션에 필수적입니다.", file=sys.stderr)
      sys.exit(1)
    asyncio.run(run_get_history(args.tickers, args.start_date, args.end_date))


if __name__ == "__main__":
  main()

