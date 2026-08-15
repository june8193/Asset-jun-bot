---
name: asset-advisor
description: 자산 현황 조회, 자산 배분 비중 분석, 관심종목 시세 확인, 투자 원칙 기반 포트폴리오 상담 요청 시 사용.
---

# 통합 자산 관리 및 투자 분석 스킬 (asset-advisor)

## 1. 실행 지침 (Execution Protocol)
- **도구 즉시 실행**: 사전 안내 멘트(Preamble) 없이 필요한 `assetmanager` MCP 도구를 즉시 호출합니다.
- **투자 원칙 동기화**: 투자 상담 및 조언 시 `references/investment-principles.md`를 열람하여 원칙에 입각한 비판적 가설 검증을 수행합니다.
- **사례 기반 검증 (On-Demand)**: 상담 상황(종목, 고점돌파, 물타기, FOMO 등) 감지 시 `references/trade-cases-index.md` 색인을 확인하고, 매칭되는 `references/cases/*.md`를 로드하여 객관적 근거로 인용합니다.

## 2. MCP 도구 매핑
- **총자산 요약**: `get_asset_summary` (원금, 평가액, ROI)
- **자산 비중 & 리밸런싱**: `get_asset_ratios` (소분류 비중은 반드시 `current_amt / total_valuation * 100`으로 직접 계산)
- **관심종목 시세**: `get_watchlist_prices` (`country`: "KR" | "US")
- **포트폴리오 상세**: `get_portfolio_status` (종목 수량, 평가금, 예수금)
- **시장 지수 / 개별 주가 추이**: `get_market_history`, `get_stock_history`
- **통계 / 스냅샷 / 거래내역**: `get_yearly_stats`, `get_daily_stats`, `get_snapshots`, `get_transactions`
- **시세 동기화**: `refresh_market_prices`
- **텔레그램 발송**: `run_command`로 `uv run python scripts/send_telegram.py "[내용]"` 실행

## 3. 출력 서식 및 완료 기준 (Completion Criteria)
- **출력 서식**: 텔레그램 모바일 가독성을 위해 불릿 리스트, 줄바꿈, 텍스트 블록, 이모지만으로 구조화합니다.
- **완료 검증 조건**:
  - [ ] 요청된 자산 데이터가 MCP 도구 응답을 통해 정합성 있게 추출되었는가?
  - [ ] 소분류 자산 비중 계산 시 총자산 대비 비중(`current_amt / total_valuation * 100`)을 직접 산출했는가?
  - [ ] 투자 조언 시 `investment-principles.md`의 손절 기준(-15% 가설 점검) 및 장세 원칙이 반영되었는가?
  - [ ] 유사 패턴 상담 시 `trade-cases-index.md` 및 해당 `cases/*.md` 교훈을 인용했는가?
  - [ ] 텔레그램 모바일 가독성을 위해 불릿 리스트와 텍스트 블록 중심의 서식으로 구성되었는가?
