---
name: asset-auditor
description: Use when requested to audit assets, review trades, or perform periodic investment checkup. 자산 점검, 매매 복기 및 1대1 인터뷰 스킬.
---

# 자산 점검 및 투자 복기 스킬 (asset-auditor)

사용자의 자산점검 및 투자 복기 요청에 따라 1대1 인터뷰(Grill-Me) 방식으로 엄격하게 워크플로우를 실행하는 스킬입니다.

## 1. 기본 원칙 및 태도
- **언어 정책**: 모든 대화와 보고서는 객관적인 **한국어**로 작성합니다.
- **인터뷰 규칙 (Grill-Me)**: 한 번에 단 하나의 구체적인 질문만 던진 후 사용자의 답변을 대기합니다.
- **원칙 검증**: `asset-advisor/references/investment-principles.md`를 로드하여 사용자의 매매 및 계획이 원칙(손절 -15%, 장세대응, FOMO 방지 등)에 부합하는지 비판적으로 검증합니다.

---

## 2. 자산 점검 및 투자 복기 워크플로우 단계

### [1단계] 정보 수집 및 AI 예비 진단
1. `uv run python scripts/get_storage_dir.py` 실행 ➔ `STORAGE_DIR` 파악
2. `STORAGE_DIR/asset_audits/asset_audit_journal.md` 조회 ➔ `LAST_AUDIT_DATE` 식별 및 **'현재 활성 전략(Active Strategy)'** 확인 (없을 경우 기본값 또는 30일 전)
3. `LAST_AUDIT_DATE`부터 오늘 사이 주간 리포트 파일 요약 및 `get_market_history` 호출로 KOSPI/S&P500/NASDAQ 지수 변동 수집
4. `get_snapshots` / `get_asset_ratios` / `get_yearly_stats` 호출로 자산 배분 현황 및 올해 YTD 수익률(ROI) 산출
5. **YTD 벤치마크 수익률 비교**:
   - `get_yearly_stats`의 올해 ROI와 `get_market_history` 기반 S&P 500 YTD 수익률을 비교하여 초과수익률(`Alpha = 포트폴리오 ROI - S&P 500 YTD`) 산출 (KOSPI/NASDAQ은 참고용 수집)
6. **AI YTD 알파 원인 분석 4대 레이어 (Attribution Analysis)**:
   - **Cash Drag 효과**: `get_asset_ratios`로 현금/달러 비중 측정 ➔ 상승장/하락장에서의 현금 보유에 따른 성과 영향도 계산
   - **보유 종목 기여도**: `get_asset_summary` / `get_stock_history` 기반 종목별 비중 $\times$ YTD 수익률 ➔ 특정 종목 쏠림 및 손익 기여도 분해
   - **시장/국가 노출도**: `get_market_history`로 한국(KOSPI) vs 미국(S&P 500) 자산 배분 비중에 따른 시장 지수 영향 구분
   - **원칙 준수 및 매매 행태**: `get_transactions`로 손절원칙(-15%) 미준수 방치, 잦은 매매, 뇌동매매 여부 대조
7. `investment-principles.md` 기반 AI 예비 진단 및 조언 도출 (4대 레이어 원인 분석 브리핑 포함)
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 이전 점검일, 현재 전략, 지수 수집, 자산 비중 조회, YTD 벤치마크 Alpha 산출 및 4대 레이어 원인 분석이 준비되었는가?
  - [ ] YTD S&P 500 비교 성과 및 팩트 기반 원인 분석이 포함된 현황 브리핑 출력 후 **질문 1개만** 던지고 턴을 멈추어 사용자 답변을 대기하고 있는가?

### [2단계] 장세 판단 및 리밸런싱/현재 전략 인터뷰 (Grill-Me)
1. 사용자 답변에 따른 투자 원칙 대조 및 피드백 (Grilling)
2. **YTD 알파(Alpha) 성과 연계 Grilling 질의**:
   - 🟢 `Alpha > 0` (시장 상회): 과도한 위험 노출(고변동성/레버리지 타점) 여부 점검 및 리밸런싱/수익 실현 계획 질의
   - 🔴 `Alpha < 0` (시장 하회): Cash drag(현금 비중 과다), 특정 종목 쏠림, 손절원칙(-15%) 미준수 등 원인 진단 질의
3. 장세 판단 및 **현재 운용 전략(ex. 조정장 저점매수, 상승장 모멘텀 추격매수 등 스탠스)** 명시/갱신 질의
4. 추상적 답변 시 타겟 종목, 거래 규모, 집행 주기, 투자 가설 등 구체적 정보 추가 질문
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] YTD Alpha 원인 진단, 장세 판단, 현재 활성 전략(변동 여부 포함), 구체적 리밸런싱 종목/금액/주기에 대한 사용자 답변이 명확히 수집되었는가?

### [3단계] 미복기 거래 필터링 및 매매복기 인터뷰 (Grill-Me)
1. `get_transactions`로 미복기 BUY/SELL 거래 필터링
2. 거래 없는 경우 4단계로 즉시 이동
3. 거래가 있는 경우 시간순 1건씩 릴레이 질문:
   - **거래 사유 및 가설**: 매수 건은 진입/매수 가설, 매도 건은 매도 이유(목표달성, 손절원칙 -15%, 가설붕괴, 자금회수 등) 질의
   - 주가 변동 대조 (`get_stock_history`) 및 투자 원칙 검증
4. 거래 등급 부여: 🟢 Good Trade, 🔴 Bad Trade, 🟡 Hold
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 모든 미복기 거래에 대해 1건씩 '거래 사유 및 가설' 질의가 수행되고 평가 등급(🟢/🔴/🟡)이 결정되었는가?

### [4단계] 통합 보고서 및 마스터 저널 직접 저장
1. 상세 보고서 생성: `STORAGE_DIR/asset_audits/asset_audit_YYYYMMDD_HHMMSS.md`
2. 마스터 저널 누적 업데이트: `STORAGE_DIR/asset_audits/asset_audit_journal.md`
   - **저널 및 보고서 구조**:
     - **상단 섹션**: `# 현재 활성 전략 (Active Strategy)` (최신 전략명, 갱신일자, 전략 기조 유지/변경 이력)
     - **YTD 벤치마크 성과 요약**: `[YTD 벤치마크 성과 비교]` 표 (포트폴리오 ROI vs S&P 500 YTD & Alpha 수치, 참고용 KOSPI/NASDAQ 변동률 기재)
     - **하단 이력**: 회차별 점검 내역 누적 (최신 순 상단 삽입, 회차별 장세 판단, YTD 성과 평가 및 거래별 `거래 사유 및 가설` 명시)
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] 상세 보고서 및 마스터 저널 파일 상단에 현재 활성 전략 섹션과 [YTD 벤치마크 성과 비교] 표가 정확히 반영되었는가?

### [5단계] 투자 원칙 개선 제안 피드백 및 마무리
- YTD S&P 500 지수 대비 알파 성과 최종 평가 및 메타인지 피드백 제공 후 워크플로우 종료.
- **완료 검증 조건 (Completion Criterion)**:
  - [ ] YTD Alpha 성과에 기반한 메타인지 피드백 및 투자 원칙 개선안이 최종 전달되었는가?
