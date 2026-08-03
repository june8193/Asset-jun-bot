# -*- coding: utf-8 -*-
"""텔레그램 메시지 서식 렌더링 및 변환을 담당하는 Deep MessageRenderer 모듈입니다."""

import collections
import datetime
import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
  from ..asset_client.models import (
      AssetSummaryResponse,
      AssetRatiosResponse,
      TransactionsResponse,
      YearlyStatsResponse,
      DailyStatsResponse,
  )

logger = logging.getLogger(__name__)


def markdown_to_html(text: str) -> str:
  """마크다운 텍스트를 텔레그램용 HTML 서식으로 변환합니다.

  Args:
      text: 원본 마크다운 텍스트

  Returns:
      텔레그램 HTML 규격에 맞춰 이스케이프 및 변환된 HTML 텍스트
  """
  if not text:
    return ""

  text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
  text = re.sub(r"```([\s\S]*?)```", r"<pre>\1</pre>", text)
  text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)
  text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
  text = re.sub(r"\*([^*]+)\*", r"<b>\1</b>", text)
  text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
  text = re.sub(
      r"^\s*&gt;\s*(.*?)$", r"<blockquote>\1</blockquote>", text, flags=re.MULTILINE
  )
  text = re.sub(r"^\s*#{1,6}\s*(.*?)$", r"<b>\1</b>", text, flags=re.MULTILINE)
  text = re.sub(r"^\s*---\s*$", "━━━━━━━━━━━━━━━━━━━━", text, flags=re.MULTILINE)

  return text


def remove_markdown_markup(text: str) -> str:
  """텍스트에서 마크다운 마크업 서식을 지우고 순수 일반 텍스트로 변환합니다.

  Args:
      text: 마크다운 서식이 포함된 원본 텍스트

  Returns:
      서식 기호가 지워진 순수 일반 텍스트
  """
  if not text:
    return ""

  text = text.replace("```", "")
  text = text.replace("`", "")
  text = text.replace("**", "").replace("*", "")
  text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
  text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
  text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
  text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)

  return text


class MessageRenderer:
  """도메인 응답 모델을 텔레그램 규격 마크다운 메시지로 렌더링하는 클래스입니다."""

  @staticmethod
  def _format_currency_amount(
      price: float,
      total_amount: float,
      currency: str,
      exchange_rate: float | None = None,
      quantity: float | None = None,
  ) -> str:
    """통화별 단가, 총액 및 원화 환산 텍스트를 공통 포맷팅하는 헬퍼 함수입니다.

    Args:
        price: 거래 단가
        total_amount: 총 거래 금액
        currency: 통화 코드 (KRW, USD 등)
        exchange_rate: 적용 환율 (선택 사항)
        quantity: 매수/매도 수량 (선택 사항)

    Returns:
        포맷팅된 금액 및 환율 표시 문자열
    """
    unit = "원" if currency == "KRW" else f" {currency}"
    price_unit = "원" if currency == "KRW" else f" {currency}"

    exch_str = ""
    if currency != "KRW" and exchange_rate:
      krw_total = total_amount * exchange_rate
      exch_str = f" (환율 {exchange_rate:,.1f}원 | 원화 환산 {krw_total:,.0f}원)"

    if quantity is not None and quantity > 0:
      return f"\n  {quantity:,.2f}주 @ {price:,.2f}{price_unit} | 총 {total_amount:,.2f}{unit}{exch_str}"
    else:
      return f"\n  총 {total_amount:,.2f}{unit}{exch_str}"

  @staticmethod
  def render_asset_summary(summary: "AssetSummaryResponse") -> str:
    """통합 자산 현황 정보를 마크다운 메시지로 렌더링합니다.

    Args:
        summary: 자산 요약 응답 모델 객체

    Returns:
        마크다운 포맷의 자산 현황 및 기준 정보 메시지 문자열
    """
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

    exch_info = summary.exchange_rate or {}
    exch_date = exch_info.get("date", "알 수 없음")
    exch_rate = exch_info.get("rate", 1.0)
    price_date = summary.latest_price_date

    info_section = (
        "📅 **기준 정보**\n"
        f"• 환율 기준일: {exch_date} (적용 환율: {exch_rate:,.1f}원)\n"
        f"• 주가 기준일: {price_date} (최신 DB 가격 데이터 기준)"
    )

    return f"{summary_section}\n\n{info_section}"

  @staticmethod
  def render_asset_ratios(ratios: "AssetRatiosResponse") -> str:
    """자산 비중 및 리밸런싱 정보를 마크다운 메시지로 렌더링합니다.

    Args:
        ratios: 자산군별 비중 및 리밸런싱 정보 모델 객체

    Returns:
        마크다운 포맷의 자산 비중 안내 메시지 문자열
    """
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

    return (
        "📊 **자산 대분류 비중 및 리밸런싱**\n"
        f"{major_section}\n\n"
        "🔍 **자산 소분류 비중 및 리밸런싱**\n"
        f"{sub_section}\n\n"
        "*(참고: 차액이 +이면 목표 대비 초과 상태, -이면 목표 대비 부족 상태를 뜻합니다.)*"
    )

  @staticmethod
  def render_transactions(tx_resp: "TransactionsResponse", limit: int = 5) -> str:
    """최근 거래내역 목록을 마크다운 메시지로 렌더링합니다.

    Args:
        tx_resp: 거래 내역 목록 응답 모델 객체
        limit: 표시할 최대 거래 개수 (기본 5개)

    Returns:
        마크다운 포맷의 최근 거래내역 메시지 문자열
    """
    transactions = list(tx_resp.transactions)
    transactions.sort(key=lambda x: (x.transaction_date, x.id or 0), reverse=True)
    recent_txs = transactions[:limit]

    if not recent_txs:
      return "📝 최근 거래 내역이 없습니다."

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

    tx_items = []
    for tx in recent_txs:
      date_str = tx.transaction_date
      type_kor = type_map.get(tx.type, tx.type)
      acc_display = f" | {tx.account_display_name}" if tx.account_display_name else ""

      asset_info = ""
      if tx.asset_name:
        ticker_info = f" ({tx.asset_ticker})" if tx.asset_ticker else ""
        asset_info = f" - {tx.asset_name}{ticker_info}"

      is_buy_sell = tx.type in ["BUY", "SELL"] and tx.quantity > 0
      qty_param = tx.quantity if is_buy_sell else None
      amt_str = MessageRenderer._format_currency_amount(
          price=tx.price,
          total_amount=tx.total_amount,
          currency=tx.currency,
          exchange_rate=tx.exchange_rate,
          quantity=qty_param,
      )

      memo_str = f" [{tx.memo}]" if tx.memo else ""
      tx_items.append(
          f"• [{date_str}] **{type_kor}**{acc_display}{asset_info}{memo_str}{amt_str}"
      )

    tx_section = "\n".join(tx_items)
    return f"📝 **최근 거래 내역 (최근 {len(recent_txs)}건)**\n{tx_section}"

  @staticmethod
  def render_yearly_stats(yearly_resp: "YearlyStatsResponse") -> str:
    """연도별 자산 및 투자 수익 통계를 마크다운 메시지로 렌더링합니다.

    Args:
        yearly_resp: 연도별 자산 현황 통계 응답 모델 객체

    Returns:
        마크다운 포맷의 연도별 통계 메시지 문자열
    """
    stats = list(yearly_resp.stats)
    stats.sort(key=lambda x: x.year, reverse=True)

    if not stats:
      return "📅 연도별 자산 통계 데이터가 없습니다."

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
    return f"📅 **연도별 자산 및 투자 수익 현황**\n{yearly_section}"

  @staticmethod
  def render_daily_stats(daily_resp: "DailyStatsResponse", days: int = 7) -> str:
    """일별 자산 스냅샷 통계를 마크다운 메시지로 렌더링합니다.

    Args:
        daily_resp: 일별 자산 현황 통계 응답 모델 객체
        days: 최근 조회 영업일 수 (기본 7일)

    Returns:
        마크다운 포맷의 일별 통계 메시지 문자열
    """
    stats = list(daily_resp.stats)
    stats.sort(key=lambda x: x.date, reverse=True)

    if not stats:
      return "📈 일별 스냅샷 데이터가 없습니다."

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
    return f"📈 **일별 자산 및 투자 수익 현황 (최근 {len(recent_daily)}영업일 스냅샷)**\n{daily_section}"

  @staticmethod
  def _extract_date_suffix(tx: dict[str, Any]) -> str:
    """거래 딕셔너리에서 traded_at 정보를 추출하여 날짜 접미사 문자열을 반환합니다."""
    traded_at = tx.get("traded_at")
    return f" 📅 {traded_at}" if traded_at else ""

  @staticmethod
  def render_sync_result(result: dict[str, Any]) -> str:
    """동기화 결과 딕셔너리를 마크다운 메시지로 렌더링합니다.

    Args:
        result: 키움증권 동기화 결과 데이터 딕셔너리

    Returns:
        마크다운 포맷의 동기화 결과 리포트 메시지 문자열
    """
    success_count = result.get("success_count", 0)
    pending_count = result.get("pending_count", 0)
    synced = result.get("synced_transactions", [])
    pending = result.get("unregistered_assets", [])

    lines = ["🤖 **키움증권 거래내역 자동 동기화 결과**\n"]

    lines.append(f"✅ **성공적으로 저장된 거래 ({success_count}건)**")
    if success_count > 0:
      for tx in synced:
        t_type = "매수" if tx["type"] == "BUY" else ("매도" if tx["type"] == "SELL" else "배당")
        date_suffix = MessageRenderer._extract_date_suffix(tx)
        if t_type == "배당":
          if tx["currency"] == "USD":
            lines.append(f"• [배당] {tx['asset_name']} | 배당금 입금 | 총 ${tx['price']:,.2f}{date_suffix}")
          else:
            lines.append(f"• [배당] {tx['asset_name']} | 배당금 입금 | 총 {tx['price']:,.0f}원{date_suffix}")
        else:
          price_str = f"${tx['price']:,.2f}" if tx["currency"] == "USD" else f"{tx['price']:,.0f}원"
          total_str = f"${tx['total_amount']:,.2f}" if tx["currency"] == "USD" else f"{tx['total_amount']:,.0f}원"
          tag_str = " [수동 매칭완료]" if tx.get("is_manual_matched") else ""
          lines.append(
              f"• [{t_type}] {tx['asset_name']} | {tx['quantity']:,.0f}주 | {price_str} (총 {total_str}){tag_str}{date_suffix}"
          )
    else:
      lines.append("• 새롭게 감지된 거래가 없습니다.")

    lines.append("")
    lines.append(f"⚠️ **자산 마스터 미등록으로 저장이 생략된 거래 ({pending_count}건)**")
    if pending_count > 0:
      lines.append("아래 종목은 시스템 자산 목록에 등록되어 있지 않아 거래내역을 저장하지 못했습니다. 웹에서 해당 자산을 추가 등록하신 후 `/sync` 명령어를 통해 재동기화해 주세요.")
      for tx in pending:
        t_type = "매수" if tx["type"] == "BUY" else ("매도" if tx["type"] == "SELL" else "배당")
        price_str = f"${tx['price']:,.2f}" if tx["currency"] == "USD" else f"{tx['price']:,.0f}원"
        total_str = f"${tx['total_amount']:,.2f}" if tx["currency"] == "USD" else f"{tx['total_amount']:,.0f}원"
        date_suffix = MessageRenderer._extract_date_suffix(tx)
        lines.append(
            f"• **{tx['name']} ({tx['ticker']})**\n"
            f"  - 누락 거래: [{t_type}] {tx['quantity']:,.0f}주 | {price_str} (총 {total_str}){date_suffix}"
        )
    else:
      lines.append("• 미등록 스킵된 거래가 없습니다.")

    lines.append("")
    lines.append("👉 [웹에서 자산 등록하기](http://localhost:5173/assets)")

    failed_accounts = result.get("failed_accounts", [])
    if failed_accounts:
      lines.append("")
      lines.append(f"⚠️ **동기화 실패 계좌 ({len(failed_accounts)}개)**")
      for fa in failed_accounts:
        lines.append(f"• 계좌 {fa['account_name']}: {fa['error']}")

    return "\n".join(lines)
