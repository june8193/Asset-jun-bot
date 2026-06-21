---
name: us-daily-index-report
description: Generate, save, and convert the daily S&P 500/NASDAQ/DOW index status report into Markdown and PDF formats by executing local APIs, yfinance news retrieval, file writes, and shell commands. Use when executing scheduled report tasks, or when generating daily market index briefings.
---

# 미국 시장 일일 지수 현황 보고서 작성 (US Daily Index Report)

이 스킬은 예약된 시간에 에이전트가 직접 도구(Tools)를 체인으로 호출하여 미국 시장(S&P 500, NASDAQ, DOW JONES)의 지수를 수집하고, yfinance를 통해 당일 영문 뉴스를 검색한 뒤 한글로 번역 및 요약하여 종합 마크다운 보고서를 작성하고, PDF로 변환하여 지정된 저장 공간에 보관합니다.

## Quick start

이 스킬이 로드되면 에이전트는 별도의 조작 없이 아래의 **Workflows** 절차에 명시된 도구들을 순서대로 사용하여 보고서 작성 및 변환을 완료해야 합니다.

⚠️ **계획 모드(Planning Mode) 및 승인 생략**: 이 스킬을 가동할 때는 구현 계획서(Implementation Plan, `implementation_plan.md`) 작성 및 사용자의 명시적인 승인(Approval) 단계를 **생략**하고, 바로 워크플로우를 즉시 자동 실행합니다.

## Workflows

에이전트는 아래 체크리스트와 가이드에 따라 필요한 도구를 직접 호출하여 작업을 수행합니다.

### 0단계: 주말 및 휴장일 여부 확인 (Pre-check)
- [ ] **휴장일 판정 스크립트 실행**: 쉘 명령어 실행 도구(`run_command` 등)를 통해 `uv run python scripts/query_market.py --action holiday --country US` 명령을 실행하여 미국 시장 휴장일 정보(DATE, COUNTRY, IS_HOLIDAY, DESCRIPTION)를 확인합니다.
- [ ] **휴장일 상태 정보 보존**: `IS_HOLIDAY` 값과 `DESCRIPTION` 값을 기억하여 이후 단계에서 분기 처리에 활용합니다. (주말이나 휴장일이라 하더라도 작업을 중단하지 않고 다음 단계를 계속 진행합니다.)

### 1단계: 지수 데이터 및 뉴스 수집
- [ ] **지수 데이터 조회 선택**:
  - `IS_HOLIDAY`가 `False`인 경우(정상 영업일): 쉘 명령어 실행 도구(`run_command` 등)를 통해 `uv run python scripts/query_market.py --action indices --country US` 명령을 실행하여 오늘 마감된 미국 3대 지수(S&P 500, NASDAQ, DOW JONES) 데이터를 획득합니다.
  - `IS_HOLIDAY`가 `True`인 경우(휴장일/주말): 지수 조회 명령을 **생략**합니다.
- [ ] **시장 뉴스 검색**: 평일, 휴장일 여부와 무관하게 쉘 명령어 실행 도구(`run_command` 등)를 통해 전용 CLI 스크립트(`uv run python scripts/query_us_news.py --limit 5`)를 실행하여 yfinance 상의 최신 미국 뉴스를 수집합니다. (※ 이 스크립트는 본문 없이 뉴스 제목, 링크, 언론사 정보만 반환하므로, 상세 요약을 위해서는 추가 검색 도구나 웹 조회 도구를 활용할 수 있습니다.)
- [ ] **영문 뉴스 AI 번역 및 요약**: 수집된 영문 뉴스 리스트를 Gemini 모델(자기 자신)을 통해 자연스러운 한국어로 번역하고 핵심 내용을 간략하게 요약합니다.

### 2단계: 마크다운 파일 생성 및 저장
- [ ] **저장 경로 확인**: 저장할 디렉터리 경로를 획득하기 위해 쉘 명령어 실행 도구(`run_command` 등)를 통해 `uv run python scripts/get_storage_dir.py` 명령을 실행하여 환경 변수 값을 확인합니다.
- [ ] **마크다운 파일 생성 및 저장**: 파일 쓰기 도구(`write_to_file` 등)를 호출하여 `STORAGE_DIR/reports/us_market/US_market_daily_report_YYYYMMDD.md` (YYYYMMDD는 오늘 날짜) 경로에 아래 템플릿 규격에 맞춘 새로운 마크다운 파일을 직접 생성하여 저장합니다.
  - **보고서 템플릿**:
    - **평일 (is_holiday=false)인 경우**:
      ```markdown
      # 📢 미국 주식 시장 일일 현황 보고서 (YYYY-MM-DD)
      ---

      ### 📊 지수 현황
      - S&P 500: [S&P 500지수] 포인트 ([등락률]%)
      - NASDAQ: [NASDAQ지수] 포인트 ([등락률]%)
      - DOW JONES: [DOW JONES지수] 포인트 ([등락률]%)

      ---

      ### 📰 주요 뉴스 (AI 번역 및 요약)
      - [뉴스제목1](URL): 요약 내용
      - [뉴스제목2](URL): 요약 내용
      ...

      ---

      ### 💡 종합 분석
      [지수 흐름과 뉴스를 결합한 분석 및 AI 전망]
      ```
    - **휴장일 (is_holiday=true)인 경우**:
      ```markdown
      # 📢 미국 주식 시장 일일 현황 보고서 (YYYY-MM-DD)
      ---

      ### 📊 지수 현황
      - 금일은 미국 주식 시장 휴장일(사유: [description])로 인해 지수 정보가 제공되지 않습니다.

      ---

      ### 📰 주요 뉴스 (AI 번역 및 요약)
      - [뉴스제목1](URL): 요약 내용
      - [뉴스제목2](URL): 요약 내용
      ...

      ---

      ### 💡 종합 분석
      [휴장일 뉴스 흐름 분석 및 향후 전망]
      ```
  - ⚠️ 주의: 텔레그램 등 메신저 연동 시 깨짐 방지를 위해 절대 **표(Table) 서식은 사용하지 마십시오**.

### 3단계: PDF 변환 실행
- [ ] **명령어 준비**: 저장한 마크다운 파일 경로와 저장할 PDF 파일 경로를 식별합니다.
  - 마크다운 경로: `STORAGE_DIR/reports/us_market/US_market_daily_report_YYYYMMDD.md`
  - PDF 저장 경로: `STORAGE_DIR/reports/us_market/US_market_daily_report_YYYYMMDD.pdf`
- [ ] **명령 실행**: 쉘 명령어 실행 도구(`run_command` 등)를 호출하여 PDF 변환 스크립트를 직접 구동합니다.
  - 실행할 명령어:
    ```bash
    uv run python scripts/markdown_to_pdf.py [마크다운 절대경로] [PDF 절대경로]
    ```
- [ ] **완료 검증**: 변환이 성공적으로 끝났는지 로그 출력을 통해 검증합니다.

### 4단계: 텔레그램 알림 전송 (Telegram Notification)
- [ ] **메시지 구성**: 생성된 마크다운 보고서 전체 내용 뒤에 생성된 파일명(마크다운, PDF) 정보를 덧붙여 텔레그램 메시지를 구성합니다.
  - 메시지 구성 예시:
    ```markdown
    [작성된 마크다운 보고서 전체 내용]

    ---

    ### 📁 생성된 파일
    - **마크다운 보고서**: [파일명]
    - **PDF 보고서**: [파일명]
    ```
  - ⚠️ 중요: 메시지 내용은 HTML 태그를 사용하지 않고 순수 **마크다운(Markdown)** 형식으로 작성하여 인자로 전달해야 합니다. 내부 전송 API가 마크다운을 자동으로 HTML로 변환하여 전송합니다. 또한 텔레그램 메시지에서는 표(Table) 서식이 깨지므로 절대 사용하지 마십시오.
- [ ] **메시지 전송**: 쉘 명령어 실행 도구(`run_command` 등)를 호출하여 텔레그램 메시지 전송 스크립트를 구동합니다.
  - 실행할 명령어:
    ```bash
    uv run python scripts/send_telegram.py "[구성한 메시지 내용]"
    ```
- [ ] **완료 검증**: 전송이 성공적으로 끝났는지 로그 출력("Telegram message sent successfully...")을 통해 검증합니다.
