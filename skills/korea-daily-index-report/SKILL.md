---
name: korea-daily-index-report
description: Generate, save, and convert the daily KOSPI/KOSDAQ index status report into Markdown and PDF formats by executing local APIs, web searches, file writes, and shell commands. Use when executing scheduled report tasks, or when generating daily market index briefings.
---

# 국내 시장 일일 지수 현황 보고서 작성 (Korea Daily Index Report)

이 스킬은 예약된 시간에 에이전트가 직접 도구(Tools)를 체인으로 호출하여 국내 시장(KOSPI, KOSDAQ)의 지수를 수집하고, 당일 뉴스를 검색해 종합 마크다운 보고서를 작성한 뒤, PDF로 변환하여 지정된 저장 공간에 보관합니다.

## Quick start

이 스킬이 로드되면 에이전트는 별도의 조작 없이 아래의 **Workflows** 절차에 명시된 도구들을 순서대로 사용하여 보고서 작성 및 변환을 완료해야 합니다.

## Workflows

에이전트는 아래 체크리스트와 가이드에 따라 필요한 도구를 직접 호출하여 작업을 수행합니다.

### 0단계: 주말 및 휴장일 여부 확인 (Pre-check)
- [ ] **휴장일 판정 API 호출**: `check_market_holiday(country="KR")` 도구를 호출하여 오늘 날짜의 한국 시장 휴장일 정보(date, country, is_holiday, description)를 조회합니다.
  - 만약 반환된 `is_holiday` 값이 `true`인 경우, 에이전트는 즉시 작업을 중단하고 "금일은 한국 주식 시장 휴장일(사유: [description])이므로 보고서 작성을 생략합니다." 라는 메시지와 함께 작업을 성공적으로 마칩니다.
- [ ] **수행 승인**: 반환된 `is_holiday` 값이 `false`인 정상 영업일임이 확인된 경우에만 아래 1단계로 진입합니다.

### 1단계: 지수 데이터 및 뉴스 수집
- [ ] **지수 데이터 조회**: `get_market_indices` 도구를 호출하여 오늘 마감된 KOSPI 및 KOSDAQ 지수와 전일비 등락률 데이터를 획득합니다.
- [ ] **시장 뉴스 웹 검색**: 기본 웹 검색 도구(`search_web` 등)를 사용하여 오늘 KOSPI 및 KOSDAQ 시장에 영향을 준 주요 경제 뉴스 3~5개를 조사합니다.
- [ ] **뉴스 링크 확보**: 조사한 각 뉴스 기사는 제목 옆에 반드시 해당 기사의 **URL 출처 링크**([뉴스 제목](URL))를 기재해야 합니다.

### 2단계: 마크다운 파일 저장
- [ ] **저장 파일명**: 오늘 날짜를 기준으로 파일명을 결정합니다. (형식: `Korea_market_daily_report_YYYYMMDD.md`)
- [ ] **저장 경로**: 환경 변수 `STORAGE_DIR`에서 값을 읽어와 `STORAGE_DIR/reports/korea_market/` 폴더 하위에 저장합니다.
- [ ] **파일 생성**: 파일 쓰기 도구(`write_to_file` 등)를 호출하여 아래 템플릿 규격에 맞춰 마크다운 파일을 생성합니다.
  - **보고서 템플릿**:
    ```markdown
    # 국내 주식 시장 일일 현황 보고서 (YYYY-MM-DD)

    ### 지수 현황
    - KOSPI: [코스피지수] 포인트 ([등락률]%)
    - KOSDAQ: [코스닥지수] 포인트 ([등락률]%)

    ### 주요 뉴스
    - [뉴스제목1](URL): 요약 내용
    - [뉴스제목2](URL): 요약 내용
    ...

    ### 종합 분석
    [지수 흐름과 뉴스를 결합한 분석 및 AI 전망]
    ```
  - ⚠️ 주의: 텔레그램 등 메신저 연동 시 깨짐 방지를 위해 절대 **표(Table) 서식은 사용하지 마십시오**.

### 3단계: PDF 변환 실행
- [ ] **명령어 준비**: 저장한 마크다운 파일 경로와 저장할 PDF 파일 경로를 식별합니다.
  - 마크다운 경로: `STORAGE_DIR/reports/korea_market/Korea_market_daily_report_YYYYMMDD.md`
  - PDF 저장 경로: `STORAGE_DIR/reports/korea_market/Korea_market_daily_report_YYYYMMDD.pdf`
- [ ] **명령 실행**: 쉘 명령어 실행 도구(`run_command` 등)를 호출하여 PDF 변환 스크립트를 직접 구동합니다.
  - 실행할 명령어:
    ```bash
    uv run python scripts/markdown_to_pdf.py [마크다운 절대경로] [PDF 절대경로]
    ```
- [ ] **완료 검증**: 변환이 성공적으로 끝났는지 로그 출력을 통해 검증합니다.
