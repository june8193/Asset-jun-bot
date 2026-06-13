# -*- coding: utf-8 -*-
"""AI-bot 진입점(Entry Point) 모듈입니다."""

import asyncio
import logging
import os
import sys
from src.config import Config
from src.agent_runner import AgentRunner
from src.telegram_bot import TelegramBot

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


async def async_main():
  """비동기 메인 실행 루프입니다."""
  logger.info("AI-bot 구동을 시작합니다...")

  try:
    # 1. 설정 로드
    config = Config.load()
    logger.info("설정이 성공적으로 로드되었습니다.")
    logger.info(f"AssetManager API URL: {config.asset_manager_api_url}")
    logger.info(f"허가된 사용자 ID 목록: {config.telegram_allowed_user_ids}")
  except ValueError as err:
    logger.critical(f"설정 로드 실패: {err}")
    sys.exit(1)

  # 2. Gemini API Key 환경변수 확인
  gemini_key = os.getenv("GEMINI_API_KEY")
  if not gemini_key:
    logger.warning("GEMINI_API_KEY 환경변수가 설정되지 않았습니다. Antigravity SDK가 실행 시 오류를 뱉을 수 있습니다.")

  # 3. 인스턴스 생성
  agent_runner = AgentRunner()
  bot = TelegramBot(config=config, agent_runner=agent_runner)

  # 4. 폴링 루프 실행
  try:
    await bot.start_polling()
  except asyncio.CancelledError:
    logger.info("폴링 작업이 취소되었습니다.")
  except Exception as exc:
    logger.exception(f"봇 실행 중 예기치 못한 치명적 오류 발생: {exc}")


def main():
  """동기 진입점 함수입니다."""
  try:
    asyncio.run(async_main())
  except KeyboardInterrupt:
    logger.info("사용자에 의해 종료 신호(KeyboardInterrupt)를 수신했습니다. 안전하게 종료합니다.")
    sys.exit(0)


if __name__ == "__main__":
  main()
