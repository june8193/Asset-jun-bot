# -*- coding: utf-8 -*-
"""Telegram 봇의 롱 폴링 루프 및 메시지 처리를 담당하는 모듈입니다."""

import asyncio
import logging
import httpx
from .config import Config
from .agent_runner import AgentRunner

logger = logging.getLogger(__name__)


class TelegramBot:
  """Telegram 봇의 폴링 및 사용자 요청 핸들러입니다."""

  def __init__(self, config: Config, agent_runner: AgentRunner):
    """TelegramBot 인스턴스를 생성합니다.

    Args:
        config: 로드 완료된 설정 객체
        agent_runner: AI 에이전트 실행기 객체
    """
    self.config = config
    self.agent_runner = agent_runner
    self.base_url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}"

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
        await self._send_message(
            chat_id, "⚠️ 접근 권한이 없습니다. 등록되지 않은 Telegram ID입니다."
        )
        continue

      # 인가된 사용자의 텍스트 메시지 처리
      if text:
        logger.info(f"사용자 요청 수신 (Chat ID: {chat_id}): {text}")
        # AI 에이전트 호출하여 응답 생성
        reply_text = await self.agent_runner.ask(text)
        # 텔레그램 답변 전송
        await self._send_message(chat_id, reply_text)

    return next_offset

  async def _send_message(self, chat_id: int, text: str) -> None:
    """사용자에게 Telegram 메시지를 전송합니다."""
    url = f"{self.base_url}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",  # 에이전트의 마크다운 서식을 텔레그램에 렌더링
    }

    try:
      async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    except Exception as exc:
      logger.error(f"Telegram sendMessage 호출 실패 (Chat ID: {chat_id}): {exc}")

  async def start_polling(
      self, stop_event: asyncio.Event | None = None
  ) -> None:
    """Telegram getUpdates 롱 폴링 루프를 시작합니다.

    Args:
        stop_event: 폴링을 중단하기 위한 asyncio.Event 객체 (옵션)
    """
    logger.info("Telegram 롱 폴링 루프를 실행합니다.")
    offset = None

    while stop_event is None or not stop_event.is_set():
      try:
        offset = await self.poll_once(offset)
      except Exception as exc:
        logger.error(f"폴링 처리 중 예외 발생: {exc}")
        # 오류 발생 시 루프 폭주를 막기 위해 3초 대기
        await asyncio.sleep(3.0)

      # CPU 점유 방지를 위한 최소한의 컨텍스트 스위칭 대기
      await asyncio.sleep(0.1)
