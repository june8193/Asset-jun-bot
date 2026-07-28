# -*- coding: utf-8 -*-
"""장 마감 시각 거래내역 자동 동기화 및 백그라운드 태스크 모니터링 스케줄러 모듈입니다."""

import asyncio
import datetime
import logging
from typing import TYPE_CHECKING, Dict

from ..asset_client import sync_kiwoom_transactions, get_system_task_status
from .commands import format_sync_result_message

if TYPE_CHECKING:
  from .client import TelegramClient
  from ..config import Config

logger = logging.getLogger(__name__)


class TelegramScheduler:
  """18:10(국내장 마감) 및 07:10(미국장 마감) 거래내역 동기화 및 서버 백그라운드 태스크 장애 모니터링 스케줄러입니다."""

  def __init__(self, client: "TelegramClient", config: "Config"):
    """TelegramScheduler 인스턴스를 생성합니다."""
    self.client = client
    self.config = config
    # 최근 텔레그램 알림을 발송한 백엔드 태스크 에러 타임스탬프 저장 (중복 알림 방지)
    self.last_notified_errors: Dict[str, str] = {}

  async def run_scheduler_loop(self) -> None:
    """백그라운드 스케줄러 루프를 실행합니다."""
    logger.info("거래내역 자동 동기화 및 백엔드 태스크 모니터링 스케줄러 시작")
    last_domestic_date = None
    last_overseas_date = None
    check_status_counter = 0

    while True:
      try:
        now = datetime.datetime.now()
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

        # 3. 백엔드 주기적 태스크 상태 체크 (매 5분 = 30초 * 10회 주기)
        check_status_counter += 1
        if check_status_counter >= 10:
          check_status_counter = 0
          await self._check_backend_task_status()

      except asyncio.CancelledError:
        logger.info("스케줄러 루프 취소됨.")
        break
      except Exception as exc:
        logger.error(f"스케줄러 루프 오류 발생: {exc}")
        for tid in self.config.telegram_allowed_user_ids:
          try:
            await self.client.send_message(
                tid, f"⚠️ 텔레그램 봇 스케줄러 메인 루프에서 예외가 발생했습니다: {exc}"
            )
          except Exception:
            pass

      # 30초마다 체크
      await asyncio.sleep(30)

  async def _check_backend_task_status(self) -> None:
    """AssetManager 백엔드의 백그라운드 태스크 에러 발생 여부를 점검하고 알림을 전송합니다."""
    try:
      status_data = await get_system_task_status()
      if not isinstance(status_data, dict):
        return

      for task_name, task_info in status_data.items():
        if not isinstance(task_info, dict):
          continue

        status = task_info.get("status")
        last_error = task_info.get("last_error")
        error_time = task_info.get("last_error_time")

        if status == "failed" and last_error and error_time:
          # 이미 전송한 에러 타임스탬프인지 확인
          if self.last_notified_errors.get(task_name) != error_time:
            self.last_notified_errors[task_name] = error_time
            msg = (
                f"🚨 **[서버 태스크 장애 알림]**\n"
                f"• 태스크명: `{task_name}`\n"
                f"• 발생시각: `{error_time}`\n"
                f"• 오류내용: `{last_error}`"
            )
            logger.warning(f"백엔드 태스크 장애 알림 발송: {task_name} - {last_error}")
            for tid in self.config.telegram_allowed_user_ids:
              await self.client.send_message(tid, msg)
    except Exception as exc:
      logger.exception(f"백엔드 태스크 상태 점검 실패: {exc}")

  async def _execute_auto_sync(self) -> None:
    """자동 동기화를 실행하고 등록된 모든 사용자에게 알림을 발송합니다."""
    try:
      # 당일 하루치 동기화
      result = await sync_kiwoom_transactions(days=1)

      # 성공 내역 또는 미등록 내역이 있는 경우에만 메시지 발송
      success_count = result.get("success_count", 0)
      pending_count = result.get("pending_count", 0)
      if success_count == 0 and pending_count == 0:
        logger.info("새로 감지된 거래 및 미등록 자산 거래가 없어 텔레그램 메시지 발송을 생략합니다.")
        return

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
