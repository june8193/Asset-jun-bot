# -*- coding: utf-8 -*-
"""CLI 명령어 분기 처리 및 메시지 포맷팅을 담당하는 핸들러 모듈입니다."""

import collections
import datetime
import logging
import os
import sys
from typing import TYPE_CHECKING, Callable, Awaitable

from .. import asset_client

if TYPE_CHECKING:
  from .client import TelegramClient
  from .bot import TelegramBot
  from ..config import Config

logger = logging.getLogger(__name__)


def format_sync_result_message(result: dict) -> str:
  """동기화 결과를 텔레그램 마크다운 포맷으로 가공합니다."""
  success_count = result.get("success_count", 0)
  pending_count = result.get("pending_count", 0)
  synced = result.get("synced_transactions", [])
  pending = result.get("unregistered_assets", [])

  lines = ["🤖 **키움증권 거래내역 자동 동기화 결과**\n"]

  # 성공 내역
  lines.append(f"✅ **성공적으로 저장된 거래 ({success_count}건)**")
  if success_count > 0:
    for tx in synced:
      t_type = "매수" if tx["type"] == "BUY" else ("매도" if tx["type"] == "SELL" else "배당")

      if t_type == "배당":
        if tx["currency"] == "USD":
          lines.append(f"• [배당] {tx['asset_name']} | 배당금 입금 | 총 ${tx['price']:,.2f}")
        else:
          lines.append(f"• [배당] {tx['asset_name']} | 배당금 입금 | 총 {tx['price']:,.0f}원")
      else:
        price_str = f"${tx['price']:,.2f}" if tx["currency"] == "USD" else f"{tx['price']:,.0f}원"
        total_str = f"${tx['total_amount']:,.2f}" if tx["currency"] == "USD" else f"{tx['total_amount']:,.0f}원"

        lines.append(
            f"• [{t_type}] {tx['asset_name']} | {tx['quantity']:,.0f}주 | {price_str} (총 {total_str})"
        )
  else:
    lines.append("• 새롭게 감지된 거래가 없습니다.")

  lines.append("")

  # 미등록 내역
  lines.append(f"⚠️ **자산 마스터 미등록으로 저장이 생략된 거래 ({pending_count}건)**")
  if pending_count > 0:
    lines.append("아래 종목은 시스템 자산 목록에 등록되어 있지 않아 거래내역을 저장하지 못했습니다. 웹에서 해당 자산을 추가 등록하신 후 `/sync` 명령어를 통해 재동기화해 주세요.")
    for tx in pending:
      t_type = "매수" if tx["type"] == "BUY" else ("매도" if tx["type"] == "SELL" else "배당")
      price_str = f"${tx['price']:,.2f}" if tx["currency"] == "USD" else f"{tx['price']:,.0f}원"
      total_str = f"${tx['total_amount']:,.2f}" if tx["currency"] == "USD" else f"{tx['total_amount']:,.0f}원"

      lines.append(
          f"• **{tx['name']} ({tx['ticker']})**\n"
          f"  - 누락 거래: [{t_type}] {tx['quantity']:,.0f}주 | {price_str} (총 {total_str})"
      )
  else:
    lines.append("• 미등록 스킵된 거래가 없습니다.")

  lines.append("")
  lines.append("👉 [웹에서 자산 등록하기](http://localhost:5173/assets)")

  return "\n".join(lines)


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

      final_msg = f"{summary_section}\n\n{info_section}"
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

      major_items = []
      for item in ratios.major_results:
        diff_sign = "+" if item.diff_amt >= 0 else ""
        major_items.append(
            f"• {item.category}: {item.current_ratio:.1f}% ({item.current_amt:,.0f}원) "
            f"[목표: {item.target_percentage:.1f}% | 차액: {diff_sign}{item.diff_amt:,.0f}원]"
        )
      major_section = "\n".join(major_items)

      sub_groups = collections.defaultdict(list)
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
      transactions = tx_resp.transactions
      transactions.sort(key=lambda x: (x.transaction_date, x.id or 0), reverse=True)

      recent_txs = transactions[:limit]

      if not recent_txs:
        await self.client.send_message(chat_id, "📝 최근 거래 내역이 없습니다.")
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
            "CASH_ADJUSTMENT": "현금조정",
        }
        type_kor = type_map.get(tx_type, tx_type)
        acc_display = f" | {tx.account_display_name}" if tx.account_display_name else ""

        asset_info = ""
        if tx.asset_name:
          ticker_info = f" ({tx.asset_ticker})" if tx.asset_ticker else ""
          asset_info = f" - {tx.asset_name}{ticker_info}"

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
      stats = yearly_resp.stats
      stats.sort(key=lambda x: x.year, reverse=True)

      if not stats:
        await self.client.send_message(chat_id, "📅 연도별 자산 통계 데이터가 없습니다.")
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
      stats = daily_resp.stats
      stats.sort(key=lambda x: x.date, reverse=True)

      if not stats:
        await self.client.send_message(chat_id, "📈 일별 스냅샷 데이터가 없습니다.")
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
      msg = format_sync_result_message(result)
      await self.client.send_message(chat_id, msg)
    except Exception as exc:
      logger.exception(f"거래내역 동기화 CLI 오류: {exc}")
      await self.client.send_message(chat_id, f"⚠️ 동기화 중 오류가 발생했습니다: {exc}")
