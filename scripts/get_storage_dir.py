import os
import sys
from dotenv import load_dotenv

def main():
    """STORAGE_DIR 환경 변수 값을 출력합니다."""
    # .env 파일 로드
    load_dotenv()
    
    storage_dir = os.environ.get("STORAGE_DIR")
    if not storage_dir:
        print("Error: STORAGE_DIR 환경 변수가 설정되어 있지 않습니다.", file=sys.stderr)
        sys.exit(1)
    
    # 공백 제거 및 표준 경로 출력
    print(os.path.abspath(storage_dir.strip()))

if __name__ == "__main__":
    main()
