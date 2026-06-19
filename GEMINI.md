# Asset-jun-bot 에이전트 규칙 (GEMINI.md)

이 파일은 `Asset-jun-bot` 프로젝트 개발 시 에이전트(Antigravity)가 항상 준수해야 하는 공통 규칙들을 담고 있습니다.

## 1. 커뮤니케이션 및 문서화 규칙 (언어 정책)
- **기본 언어**: 에이전트의 모든 대답(Reply)과 아티팩트(Artifact) 문서는 항상 **한국어**와 **한글**로 작성합니다.
- **Docstring 및 주석**: 모든 Docstring과 코드 주석은 **한글**로 작성하며, Docstring 스타일은 Google Style을 따릅니다.
- **커밋 메시지**: Git 커밋 메시지는 항상 **한국어**로 작성합니다.

## 2. TDD (Test Driven Development) 규칙
이 프로젝트는 TDD 방식으로 개발합니다. 새로운 기능을 구현하거나 기존 코드를 수정할 때 반드시 아래 절차를 준수합니다.

### 개발 절차
1. **Red**: 실패하는 테스트를 먼저 작성합니다 (`tests/` 디렉토리 아래에 작성).
2. **Green**: 테스트를 통과하는 최소한의 코드를 작성합니다 (`src/` 디렉토리 아래에 작성).
3. **Refactor**: 테스트 통과 상태를 유지하며 코드를 개선(리팩토링)합니다.

### 공통 원칙
- 프로덕션 코드를 작성하기 전에 반드시 해당 기능의 테스트를 먼저 작성합니다.
- 모든 공개(Public) 함수 및 메서드는 최소 하나 이상의 테스트 케이스를 가져야 합니다.
- 버그 수정 시에도 해당 버그를 재현하는 테스트를 먼저 작성한 후 수정을 진행합니다.
- **테스트 격리**: 외부 API 호출(Telegram Bot API, AssetManager API 등)은 테스트 환경에서 실제 호출이 일어나지 않도록 반드시 Mocking(예: `respx`, `pytest-mock` 등)을 사용하여 격리합니다.

## 3. Python 실행 및 패키지 관리 규칙
- **원칙**: 모든 파이썬 스크립트 및 도구 실행 시 반드시 `uv`를 사용합니다.
- **실행 방법**: `uv run <script_path>` 형식을 사용하여 일관된 가상환경 내에서 실행되도록 합니다. (예: `uv run pytest`, `uv run python src/main.py`)

## 4. Shell 명령어 실행 규칙 (OS 및 환경별 대응)
- **Windows PowerShell 환경인 경우**:
  - **리다이렉션**: `2>/dev/null` 대신 `2>$null`을 사용해야 합니다.
  - **연산자**: `&&` 연산자 대신 `;`를 사용하거나 도구 호출을 분리하십시오.
  - **대체 명령어**:
    - `grep` -> `Select-String`
    - `rm -rf` -> `Remove-Item -Recurse -Force`
- **macOS 및 Linux (Bash, Zsh 등) 환경인 경우**:
  - 표준 Unix 계열 명령어와 연산자(`&&`, `2>/dev/null`, `rm -rf`, `grep` 등)를 그대로 사용합니다.
