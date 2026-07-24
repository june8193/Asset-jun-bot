# -*- coding: utf-8 -*-
"""장 마감 시각 거래내역 자동 동기화 백그라운드 스케줄러 모듈입니다."""

import asyncio
import datetime
import logging
from typing import TYPE_CHECKING

from ..asset_client import sync_kiwoom_transactions
from .commands import format_sync_result_message

if TYPE_CHECKING:
  from .client import TelegramClient
  from ..config import Config

logger = logging.getLogger(__name__)


class TelegramScheduler:
  """18:10(국내장 마감) 및 07:10(미국장 마감)에 자동으로 동기화를 실행하는 백그라운드 스케줄러입니다."""

  def __init__(self, client: "TelegramClient", config: "Config"):
    """TelegramScheduler 인스턴스를 생성합니다."""
    self.client = client
    self.config = config

  async def run_scheduler_loop(self) -> None:
    """자동 동기화 백그라운드 루프를 실행합니다."""
    logger.info("거래내역 자동 동기화 백그라운드 스케줄러 시작")
    last_domestic_date = None
    last_overseas_date = None

    while True:
      try:
        now = datetime.datetime.now()
        # 평일 여부 (0: 월, 1: 화, 2: 수, 3: 목, 4: 금, 5: 토, 6: 일)
        weekday = now.weekday()

        # 1. 국내 장마감 동기화 (평일 18:10)
        if weekday in [0, 1, 2, 3, 4] and now.hour == 18 and now.minute == 10:
          today_date = now.date()
          if last_domestic_date != today_date:
            last_domestic_date = today_date
            logger.info("국내 장 마감 자동 동기화 트리거")
            await self._execute_auto_sync()

        # 2. 미국 장마감 동기화 (화~토 07:10)
        if weekday in [1, 2, 3, 4, 5] and now.hour == 7 and now.minute == 10:
          today_date = now.date()
          if last_overseas_date != today_date:
            last_overseas_date = today_date
            logger.info("미국 장 마감 자동 동기화 트리거")
            await self._execute_auto_sync()

      except asyncio.CancelledError:
        logger.info("자동 동기화 스케줄러 루프 취소됨.")
        break
      except Exception as exc:
        logger.error(f"스케줄러 루프 오류 발생: {exc}")

      # 30초마다 체크
      await asyncio.sleep(30)

  async def _execute_auto_sync(self) -> None:
    """자동 동기화를 실행하고 등록된 모든 사용자에게 알림을 발송합니다."""
    try:
      # 당일 하루치 동기화
      result = await sync_kiwoom_transactions(days=1)
      msg = format_sync_result_message(result)

      # 등록된 모든 허가 사용자에게 알림 발송
      for tid in self.config.telegram_allowed_user_ids:
        await self.client.send_message(tid, msg)
    except Exception as exc:
      logger.exception(f"자동 동기화 실행 실패: {exc}")
      for tid in self.config.telegram_allowed_user_ids:
        await self.client.send_message(
            tid, f"⚠️ 거래내역 자동 동기화 실행 중 오류가 발생했습니다: {exc}"
        )
