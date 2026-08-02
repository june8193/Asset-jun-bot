# -*- coding: utf-8 -*-
"""MessageRenderer 모듈 단위 테스트입니다."""

import pytest
from asset_jun_bot.asset_client.models import (
    AssetSummaryResponse,
    AssetRatiosResponse,
    AssetRatioItem,
    TransactionsResponse,
    TransactionItem,
    YearlyStatsResponse,
    YearlyStatItem,
    DailyStatsResponse,
    DailyStatItem,
)
from asset_jun_bot.telegram_bot.renderer import MessageRenderer


def test_render_asset_summary():
  """통합 자산 현황 마크다운 메시지 렌더링을 검증합니다."""
  summary = AssetSummaryResponse(
      total_valuation_krw=10000000.0,
      total_principal=8000000.0,
      total_profit=2000000.0,
      cumulative_roi=25.0,
      contribution_ratio=80.0,
      profit_ratio=20.0,
      exchange_rate={"date": "2026-08-01", "rate": 1350.0},
      latest_price_date="2026-08-01",
  )

  msg = MessageRenderer.render_asset_summary(summary)

  assert "💰 **통합 자산 현황**" in msg
  assert "10,000,000원" in msg
  assert "8,000,000원" in msg
  assert "+2,000,000원 (25.0%)" in msg
  assert "1,350.0원" in msg


def test_render_asset_ratios():
  """자산 비중 마크다운 메시지 렌더링을 검증합니다."""
  ratios = AssetRatiosResponse(
      total_valuation=10000000.0,
      total_target=10000000.0,
      additional_cash=0.0,
      major_results=[
          AssetRatioItem(
              category="주식",
              current_ratio=60.0,
              current_amt=6000000.0,
              target_percentage=50.0,
              target_amt=5000000.0,
              diff_amt=1000000.0,
          )
      ],
      sub_results=[
          AssetRatioItem(
              category="미국주식",
              parent_category="주식",
              current_ratio=40.0,
              current_amt=4000000.0,
              target_percentage=35.0,
              target_amt=3500000.0,
              diff_amt=500000.0,
          )
      ],
  )

  msg = MessageRenderer.render_asset_ratios(ratios)

  assert "📊 **자산 대분류 비중 및 리밸런싱**" in msg
  assert "• 주식: 60.0% (6,000,000원) [목표: 50.0% | 차액: +1,000,000원]" in msg
  assert "[주식]" in msg
  assert "- 미국주식: 40.0%" in msg


def test_render_transactions():
  """최근 거래내역 마크다운 메시지 렌더링을 검증합니다."""
  tx_resp = TransactionsResponse(
      transactions=[
          TransactionItem(
              id=1,
              account_id=1,
              asset_id=10,
              transaction_date="2026-08-01",
              type="BUY",
              quantity=10.0,
              price=100.0,
              total_amount=1000.0,
              currency="USD",
              exchange_rate=1350.0,
              asset_name="애플",
              asset_ticker="AAPL",
              account_display_name="키움 해외",
              memo="테스트 매수",
          )
      ]
  )

  msg = MessageRenderer.render_transactions(tx_resp, limit=5)

  assert "📝 **최근 거래 내역 (최근 1건)**" in msg
  assert "[2026-08-01] **매수** | 키움 해외 - 애플 (AAPL) [테스트 매수]" in msg
  assert "10.00주 @ 100.00 USD | 총 1,000.00 USD" in msg
  assert "(환율 1,350.0원 | 원화 환산 1,350,000원)" in msg


def test_render_transactions_empty():
  """거래내역이 없을 때의 마크다운 메시지 렌더링을 검증합니다."""
  tx_resp = TransactionsResponse(transactions=[])
  msg = MessageRenderer.render_transactions(tx_resp)
  assert msg == "📝 최근 거래 내역이 없습니다."


def test_render_yearly_stats():
  """연도별 자산 통계 마크다운 메시지 렌더링을 검증합니다."""
  yearly_resp = YearlyStatsResponse(
      stats=[
          YearlyStatItem(
              year=2025,
              assets=10000000.0,
              increase=2000000.0,
              profit=1500000.0,
              roi=18.5,
              contribution=500000.0,
          )
      ]
  )

  msg = MessageRenderer.render_yearly_stats(yearly_resp)

  assert "📅 **연도별 자산 및 투자 수익 현황**" in msg
  assert "• **2025년**:" in msg
  assert "기말 자산: 10,000,000원 (전년비 +2,000,000원)" in msg
  assert "투자 수익: +1,500,000원 (+18.5%)" in msg


def test_render_daily_stats():
  """일별 자산 스냅샷 통계 마크다운 메시지 렌더링을 검증합니다."""
  daily_resp = DailyStatsResponse(
      stats=[
          DailyStatItem(
              date="2026-08-01",
              assets=10000000.0,
              profit=100000.0,
              roi=1.0,
              contribution=0.0,
              increase=100000.0,
          )
      ]
  )

  msg = MessageRenderer.render_daily_stats(daily_resp, days=7)

  assert "📈 **일별 자산 및 투자 수익 현황" in msg
  assert "자산 10,000,000원 | 수익 +100,000원 (+1.00%)" in msg


def test_render_sync_result():
  """키움 동기화 결과 마크다운 메시지 렌더링을 검증합니다."""
  result = {
      "success_count": 1,
      "pending_count": 1,
      "synced_transactions": [{
          "type": "BUY",
          "asset_name": "삼성전자",
          "quantity": 5,
          "price": 70000,
          "total_amount": 350000,
          "currency": "KRW",
          "is_manual_matched": True,
      }],
      "unregistered_assets": [{
          "type": "BUY",
          "name": "엔비디아",
          "ticker": "NVDA",
          "quantity": 2,
          "price": 120.0,
          "total_amount": 240.0,
          "currency": "USD",
      }],
      "failed_accounts": [{
          "account_name": "위탁1",
          "error": "비밀번호 오류",
      }],
  }

  msg = MessageRenderer.render_sync_result(result)

  assert "🤖 **키움증권 거래내역 자동 동기화 결과**" in msg
  assert "✅ **성공적으로 저장된 거래 (1건)**" in msg
  assert "⚠️ **자산 마스터 미등록으로 저장이 생략된 거래 (1건)**" in msg
  assert "엔비디아 (NVDA)" in msg
  assert "⚠️ **동기화 실패 계좌 (1개)**" in msg
  assert "계좌 위탁1: 비밀번호 오류" in msg
