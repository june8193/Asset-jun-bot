# -*- coding: utf-8 -*-
"""Telegram 봇의 롱 폴링 루프 및 메시지 처리를 담당하는 모듈입니다."""

import asyncio
import logging
import re
import httpx
from .config import Config
from .agent_runner import AgentRunner
from .chat_history_manager import ChatHistoryManager

logger = logging.getLogger(__name__)


class TelegramBot:
  """Telegram 봇의 폴링 및 사용자 요청 핸들러입니다."""

  def __init__(
      self,
      config: Config,
      agent_runner: AgentRunner,
      chat_history_manager: ChatHistoryManager | None = None,
  ):
    """TelegramBot 인스턴스를 생성합니다.

    Args:
        config: 로드 완료된 설정 객체
        agent_runner: AI 에이전트 실행기 객체
        chat_history_manager: 대화 내역 저장 관리 객체
    """
    self.config = config
    self.agent_runner = agent_runner
    self.chat_history_manager = chat_history_manager or ChatHistoryManager(
        storage_dir=config.storage_dir
    )
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
        # 사용자 대화 내역 저장
        await self.chat_history_manager.save_message(
            user_id=chat_id, role="user", message=text
        )

        # 1. 임시 메시지 전송 및 typing 상태 표시
        status_msg_id = await self._send_message(chat_id, "🔄 AI 답변을 준비 중입니다...")
        await self._send_chat_action(chat_id, "typing")

        last_status_text = "🔄 AI 답변을 준비 중입니다..."

        # 상태 메시지 수정을 위한 비동기 콜백 정의
        async def on_status_update(status_text: str):
          nonlocal last_status_text
          # CHAT은 초기 세션 상태이므로 메시지를 변경할 필요가 없습니다.
          if status_text == "CHAT":
            return
          # 동일한 텍스트로의 연속적인 중복 수정을 방지합니다.
          if status_text == last_status_text:
            return
          last_status_text = status_text

          if status_msg_id is not None:
            await self._edit_message(chat_id, status_msg_id, status_text)

        # AI 에이전트 호출하여 응답 생성
        reply_text = await self.agent_runner.ask(text, on_status_update=on_status_update)

        # 봇 대화 내역 저장
        await self.chat_history_manager.save_message(
            user_id=chat_id, role="bot", message=reply_text
        )

        # 3. 최종 답변으로 수정 또는 전송
        if status_msg_id is not None:
          await self._edit_message(chat_id, status_msg_id, reply_text)
        else:
          await self._send_message(chat_id, reply_text)

    return next_offset

  async def _send_message(self, chat_id: int, text: str) -> int | None:
    """사용자에게 Telegram 메시지를 전송합니다.

    1차로 마크다운을 HTML로 변환하여 parse_mode="HTML"로 전송을 시도하고,
    실패할 경우 마크다운 마크업을 제거한 일반 텍스트로 에러 정보와 함께 Fallback 재전송합니다.

    Args:
        chat_id: 텔레그램 대화방 ID
        text: 전송할 원본 마크다운 텍스트

    Returns:
        성공 시 메시지 ID (message_id: int), 실패 시 None
    """
    url = f"{self.base_url}/sendMessage"
    
    # 1차 시도: 마크다운을 HTML로 변환하여 parse_mode="HTML"로 전송
    html_text = markdown_to_html(text)
    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
    }

    try:
      async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("ok") and data.get("result"):
          return data["result"].get("message_id")
    except Exception as exc:
      logger.error(
          f"Telegram sendMessage HTML 모드 전송 실패 (Chat ID: {chat_id}): {exc}"
      )
      
      # 2차 시도 (Fallback): 1차 실패 시 일반 텍스트 모드로 재전송하여 오류 보고 및 평문 본문 전달
      plain_body = remove_markdown_markup(text)
      error_detail = str(exc)
      if isinstance(exc, httpx.HTTPStatusError):
        try:
          err_json = exc.response.json()
          error_detail = (
              f"{exc.response.status_code} "
              f"{err_json.get('description', exc.response.reason_phrase)}"
          )
        except Exception:
          error_detail = f"{exc.response.status_code} {exc.response.reason_phrase}"

      fallback_text = (
          "⚠️ 메시지 전송 중 오류가 발생했습니다.\n"
          f"원인: {error_detail}\n\n"
          "--- [전송 실패한 답변 내용] ---\n"
          f"{plain_body}"
      )
      
      fallback_payload = {
          "chat_id": chat_id,
          "text": fallback_text,
          "parse_mode": None,  # 일반 텍스트 모드로 전송하여 파싱 에러 방지
      }
      
      try:
        async with httpx.AsyncClient(timeout=10.0) as client:
          response2 = await client.post(url, json=fallback_payload)
          response2.raise_for_status()
          data2 = response2.json()
          if data2.get("ok") and data2.get("result"):
            return data2["result"].get("message_id")
        logger.info(f"Fallback 평문 메시지 재전송 성공 (Chat ID: {chat_id})")
      except Exception as fallback_exc:
        logger.critical(
            f"Fallback 평문 메시지조차 전송 실패 (Chat ID: {chat_id}): {fallback_exc}"
        )
    return None

  async def _edit_message(self, chat_id: int, message_id: int, text: str) -> None:
    """사용자에게 보낸 기존 Telegram 메시지를 수정합니다.

    1차로 마크다운을 HTML로 변환하여 parse_mode="HTML"로 수정을 시도하고,
    실패할 경우 마크다운 마크업을 제거한 일반 텍스트로 에러 정보와 함께 Fallback 재수정합니다.

    Args:
        chat_id: 텔레그램 대화방 ID
        message_id: 수정할 메시지 ID
        text: 전송할 원본 마크다운 텍스트
    """
    url = f"{self.base_url}/editMessageText"
    
    # 1차 시도: 마크다운을 HTML로 변환하여 parse_mode="HTML"로 수정
    html_text = markdown_to_html(text)
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": html_text,
        "parse_mode": "HTML",
    }

    try:
      async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    except Exception as exc:
      logger.error(
          f"Telegram editMessageText HTML 모드 수정 실패 (Chat ID: {chat_id}): {exc}"
      )
      
      # 2차 시도 (Fallback): 1차 실패 시 일반 텍스트 모드로 재수정하여 오류 보고 및 평문 본문 전달
      plain_body = remove_markdown_markup(text)
      error_detail = str(exc)
      if isinstance(exc, httpx.HTTPStatusError):
        try:
          err_json = exc.response.json()
          error_detail = (
              f"{exc.response.status_code} "
              f"{err_json.get('description', exc.response.reason_phrase)}"
          )
        except Exception:
          error_detail = f"{exc.response.status_code} {exc.response.reason_phrase}"

      fallback_text = (
          "⚠️ 메시지 수정 중 오류가 발생했습니다.\n"
          f"원인: {error_detail}\n\n"
          "--- [전송 실패한 답변 내용] ---\n"
          f"{plain_body}"
      )
      
      fallback_payload = {
          "chat_id": chat_id,
          "message_id": message_id,
          "text": fallback_text,
          "parse_mode": None,  # 일반 텍스트 모드로 수정하여 파싱 에러 방지
      }
      
      try:
        async with httpx.AsyncClient(timeout=10.0) as client:
          response2 = await client.post(url, json=fallback_payload)
          response2.raise_for_status()
        logger.info(f"Fallback 평문 메시지 재수정 성공 (Chat ID: {chat_id})")
      except Exception as fallback_exc:
        logger.critical(
            f"Fallback 평문 메시지조차 수정 실패 (Chat ID: {chat_id}): {fallback_exc}"
        )

  async def _send_chat_action(self, chat_id: int, action: str = "typing") -> None:
    """사용자에게 Telegram Chat Action(예: typing)을 전송합니다.

    Args:
        chat_id: 텔레그램 대화방 ID
        action: 전송할 액션 종류 (기본값: "typing")
    """
    url = f"{self.base_url}/sendChatAction"
    payload = {
        "chat_id": chat_id,
        "action": action,
    }
    try:
      async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
    except Exception as exc:
      logger.warning(f"Telegram sendChatAction 호출 실패 (Chat ID: {chat_id}): {exc}")

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


def markdown_to_html(text: str) -> str:
  """마크다운 텍스트를 텔레그램용 HTML 서식으로 변환합니다.

  Args:
      text: 원본 마크다운 텍스트

  Returns:
      텔레그램 HTML 규격에 맞춰 이스케이프 및 변환된 텍스트
  """
  if not text:
    return ""

  # 1. 텔레그램 필수 HTML 이스케이프 (태그 충돌 방지)
  # &를 가장 먼저 변환하여 &lt; 등의 &가 이중 변환되지 않도록 함
  text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

  # 2. 코드 블록 변환 (```code``` -> <pre>code</pre>)
  text = re.sub(r"```([\s\S]*?)```", r"<pre>\1</pre>", text)

  # 3. 인라인 코드 변환 (`code` -> <code>code</code>)
  text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)

  # 4. 강조 (Bold) 변환
  text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
  text = re.sub(r"\*([^*]+)\*", r"<b>\1</b>", text)

  # 5. 하이퍼링크 변환 ([text](url) -> <a href="url">text</a>)
  text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

  # 6. 블록 인용구 (줄 시작 > 텍스트 -> <blockquote>텍스트</blockquote>)
  # HTML 이스케이프 처리 후 '>'가 '&gt;'로 변경되었으므로 이를 매칭
  text = re.sub(
      r"^\s*&gt;\s*(.*?)$", r"<blockquote>\1</blockquote>", text, flags=re.MULTILINE
  )

  # 7. 헤더 (# 제목 -> <b>제목</b>)
  text = re.sub(r"^\s*#{1,6}\s*(.*?)$", r"<b>\1</b>", text, flags=re.MULTILINE)

  # 8. 수평선 (--- -> ━━━━━━━━━━━━━━━━━━━━)
  text = re.sub(r"^\s*---\s*$", "━━━━━━━━━━━━━━━━━━━━", text, flags=re.MULTILINE)

  return text


def remove_markdown_markup(text: str) -> str:
  """텍스트에서 마크다운 마크업 서식을 지우고 일반 텍스트로 변환합니다.

  Args:
      text: 마크다운 서식이 포함된 원본 텍스트

  Returns:
      서식 마크업이 지워진 순수 일반 텍스트
  """
  if not text:
    return ""

  # 1. 코드블록 마크업 제거
  text = text.replace("```", "")
  # 2. 인라인 코드 마크업 제거
  text = text.replace("`", "")
  # 3. 굵게/강조 마크업 제거
  text = text.replace("**", "").replace("*", "")
  # 4. 링크 마크업 단순화 ([text](url) -> text)
  text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
  # 5. 블록 인용 기호 제거
  text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
  # 6. 헤더 # 기호 제거
  text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
  # 7. 수평선 제거
  text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)

  return text
