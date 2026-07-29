---
name: asset-auditor
description: 자산 점검, 매매 복기 및 1대1 인터뷰 스킬. Use when requested to audit assets, review trades, or perform periodic investment checkup.
---

# 자산 점검 및 투자 복기 스킬 (asset-auditor)

사용자의 자산점검 및 투자 복기 요청에 따라 1대1 인터뷰(Grill-Me) 방식으로 엄격하게 워크플로우를 실행하는 스킬입니다.

## 1. 기본 원칙 및 태도
- **언어 정책**: 모든 대화와 보고서는 친절하면서도 객관적인 **한국어**로 작성합니다.
- **인터뷰 규칙 (Grill-Me)**: 절대로 여러 질문을 한 번에 쏟아내지 말고, **반드시 한 번에 단 하나의 구체적인 질문만 던진 후 사용자의 답변을 대기**하십시오.
- **원칙 검증**: `asset-advisor/references/investment-principles.md`를 로드하여 사용자의 매매 및 계획이 원칙(손절 -15%, 장세대응, FOMO 방지 등)에 부합하는지 비판적으로 검증합니다.

---

## 2. 자산 점검 및 투자 복기 워크플로우 단계

### [1단계] 정보 수집 및 AI 예비 진단
1. `uv run python scripts/get_storage_dir.py` 실행 ➔ `STORAGE_DIR` 파악
2. `STORAGE_DIR/asset_audits/asset_audit_journal.md` 조회 ➔ `LAST_AUDIT_DATE` 식별 (없을 경우 30일 전)
3. `LAST_AUDIT_DATE`부터 오늘 사이 주간 리포트 파일 요약 및 `get_market_history` 호출로 KOSPI/S&P500 지수 변동 수집
4. `get_snapshots` / `get_asset_ratios` 호출로 자산 배분 현황 파악
5. `investment-principles.md` 기반 AI 예비 진단 및 조언 도출
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 이전 점검일, 지수 수집, 자산 비중 조회 및 AI 예비 조언이 준비되었는가?
  - [ ] 현황 브리핑 출력 후 **질문 1개만** 던지고 턴을 멈추어 사용자 답변을 대기하고 있는가?

### [2단계] 장세 판단 및 리밸런싱 계획 인터뷰 (Grill-Me)
1. 사용자 답변에 따른 투자 원칙 대조 및 피드백 (Grilling)
2. 추상적 답변 시 타겟 종목, 거래 규모, 집행 주기, 투자 가설 등 구체적 정보 추가 질문
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 장세 판단, 구체적 리밸런싱 종목, 금액, 주기에 대한 사용자 답변이 명확히 수집되었는가?

### [3단계] 미복기 거래 필터링 및 매매복기 인터뷰 (Grill-Me)
1. `get_transactions`로 미복기 BUY/SELL 거래 필터링
2. 거래 없는 경우 4단계로 즉시 이동
3. 거래가 있는 경우 시간순 1건씩 릴레이 질문: 진입 근거, 가설 붕괴 여부, 주가 변동 대조 (`get_stock_history`)
4. 거래 등급 부여: 🟢 Good Trade, 🔴 Bad Trade, 🟡 Hold
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 모든 미복기 거래에 대해 1건씩 질문이 수행되고 평가 등급(🟢/🔴/🟡)이 결정되었는가?

### [4단계] 통합 보고서 및 마스터 저널 직접 저장
1. 상세 보고서 생성: `STORAGE_DIR/asset_audits/asset_audit_YYYYMMDD_HHMMSS.md`
2. 마스터 저널 누적 업데이트: `STORAGE_DIR/asset_audits/asset_audit_journal.md` (최신 순 상단 삽입)
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 상세 보고서 및 마스터 저널 파일이 성공적으로 쓰기/업데이트되었는가?

### [5단계] 투자 원칙 개선 제안 피드백 및 마무리
- 지수 대비 알파 성과 제시 및 메타인지 피드백 제공 후 워크플로우 종료.
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 메타인지 피드백 및 투자 원칙 개선안이 최종 전달되었는가?
