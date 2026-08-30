# -*- coding: utf-8 -*-
"""Telegram 봇의 롱 폴링 루프 및 메시지 처리를 담당하는 모듈입니다."""

import asyncio
import logging
import os
import sys
import httpx
from ..config import Config
from .client import TelegramClient
from .commands import CLICommandHandler, format_sync_result_message
from .scheduler import TelegramScheduler
from .formatter import markdown_to_html, remove_markdown_markup

logger = logging.getLogger(__name__)


class TelegramBot:
  """Telegram 봇의 폴링 및 사용자 요청 핸들러입니다."""

  def __init__(
      self,
      config: Config,
  ):
    """TelegramBot 인스턴스를 생성합니다.

    Args:
        config: 로드 완료된 설정 객체
    """
    self.config = config
    self.base_url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}"
    self.client = TelegramClient(base_url=self.base_url)
    self.command_handler = CLICommandHandler(
        client=self.client, config=self.config, bot=self
    )
    self.scheduler = TelegramScheduler(client=self.client, config=self.config)

  async def poll_once(self, offset: int | None = None) -> int | None:
    """Telegram 서버로부터 업데이트를 1회 수신(롱 폴링)하여 처리합니다.

    Args:
        offset: 가져올 업데이트의 시작 ID

    Returns:
        다음 폴링에서 사용할 갱신된 offset 값
    """
    url = f"{self.base_url}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset is not None:
      params["offset"] = offset

    try:
      async with httpx.AsyncClient(timeout=35.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
      logger.error(f"Telegram getUpdates 호출 실패: {exc}")
      # 네트워크 에러 시 원래 offset을 리턴하여 다시 시도하도록 함
      return offset

    if not data.get("ok"):
      logger.error(f"Telegram getUpdates 응답 오류: {data}")
      return offset

    updates = data.get("result", [])
    next_offset = offset

    for update in updates:
      update_id = update["update_id"]
      next_offset = update_id + 1

      message = update.get("message")
      if not message:
        continue

      chat = message.get("chat", {})
      chat_id = chat.get("id")
      text = message.get("text")

      if chat_id is None:
        continue

      # 보안 가드: 허가된 사용자 ID 인지 확인
      if chat_id not in self.config.telegram_allowed_user_ids:
        logger.warning(f"비인가 사용자의 접근 차단: Chat ID {chat_id}")
        await self.client.send_message(
            chat_id, "⚠️ 접근 권한이 없습니다. 등록되지 않은 Telegram ID입니다."
        )
        continue

      # 인가된 사용자의 텍스트 메시지 처리
      if text:
        logger.info(f"사용자 요청 수신 (Chat ID: {chat_id}): {text}")

        # CLI 명령어 분기
        if text.startswith("/"):
          await self.process_cli_command(chat_id, text)
          continue

        # 일반 텍스트 입력 시 안내 메시지 전송
        notice_text = (
            "💡 자연어 대화 기능은 종료되었습니다.\n"
            "사용 가능한 CLI 명령어를 확인하려면 `/help`를 입력하거나, Antigravity 원격 제어를 사용해 주세요."
        )
        await self.client.send_message(chat_id, notice_text)

    return next_offset

  async def _send_message(self, chat_id: int, text: str) -> int | None:
    """사용자에게 Telegram 메시지를 전송합니다 (Client 위임)."""
    return await self.client.send_message(chat_id, text)

  async def _edit_message(self, chat_id: int, message_id: int, text: str) -> None:
    """사용자에게 보낸 기존 Telegram 메시지를 수정합니다 (Client 위임)."""
    await self.client.edit_message(chat_id, message_id, text)

  async def _send_chat_action(self, chat_id: int, action: str = "typing") -> None:
    """사용자에게 Telegram Chat Action을 전송합니다 (Client 위임)."""
    await self.client.send_chat_action(chat_id, action)

  def exit_system(self) -> None:
    """시스템을 정상 종료합니다."""
    logger.info("시스템을 종료합니다 (exit 0)...")
    sys.exit(0)

  async def check_restart_flag(self) -> None:
    """스토리지 내 재시작 대기 플래그가 발견되면 알림을 전송하고 삭제합니다."""
    flag_file = os.path.join(self.config.storage_dir, ".restart_pending")
    if os.path.exists(flag_file):
      logger.info("재시작 플래그 파일 감지: 완료 메시지를 발송하고 파일을 삭제합니다.")
      try:
        os.remove(flag_file)
      except Exception as exc:
        logger.error(f"재시작 플래그 파일 삭제 실패: {exc}")

      # 봇 시작 단계에서 등록된 모든 허가 사용자에게 발송
      for tid in self.config.telegram_allowed_user_ids:
        await self.client.send_message(tid, "🔄 asset-jun-bot 서버 재시작이 완료되었습니다.")

  async def process_cli_command(self, chat_id: int, text: str) -> None:
    """AI 개입 없이 즉각 처리하는 CLI 명령어를 수행합니다 (Command 핸들러 위임)."""
    await self.command_handler.process_cli_command(chat_id, text)

  async def start_polling(
      self, stop_event: asyncio.Event | None = None
  ) -> None:
    """Telegram getUpdates 롱 폴링 루프를 시작합니다.

    Args:
        stop_event: 폴링을 중단하기 위한 asyncio.Event 객체 (옵션)
    """
    # 재시작 플래그 검사 루틴 수행
    await self.check_restart_flag()

    logger.info("Telegram 롱 폴링 루프를 실행합니다.")
    offset = None

    # 자동 동기화 백그라운드 스케줄러 태스크 구동
    scheduler_task = asyncio.create_task(self._run_scheduler_loop())

    try:
      while stop_event is None or not stop_event.is_set():
        try:
          offset = await self.poll_once(offset)
        except Exception as exc:
          logger.error(f"폴링 처리 중 예외 발생: {exc}")
          # 오류 발생 시 루프 폭주를 막기 위해 3초 대기
          await asyncio.sleep(3.0)

        # CPU 점유 방지를 위한 최소한의 컨텍스트 스위칭 대기
        await asyncio.sleep(0.1)
    finally:
      logger.info("폴링 루프 종료: 스케줄러를 정지합니다.")
      scheduler_task.cancel()
      try:
        await scheduler_task
      except asyncio.CancelledError:
        pass

  async def _run_scheduler_loop(self) -> None:
    """18:10(국내장 마감) 및 07:10(미국장 마감)에 자동으로 동기화를 실행하는 백그라운드 루프입니다 (Scheduler 위임)."""
    await self.scheduler.run_scheduler_loop()

  async def _execute_auto_sync(self) -> None:
    """자동 동기화를 실행하고 등록된 모든 사용자에게 알림을 발송합니다 (Scheduler 위임)."""
    await self.scheduler._execute_auto_sync()

  def _format_sync_result_message(self, result: dict) -> str:
    """동기화 결과를 텔레그램 마크다운 포맷으로 가공합니다."""
    return format_sync_result_message(result)
