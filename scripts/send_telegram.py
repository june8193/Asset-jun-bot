# -*- coding: utf-8 -*-
"""텔레그램 메시지를 전송하는 CLI 스크립트입니다."""

import asyncio
import sys
from asset_jun_bot.asset_client import send_telegram_message, AssetClientError


async def main():
  if len(sys.argv) < 2:
    print("사용법: uv run python scripts/send_telegram.py <메시지 내용> [chat_id]")
    sys.exit(1)

  message = sys.argv[1]
  chat_id = None
  if len(sys.argv) >= 3:
    try:
      chat_id = int(sys.argv[2])
    except ValueError:
      print(f"오류: chat_id는 숫자여야 합니다. 입력값: {sys.argv[2]}")
      sys.exit(1)

  try:
    result = await send_telegram_message(message, chat_id=chat_id)
    print(result)
  except AssetClientError as err:
    print(f"오류: 텔레그램 메시지 전송 실패: {err}")
    sys.exit(1)
  except Exception as exc:
    print(f"예기치 못한 오류 발생: {exc}")
    sys.exit(1)


if __name__ == "__main__":
  asyncio.run(main())
