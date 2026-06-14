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

---

## 아키텍처 및 소스 코드 탐색 가이드

### 1. 시스템 아키텍처
Asset-jun-bot은 다음과 같은 흐름으로 사용자의 요청을 처리하고 자산 정보를 조회합니다.

```mermaid
graph TD
    User(["사용자 (Telegram)"]) <--> TelegramBot["telegram_bot.py"]
    TelegramBot <--> ChatHistory["chat_history_manager.py"]
    TelegramBot <--> AgentRunner["agent_runner.py"]
    AgentRunner <--> GeminiAPI["Gemini API (Antigravity SDK)"]
    AgentRunner <--> AssetClient["asset_client.py"]
    AssetClient <--> AssetManagerAPI[(AssetManager API Server)]
```

---

### 2. 프로젝트 디렉터리 구조
코드 검토가 필요할 때 각 기능이 구현된 파일들의 위치는 다음과 같습니다.

* **[src/asset_jun_bot/](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot)**
  * [main.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/main.py): 애플리케이션 진입점. 설정을 초기화하고 텔레그램 봇을 구동합니다.
  * [telegram_bot.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/telegram_bot.py): 텔레그램 API 연동 및 메시지 송수신 루프를 제어합니다.
  * [agent_runner.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/agent_runner.py): Google Antigravity 에이전트를 정의하고, 에이전트가 활용할 도구(Tool) 및 페르소나 지침을 구성합니다.
  * [asset_client.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/asset_client.py): `AssetManager API`와 연동하여 실시간 자산 데이터를 가져오는 HTTP 클라이언트입니다.
  * [chat_history_manager.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/chat_history_manager.py): 대화 기록을 유저별 파일로 안전하게 관리하며, 60일이 지난 오래된 데이터를 자동 정리합니다.
  * [config.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/config.py): 로컬 환경 변수(`.env`) 로드 및 설정 정의 파일입니다.
  * [logging_config.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/logging_config.py): 로그 파일 크기 회전(Rotation)을 관리하는 로거 설정입니다.
* **[tests/](file:///c:/localrepo/Asset-jun-bot/tests)**
  * 프로젝트의 TDD 단위 테스트 코드 모음입니다.

---

### 3. 검토 목적별 탐색 경로

| 검토 및 수정하고자 하는 내용 | 찾아가야 할 파일 위치 |
| :--- | :--- |
| **텔레그램 메시지 송수신 로직 및 사용자 차단/인증** | [telegram_bot.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/telegram_bot.py) |
| **AI의 대답 스타일 변경 및 시스템 지침(Prompt) 수정** | [agent_runner.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/agent_runner.py) |
| **AssetManager API 연동 로직 및 호출 엔드포인트 수정** | [asset_client.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/asset_client.py) |
| **대화 히스토리 저장 및 보존 기간(60일) 규칙 변경** | [chat_history_manager.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/chat_history_manager.py) |
| **환경 변수 추가 및 기본 설정 항목 수정** | [config.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/config.py) |
| **로그 저장 폴더 경로 및 파일 회전 용량 설정 변경** | [logging_config.py](file:///c:/localrepo/Asset-jun-bot/src/asset_jun_bot/logging_config.py) |

