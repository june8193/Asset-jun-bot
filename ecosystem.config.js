module.exports = {
  apps: [
    {
      name: "asset-jun-bot",
      // 실행할 파이썬 진입점 스크립트
      script: "src/asset_jun_bot/main.py",
      
      // uv sync를 통해 생성된 로컬 가상환경(.venv)의 Python 인터프리터 경로를 지정합니다.
      // - macOS / Linux: "./.venv/bin/python"
      // - Windows: ".\\.venv\\Scripts\\python.exe" (또는 실행 환경에 맞는 백슬래시 표기)
      interpreter: "./.venv/bin/python",
      
      // 작업 디렉터리 경로
      cwd: "./",
      
      // 단일 인스턴스 구동 모드
      instances: 1,
      exec_mode: "fork",
      
      // 프로세스 다운 시 자동 재시작 활성화
      autorestart: true,
      
      // 코드 수정 실시간 감시 (상용/서버 환경의 안정성을 위해 기본값 false 설정)
      watch: false,
      
      // 봇 서버의 예기치 못한 메모리 누수 대비 (250MB 초과 시 자동 재시작)
      max_memory_restart: "250M",
      
      // 환경 변수 설정
      env: {
        NODE_ENV: "production",
        PYTHONUTF8: "1" // Windows 환경 등에서 터미널 및 파이썬 한글 출력 깨짐을 방지
      },
      
      // 로그 설정: 앱 내에 자체 회전(Rotation) 로그 시스템이 구축되어 있으므로,
      // PM2 단에서 콘솔 출력을 캡처하여 디스크 파일에 중복 기록하지 않도록 설정합니다.
      // - macOS / Linux: "/dev/null"
      // - Windows: "NUL"
      error_file: "/dev/null",
      out_file: "/dev/null",
      
      // 비정상 종료 후 재시작될 때 지연 시간(ms)을 주어 무한 재시작 루프에 따른 CPU 점유 방지
      restart_delay: 3000
    }
  ]
};
