# -*- coding: utf-8 -*-
"""Telegram 봇의 롱 폴링 루프 및 메시지 처리를 담당하는 모듈입니다."""

import asyncio
import logging
import re
import os
import sys
import httpx
from .config import Config
from .agent_runner import AgentRunner
from .chat_history_manager import ChatHistoryManager
from .asset_client import (
    get_asset_summary,
    get_asset_ratios,
    get_transactions,
    get_yearly_stats,
    get_daily_stats,
)
import datetime

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

        # CLI 명령어 분기 (AI 개입 없음)
        if text.startswith("/"):
          await self.process_cli_command(chat_id, text)
          continue

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

  def exit_system(self) -> None:
    """시스템을 정상 종료합니다. PM2의 autorestart 옵션과 연동하여 재기동을 발생시킵니다."""
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
        await self._send_message(tid, "🔄 asset-jun-bot 서버 재시작이 완료되었습니다.")

  async def process_cli_command(self, chat_id: int, text: str) -> None:
    """AI 개입 없이 즉각 처리하는 CLI 명령어를 수행합니다."""
    cmd = text.strip().split()[0].lower()

    if cmd == "/help":
      help_msg = (
          "💡 **asset-jun-bot 명령어 안내**\n"
          "• /help: 현재 명령어 리스트를 확인합니다.\n"
          "• /restart: 봇 서버를 완전히 재시작합니다 (MCP 서버 연동 초기화 포함).\n"
          "• /asset: 현재 통합 자산 총액 및 누적 투자 수익, 기준 정보를 조회합니다.\n"
          "• /ratio: 대분류 및 소분류 자산 비중과 목표비중 리밸런싱 현황을 조회합니다.\n"
          "• /tx 또는 /transactions [개수]: 최근 거래내역을 조회합니다. (기본 5개)\n"
          "• /yearly: 연도별 자산 통계 및 수익률을 조회합니다.\n"
          "• /daily [일수]: 스냅샷 기준 일별 자산 및 수익 현황을 조회합니다. (기본 7일)"
      )
      await self._send_message(chat_id, help_msg)

    elif cmd == "/restart":
      # 플래그 파일 작성
      flag_file = os.path.join(self.config.storage_dir, ".restart_pending")
      try:
        os.makedirs(self.config.storage_dir, exist_ok=True)
        with open(flag_file, "w", encoding="utf-8") as f:
          f.write("restart_pending")
      except Exception as exc:
        logger.error(f"재시작 플래그 파일 생성 실패: {exc}")

      await self._send_message(chat_id, "🔄 서버를 재시작합니다. 약 5~8초 정도 소요됩니다...")
      self.exit_system()

    elif cmd == "/asset":
      # typing 상태 표시
      await self._send_chat_action(chat_id, "typing")
      try:
        # 1. API 호출
        summary = await get_asset_summary()

        # 2. 텍스트 빌드
        total_val = summary.total_valuation_krw
        total_principal = summary.total_principal
        total_profit = summary.total_profit
        roi = summary.cumulative_roi

        profit_sign = "+" if total_profit >= 0 else ""

        summary_section = (
            "💰 **통합 자산 현황**\n"
            f"• 총 평가자산: {total_val:,.0f}원\n"
            f"• 총 투자원금: {total_principal:,.0f}원\n"
            f"• 누적 투자수익: {profit_sign}{total_profit:,.0f}원 ({roi:.1f}%)"
        )

        exch_info = summary.exchange_rate
        exch_date = exch_info.get("date", "알 수 없음")
        exch_rate = exch_info.get("rate", 1.0)
        price_date = summary.latest_price_date

        info_section = (
            "📅 **기준 정보**\n"
            f"• 환율 기준일: {exch_date} (적용 환율: {exch_rate:,.1f}원)\n"
            f"• 주가 기준일: {price_date} (최신 DB 가격 데이터 기준)"
        )

        final_msg = (
            f"{summary_section}\n\n"
            f"{info_section}"
        )
        await self._send_message(chat_id, final_msg)

      except Exception as exc:
        logger.exception(f"자산 정보 조회 CLI 오류: {exc}")
        await self._send_message(chat_id, f"⚠️ 자산 정보를 가져오는데 실패했습니다: {exc}")

    elif cmd == "/ratio":
      await self._send_chat_action(chat_id, "typing")
      try:
        ratios = await get_asset_ratios()

        # 1. 대분류 비중 빌드
        major_items = []
        for item in ratios.major_results:
          diff_sign = "+" if item.diff_amt >= 0 else ""
          major_items.append(
              f"• {item.category}: {item.current_ratio:.1f}% ({item.current_amt:,.0f}원) "
              f"[목표: {item.target_percentage:.1f}% | 차액: {diff_sign}{item.diff_amt:,.0f}원]"
          )
        major_section = "\n".join(major_items)

        # 2. 소분류 비중 그룹화 빌드 (parent_category별로 묶음)
        from collections import defaultdict
        sub_groups = defaultdict(list)
        for item in ratios.sub_results:
          parent = item.parent_category or "기타"
          sub_groups[parent].append(item)

        sub_sections = []
        for parent, items in sub_groups.items():
          sub_items = []
          for item in items:
            diff_sign = "+" if item.diff_amt >= 0 else ""
            sub_items.append(
                f"  - {item.category}: {item.current_ratio:.1f}% ({item.current_amt:,.0f}원) "
                f"[목표: {item.target_percentage:.1f}% | 차액: {diff_sign}{item.diff_amt:,.0f}원]"
            )
          sub_sections.append(f"[{parent}]\n" + "\n".join(sub_items))
        sub_section = "\n\n".join(sub_sections)

        final_msg = (
            "📊 **자산 대분류 비중 및 리밸런싱**\n"
            f"{major_section}\n\n"
            "🔍 **자산 소분류 비중 및 리밸런싱**\n"
            f"{sub_section}\n\n"
            "*(참고: 차액이 +이면 목표 대비 초과 상태, -이면 목표 대비 부족 상태를 뜻합니다.)*"
        )
        await self._send_message(chat_id, final_msg)

      except Exception as exc:
        logger.exception(f"자산 비중 조회 CLI 오류: {exc}")
        await self._send_message(chat_id, f"⚠️ 자산 비중 정보를 가져오는데 실패했습니다: {exc}")

    elif cmd in ["/transactions", "/tx"]:
      tokens = text.strip().split()
      limit = 5
      if len(tokens) > 1:
        try:
          limit = int(tokens[1])
          if limit <= 0:
            limit = 5
        except ValueError:
          pass

      await self._send_chat_action(chat_id, "typing")
      try:
        tx_resp = await get_transactions()
        transactions = tx_resp.transactions
        # 최신 거래 순으로 내림차순 정렬
        transactions.sort(key=lambda x: (x.transaction_date, x.id or 0), reverse=True)

        recent_txs = transactions[:limit]

        if not recent_txs:
          await self._send_message(chat_id, "📝 최근 거래 내역이 없습니다.")
          return

        tx_items = []
        for tx in recent_txs:
          date_str = tx.transaction_date
          tx_type = tx.type
          type_map = {
              "BUY": "매수",
              "SELL": "매도",
              "DEPOSIT": "입금",
              "WITHDRAW": "출금",
              "INITIAL_BALANCE": "초기잔고",
              "INTEREST": "이자",
              "TAX": "세금",
              "CASH_ADJUSTMENT": "현금조정"
          }
          type_kor = type_map.get(tx_type, tx_type)
          acc_display = f" | {tx.account_display_name}" if tx.account_display_name else ""

          asset_info = ""
          if tx.asset_name:
            ticker_info = f" ({tx.asset_ticker})" if tx.asset_ticker else ""
            asset_info = f" - {tx.asset_name}{ticker_info}"

          amt_str = ""
          if tx_type in ["BUY", "SELL"] and tx.quantity > 0:
            price_unit = "원" if tx.currency == "KRW" else f" {tx.currency}"
            total_unit = "원" if tx.currency == "KRW" else f" {tx.currency}"

            exch_str = ""
            if tx.currency != "KRW" and tx.exchange_rate:
              krw_total = tx.total_amount * tx.exchange_rate
              exch_str = f" (환율 {tx.exchange_rate:,.1f}원 | 원화 환산 {krw_total:,.0f}원)"

            amt_str = f"\n  {tx.quantity:,.2f}주 @ {tx.price:,.2f}{price_unit} | 총 {tx.total_amount:,.2f}{total_unit}{exch_str}"
          else:
            unit = "원" if tx.currency == "KRW" else f" {tx.currency}"
            exch_str = ""
            if tx.currency != "KRW" and tx.exchange_rate:
              krw_total = tx.total_amount * tx.exchange_rate
              exch_str = f" (원화 환산 {krw_total:,.0f}원)"
            amt_str = f"\n  총 {tx.total_amount:,.2f}{unit}{exch_str}"

          memo_str = f" [{tx.memo}]" if tx.memo else ""

          tx_items.append(
              f"• [{date_str}] **{type_kor}**{acc_display}{asset_info}{memo_str}{amt_str}"
          )

        tx_section = "\n".join(tx_items)
        final_msg = f"📝 **최근 거래 내역 (최근 {len(recent_txs)}건)**\n{tx_section}"
        await self._send_message(chat_id, final_msg)

      except Exception as exc:
        logger.exception(f"최근 거래내역 조회 CLI 오류: {exc}")
        await self._send_message(chat_id, f"⚠️ 최근 거래내역을 가져오는데 실패했습니다: {exc}")

    elif cmd == "/yearly":
      await self._send_chat_action(chat_id, "typing")
      try:
        yearly_resp = await get_yearly_stats()
        stats = yearly_resp.stats
        stats.sort(key=lambda x: x.year, reverse=True)

        if not stats:
          await self._send_message(chat_id, "📅 연도별 자산 통계 데이터가 없습니다.")
          return

        yearly_items = []
        for y in stats:
          profit_sign = "+" if y.profit >= 0 else ""
          inc_sign = "+" if y.increase >= 0 else ""
          yearly_items.append(
              f"• **{y.year}년**:\n"
              f"  - 기말 자산: {y.assets:,.0f}원 (전년비 {inc_sign}{y.increase:,.0f}원)\n"
              f"  - 투자 수익: {profit_sign}{y.profit:,.0f}원 ({y.roi:+.1f}%)\n"
              f"  - 순 투자금 추가액: {y.contribution:,.0f}원"
          )

        yearly_section = "\n".join(yearly_items)
        final_msg = f"📅 **연도별 자산 및 투자 수익 현황**\n{yearly_section}"
        await self._send_message(chat_id, final_msg)

      except Exception as exc:
        logger.exception(f"연간 수익률 조회 CLI 오류: {exc}")
        await self._send_message(chat_id, f"⚠️ 연간 수익률 정보를 가져오는데 실패했습니다: {exc}")

    elif cmd == "/daily":
      tokens = text.strip().split()
      days = 7
      if len(tokens) > 1:
        try:
          days = int(tokens[1])
          if days <= 0:
            days = 7
        except ValueError:
          pass

      await self._send_chat_action(chat_id, "typing")
      try:
        daily_resp = await get_daily_stats(all_data=True)
        stats = daily_resp.stats
        stats.sort(key=lambda x: x.date, reverse=True)

        if not stats:
          await self._send_message(chat_id, "📈 일별 스냅샷 데이터가 없습니다.")
          return

        recent_daily = stats[:days]

        daily_items = []
        for d in recent_daily:
          try:
            dt = datetime.datetime.strptime(d.date, "%Y-%m-%d")
            weekday_map = ["월", "화", "수", "목", "금", "토", "일"]
            weekday_str = weekday_map[dt.weekday()]
            date_display = f"{d.date[5:]} ({weekday_str})"
          except Exception:
            date_display = d.date

          profit_sign = "+" if d.profit >= 0 else ""
          dep_str = f" | 입출금: {d.contribution:,.0f}원" if d.contribution != 0 else ""

          daily_items.append(
              f"• {date_display}: 자산 {d.assets:,.0f}원 | "
              f"수익 {profit_sign}{d.profit:,.0f}원 ({d.roi:+.2f}%){dep_str}"
          )

        daily_section = "\n".join(daily_items)
        final_msg = f"📈 **일별 자산 및 투자 수익 현황 (최근 {len(recent_daily)}영업일 스냅샷)**\n{daily_section}"
        await self._send_message(chat_id, final_msg)

      except Exception as exc:
        logger.exception(f"일별 수익률 조회 CLI 오류: {exc}")
        await self._send_message(chat_id, f"⚠️ 일별 수익률 정보를 가져오는데 실패했습니다: {exc}")

    else:
      await self._send_message(
          chat_id,
          f"⚠️ 알 수 없는 명령어입니다: {cmd}\n사용 가능한 명령어 확인을 위해 `/help`를 입력해 보세요."
      )

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
