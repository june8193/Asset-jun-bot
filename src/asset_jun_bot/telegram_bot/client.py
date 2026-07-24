# -*- coding: utf-8 -*-
"""텔레그램 HTTP REST API 전송/수정 및 API 클라이언트 모듈입니다."""

import logging
import httpx
from .formatter import markdown_to_html, remove_markdown_markup

logger = logging.getLogger(__name__)


class TelegramClient:
  """Telegram Bot REST API 송수신을 담당하는 클라이언트 클래스입니다."""

  def __init__(self, base_url: str):
    """TelegramClient 인스턴스를 초기화합니다.

    Args:
        base_url: Telegram API base URL (예: https://api.telegram.org/bot<TOKEN>)
    """
    self.base_url = base_url

  async def send_message(self, chat_id: int, text: str) -> int | None:
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

  async def edit_message(self, chat_id: int, message_id: int, text: str) -> None:
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

  async def send_chat_action(self, chat_id: int, action: str = "typing") -> None:
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
