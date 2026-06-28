---
name: us-weekly-index-report
description: Generate, save, and convert the weekly S&P 500/NASDAQ/DOW index status report into Markdown and PDF formats by reading daily reports of the past week, query weekly index change, and send notification. Use when executing weekly market index briefings.
---

# 미국 시장 주간 지수 현황 보고서 작성 (US Weekly Index Report)

이 스킬은 예약된 시간에 에이전트가 직접 도구(Tools)를 체인으로 호출하여 가장 최근에 완료된 한 주(일요일~토요일)의 미국 시장(S&P 500, NASDAQ, DOW JONES) 일일 보고서들을 수집·요약하고, 주간 지수 변동률 데이터를 획득한 뒤 종합 주간 마크다운 보고서를 작성한 뒤, PDF로 변환하여 지정된 저장 공간에 보관하고 텔레그램으로 전송합니다.

## Quick start

이 스킬이 로드되면 에이전트는 별도의 조작 없이 아래의 **Workflows** 절차에 명시된 도구들을 순서대로 사용하여 보고서 작성 및 변환을 완료해야 합니다.

⚠️ **계획 모드(Planning Mode) 및 승인 생략**: 이 스킬을 가동할 때는 구현 계획서(Implementation Plan, `implementation_plan.md`) 작성 및 사용자의 명시적인 승인(Approval) 단계를 **생략**하고, 바로 워크플로우를 즉시 자동 실행합니다.

## Workflows

에이전트는 아래 체크리스트와 가이드에 따라 필요한 도구를 직접 호출하여 작업을 수행합니다.

### 1단계: 분석 대상 주간의 날짜 범위 판정
- [ ] **실행 기준일(오늘)을 확인하고 대상 기간(가장 최근 마감된 일요일~토요일) 계산**:
  - 오늘 요일을 파악합니다.
  - **오늘이 일요일인 경우**: `오늘 - 7일(직전 일요일)`부터 `오늘 - 1일(어제 토요일)`까지의 7일간을 분석 대상 기간으로 판정합니다.
  - **오늘이 월요일 ~ 토요일인 경우**: `이번 주 일요일`부터 `이번 주 토요일`까지의 7일간을 분석 대상 기간으로 판정합니다.
  - (예: 오늘이 2026-06-28(일)인 경우 대상 기간은 2026-06-21부터 2026-06-27까지임)
  - 이 기간 동안의 일요일 날짜(시작일)와 토요일 날짜(종료일/기준일)를 YYYY-MM-DD 형식으로 결정합니다.

### 2단계: 일일 보고서 수집 및 파싱
- [ ] **저장 경로 확인**: 쉘 명령어 실행 도구(`run_command` 등)를 통해 `uv run python scripts/get_storage_dir.py` 명령을 실행하여 환경 변수 `STORAGE_DIR` 경로를 획득합니다.
- [ ] **일일 보고서 파일 조회**: 1단계에서 산출된 7일간의 날짜(일요일 ~ 토요일)에 대해 각 날짜별 일일 마크다운 보고서 경로를 구성하여 존재 여부를 확인합니다.
  - 미국 일일 보고서 경로: `STORAGE_DIR/reports/us_market/US_market_daily_report_YYYYMMDD.md`
- [ ] **보고서 내용 읽기**: 파일이 존재하는 일일 보고서들에 대해 파일 읽기 도구(`view_file` 등)를 사용해 내용을 조회합니다.
  - 파일이 없는 날짜(주말, 휴장일 또는 단순 누락)는 요약에서 제외하거나 '일일 보고서 미존재'로 간략히 기재하고 진행합니다.
- [ ] **뉴스 및 분석 정보 요약**: 조회한 일일 보고서들로부터 날짜별 주요 뉴스 목록(한글 번역 및 요약본)과 일일 종합 분석 요점을 추출합니다.

### 3단계: 주간 지수 변동 데이터 조회
- [ ] **주간 지수 변동 분석 획득**: 쉘 명령어 실행 도구(`run_command` 등)를 사용하여 지정된 주간 범위의 역사적 지수 데이터 변동 정보를 조회합니다.
  - 실행 명령어:
    ```bash
    uv run python scripts/query_market.py --action history --tickers ^GSPC,^IXIC,^DJI --start-date [1단계의 시작일 YYYY-MM-DD] --end-date [1단계의 종료일 YYYY-MM-DD]
    ```
  - 출력 결과 중 각 지수별 **`[변동 분석]`** 영역에 출력된 시작일 종가, 종료일 종가 및 변동률 데이터를 파싱하여 기억합니다. (예: `CHANGE: +50.00 (+1.85%)`)

### 4단계: 주간 보고서 마크다운 생성 및 저장
- [ ] **마크다운 파일 생성**: 파일 쓰기 도구(`write_to_file` 등)를 호출하여 `STORAGE_DIR/reports/us_market/US_market_weekly_report_YYYYMMDD.md` (YYYYMMDD는 요약 주의 **토요일** 날짜) 경로에 아래 템플릿 규격에 맞춰 새로운 마크다운 파일을 생성 및 저장합니다.
  - **주간 보고서 템플릿**:
    ```markdown
    # 📢 미국 주식 시장 주간 현황 보고서
    - **분석 기간**: [시작일 YYYY-MM-DD] (일) ~ [종료일 YYYY-MM-DD] (토)
    - **작성 시간 (한국)**: [현재 시간 YYYY-MM-DD (요일)]
    ---

    ### 📊 주간 지수 변동 현황
    - S&P 500: [시작가격] -> [종료가격] 포인트 ([변동률]%)
    - NASDAQ: [시작가격] -> [종료가격] 포인트 ([변동률]%)
    - DOW JONES: [시작가격] -> [종료가격] 포인트 ([변동률]%)

    ---

    ### 📰 일별 주요 뉴스 요약
    - **[날짜] (월)**:
      - [뉴스제목1](URL): 요약 내용
      - [뉴스제목2](URL): 요약 내용
    - **[날짜] (화)**:
      ...
    - **[날짜] (일요일/토요일 및 일일 보고서 미존재 일자)**:
      - 일일 보고서 미존재 (또는 휴장일)

    ---

    ### 💡 주간 종합 분석
    [각 일일 보고서의 종합 분석 내용들을 유기적으로 결합하고 시장 흐름을 요약한 한 주간의 종합 시황 분석 및 향후 전망]
    ```
  - ⚠️ 주의: 텔레그램 등 메신저 연동 시 깨짐 방지를 위해 절대 **표(Table) 서식은 사용하지 마십시오**.

### 5단계: PDF 변환 실행
- [ ] **변환 명령어 실행**: 쉘 명령어 실행 도구(`run_command` 등)를 통해 PDF 변환 스크립트를 구동합니다.
  - 마크다운 경로: `STORAGE_DIR/reports/us_market/US_market_weekly_report_YYYYMMDD.md`
  - PDF 저장 경로: `STORAGE_DIR/reports/us_market/US_market_weekly_report_YYYYMMDD.pdf`
  - 실행 명령어:
    ```bash
    uv run python scripts/markdown_to_pdf.py [마크다운 절대경로] [PDF 절대경로]
    ```

### 6단계: 텔레그램 알림 전송 (Telegram Notification)
- [ ] **메시지 구성**: 생성된 주간 보고서 마크다운 전체 내용 뒤에 파일명 정보를 덧붙여 텔레그램 전송용 메시지를 작성합니다.
  - 메시지 구성 예시:
    ```markdown
    [작성된 마크다운 보고서 전체 내용]

    ---

    ### 📁 생성된 파일
    - **마크다운 보고서**: [파일명.md]
    - **PDF 보고서**: [파일명.pdf]
    ```
  - ⚠️ 중요: 메시지 내용은 HTML 태그를 사용하지 않고 순수 **마크다운(Markdown)** 형식으로 작성하여 인자로 전달해야 합니다. 표(Table) 서식은 절대 사용하지 마십시오.
- [ ] **메시지 전송**: 쉘 명령어 실행 도구(`run_command` 등)를 호출하여 텔레그램 메시지 전송 스크립트를 구동합니다.
  - 실행할 명령어:
    ```bash
    uv run python scripts/send_telegram.py "[구성한 메시지 내용]"
    ```
