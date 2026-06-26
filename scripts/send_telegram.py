# -*- coding: utf-8 -*-
"""텔레그램 메시지를 전송하는 CLI 스크립트입니다."""

import asyncio
import sys
from asset_jun_bot.asset_client import send_telegram_message, AssetClientError


import os


async def main():
  # Windows 환경이며, pytest 테스트 실행 환경이 아닌 경우에만 표준 출력 인코딩을 UTF-8로 강제 설정합니다.
  if sys.platform == "win32" and "pytest" not in sys.modules:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

  if len(sys.argv) < 2:
    print("사용법: uv run python scripts/send_telegram.py <메시지 내용 또는 파일 경로> [chat_id]")
    sys.exit(1)

  message_or_path = sys.argv[1]
  chat_id = None
  if len(sys.argv) >= 3:
    try:
      chat_id = int(sys.argv[2])
    except ValueError:
      print(f"오류: chat_id는 숫자여야 합니다. 입력값: {sys.argv[2]}")
      sys.exit(1)

  if os.path.isfile(message_or_path):
    try:
      with open(message_or_path, "r", encoding="utf-8") as f:
        message = f.read()
    except Exception as e:
      print(f"오류: 파일을 읽을 수 없습니다 ({message_or_path}): {e}")
      sys.exit(1)
  else:
    message = message_or_path

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
