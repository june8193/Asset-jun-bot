# -*- coding: utf-8 -*-
"""리다이렉트 URL을 추적하여 최종 원본 상세 URL을 반환하는 CLI 스크립트입니다."""

import asyncio
import sys
from asset_jun_bot.asset_client import resolve_redirect_url


async def main():
  if len(sys.argv) < 2:
    print("사용법: uv run python scripts/resolve_url.py <URL>")
    sys.exit(1)

  url = sys.argv[1]
  final_url = await resolve_redirect_url(url)
  print(final_url)


if __name__ == "__main__":
  asyncio.run(main())
