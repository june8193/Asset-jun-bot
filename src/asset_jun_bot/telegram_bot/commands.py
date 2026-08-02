# -*- coding: utf-8 -*-
"""CLI 명령어 분기 처리 및 메시지 디스패칭을 담당하는 경량화된 라우터 모듈입니다."""

import logging
import os
import sys
from typing import TYPE_CHECKING, Callable, Awaitable

from .renderer import MessageRenderer, markdown_to_html, remove_markdown_markup

if TYPE_CHECKING:
  from .client import TelegramClient
  from .bot import TelegramBot
  from ..config import Config

logger = logging.getLogger(__name__)


def format_sync_result_message(result: dict) -> str:
  """동기화 결과를 텔레그램 마크다운 포맷으로 가공합니다 (MessageRenderer 위임)."""
  return MessageRenderer.render_sync_result(result)


class CLICommandHandler:
  """텔레그램 CLI 명령어를 처리하는 디스패처 클래스입니다."""

  def __init__(
      self,
      client: "TelegramClient",
      config: "Config",
      bot: "TelegramBot | None" = None,
  ):
    """CLICommandHandler 인스턴스를 생성합니다."""
    self.client = client
    self.config = config
    self.bot = bot

    # 커맨드 매핑 테이블
    self.handlers: dict[
        str, Callable[[int, str], Awaitable[None]]
    ] = {
        "/help": self.handle_help,
        "/restart": self.handle_restart,
        "/asset": self.handle_asset,
        "/ratio": self.handle_ratio,
        "/transactions": self.handle_transactions,
        "/tx": self.handle_transactions,
        "/yearly": self.handle_yearly,
        "/daily": self.handle_daily,
        "/sync": self.handle_sync,
    }

  async def process_cli_command(self, chat_id: int, text: str) -> None:
    """CLI 명령어 요청을 받아 알맞은 핸들러 함수로 디스패치합니다."""
    cmd = text.strip().split()[0].lower()
    handler = self.handlers.get(cmd)

    if handler:
      await handler(chat_id, text)
    else:
      await self.client.send_message(
          chat_id,
          f"⚠️ 알 수 없는 명령어입니다: {cmd}\n사용 가능한 명령어 확인을 위해 `/help`를 입력해 보세요."
      )

  async def handle_help(self, chat_id: int, text: str) -> None:
    """도움말 메시지를 출력합니다."""
    help_msg = (
        "💡 **asset-jun-bot 명령어 안내**\n"
        "• /help: 현재 명령어 리스트를 확인합니다.\n"
        "• /restart: 봇 서버를 완전히 재시작합니다 (MCP 서버 연동 초기화 포함).\n"
        "• /asset: 현재 통합 자산 총액 및 누적 투자 수익, 기준 정보를 조회합니다.\n"
        "• /ratio: 대분류 및 소분류 자산 비중과 목표비중 리밸런싱 현황을 조회합니다.\n"
        "• /tx 또는 /transactions [개수]: 최근 거래내역을 조회합니다. (기본 5개)\n"
        "• /yearly: 연도별 자산 통계 및 수익률을 조회합니다.\n"
        "• /daily [일수]: 스냅샷 기준 일별 자산 및 수익 현황을 조회합니다. (기본 7일)\n"
        "• /sync [일수]: 키움증권 거래내역을 수동으로 동기화합니다. (기본 7일)"
    )
    await self.client.send_message(chat_id, help_msg)

  async def handle_restart(self, chat_id: int, text: str) -> None:
    """봇 프로세스를 재시작합니다."""
    flag_file = os.path.join(self.config.storage_dir, ".restart_pending")
    try:
      os.makedirs(self.config.storage_dir, exist_ok=True)
      with open(flag_file, "w", encoding="utf-8") as f:
        f.write("restart_pending")
    except Exception as exc:
      logger.error(f"재시작 플래그 파일 생성 실패: {exc}")

    await self.client.send_message(chat_id, "🔄 서버를 재시작합니다. 약 5~8초 정도 소요됩니다...")
    if self.bot and hasattr(self.bot, "exit_system"):
      self.bot.exit_system()
    else:
      logger.info("시스템을 종료합니다 (exit 0)...")
      sys.exit(0)

  async def handle_asset(self, chat_id: int, text: str) -> None:
    """통합 자산 현황 정보를 조회합니다."""
    await self.client.send_chat_action(chat_id, "typing")
    try:
      from . import get_asset_summary
      summary = await get_asset_summary()
      final_msg = MessageRenderer.render_asset_summary(summary)
      await self.client.send_message(chat_id, final_msg)
    except Exception as exc:
      logger.exception(f"자산 정보 조회 CLI 오류: {exc}")
      await self.client.send_message(chat_id, f"⚠️ 자산 정보를 가져오는데 실패했습니다: {exc}")

  async def handle_ratio(self, chat_id: int, text: str) -> None:
    """자산 비중 및 리밸런싱 정보를 조회합니다."""
    await self.client.send_chat_action(chat_id, "typing")
    try:
      from . import get_asset_ratios
      ratios = await get_asset_ratios()
      final_msg = MessageRenderer.render_asset_ratios(ratios)
      await self.client.send_message(chat_id, final_msg)
    except Exception as exc:
      logger.exception(f"자산 비중 조회 CLI 오류: {exc}")
      await self.client.send_message(chat_id, f"⚠️ 자산 비중 정보를 가져오는데 실패했습니다: {exc}")

  async def handle_transactions(self, chat_id: int, text: str) -> None:
    """최근 거래 내역을 조회합니다."""
    tokens = text.strip().split()
    limit = 5
    if len(tokens) > 1:
      try:
        limit = int(tokens[1])
        if limit <= 0:
          limit = 5
      except ValueError:
        pass

    await self.client.send_chat_action(chat_id, "typing")
    try:
      from . import get_transactions
      tx_resp = await get_transactions()
      final_msg = MessageRenderer.render_transactions(tx_resp, limit=limit)
      await self.client.send_message(chat_id, final_msg)
    except Exception as exc:
      logger.exception(f"최근 거래내역 조회 CLI 오류: {exc}")
      await self.client.send_message(chat_id, f"⚠️ 최근 거래내역을 가져오는데 실패했습니다: {exc}")

  async def handle_yearly(self, chat_id: int, text: str) -> None:
    """연도별 자산 통계를 조회합니다."""
    await self.client.send_chat_action(chat_id, "typing")
    try:
      from . import get_yearly_stats
      yearly_resp = await get_yearly_stats()
      final_msg = MessageRenderer.render_yearly_stats(yearly_resp)
      await self.client.send_message(chat_id, final_msg)
    except Exception as exc:
      logger.exception(f"연간 수익률 조회 CLI 오류: {exc}")
      await self.client.send_message(chat_id, f"⚠️ 연간 수익률 정보를 가져오는데 실패했습니다: {exc}")

  async def handle_daily(self, chat_id: int, text: str) -> None:
    """일별 자산 스냅샷 통계를 조회합니다."""
    tokens = text.strip().split()
    days = 7
    if len(tokens) > 1:
      try:
        days = int(tokens[1])
        if days <= 0:
          days = 7
      except ValueError:
        pass

    await self.client.send_chat_action(chat_id, "typing")
    try:
      from . import get_daily_stats
      daily_resp = await get_daily_stats(all_data=True)
      final_msg = MessageRenderer.render_daily_stats(daily_resp, days=days)
      await self.client.send_message(chat_id, final_msg)
    except Exception as exc:
      logger.exception(f"일별 수익률 조회 CLI 오류: {exc}")
      await self.client.send_message(chat_id, f"⚠️ 일별 수익률 정보를 가져오는데 실패했습니다: {exc}")

  async def handle_sync(self, chat_id: int, text: str) -> None:
    """키움증권 거래내역 수동 동기화를 수행합니다."""
    tokens = text.strip().split()
    days = 7
    if len(tokens) > 1:
      try:
        days = int(tokens[1])
        if days <= 0:
          days = 7
      except ValueError:
        pass

    await self.client.send_chat_action(chat_id, "typing")
    await self.client.send_message(chat_id, f"🔄 키움증권으로부터 {days}일간의 거래내역 동기화를 시작합니다...")
    try:
      from . import sync_kiwoom_transactions
      result = await sync_kiwoom_transactions(days=days)
      msg = MessageRenderer.render_sync_result(result)
      await self.client.send_message(chat_id, msg)
    except Exception as exc:
      logger.exception(f"거래내역 동기화 CLI 오류: {exc}")
      await self.client.send_message(chat_id, f"⚠️ 동기화 중 오류가 발생했습니다: {exc}")
