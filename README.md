# Asset-jun-bot (통합 자산 관리 도우미 텔레그램 봇)

준과 성은 부부의 통합 자산 정보를 조회하고 분석하는 AI 비서 텔레그램 봇 프로젝트입니다.  
Google DeepMind의 `google-antigravity` SDK를 활용하여 대화형 인터페이스를 지원하며, 실시간 자산 관리 정보(AssetManager API)를 호출하여 답변을 제공합니다.

## 개발 환경 요구사항
- Python 3.12 이상
- [uv](https://github.com/astral-sh/uv) (파이썬 패키지 및 가상환경 관리 도구)

## 설치 및 설정

1. **의존성 설치 및 가상환경 설정**
   ```bash
   uv sync
   ```

2. **환경 변수 설정**
   프로젝트 루트에 `.env` 파일을 생성하고 아래 설정을 입력합니다:
   ```env
   TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   TELEGRAM_ALLOWED_USER_IDS="allowed_user_id_1,allowed_user_id_2"
   GEMINI_API_KEY="your_gemini_api_key"
   ASSET_MANAGER_API_URL="http://localhost:8000"
   ```

## 실행 방법

### 1. 로컬 개발 패키지 연동
프로젝트를 개발 모드로 설치하여 CLI 명령어로 직접 호출할 수 있도록 합니다.
```bash
uv pip install -e .
```

### 2. 봇 서버 실행
아래 명령어를 사용하여 텔레그램 봇 서버를 가동합니다.
```bash
uv run asset-jun-bot
```

## 테스트 실행

프로젝트 내 구현된 전체 단위 테스트를 구동하려면 아래 명령을 사용합니다.
```bash
uv run python -m pytest
```
