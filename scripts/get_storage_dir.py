import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    """STORAGE_DIR 환경 변수 값을 운영체제에 호환되는 절대 경로로 변환하여 출력합니다."""
    # .env 파일 로드
    load_dotenv()
    
    storage_dir = os.environ.get("STORAGE_DIR")
    if not storage_dir:
        print("Error: STORAGE_DIR 환경 변수가 설정되어 있지 않습니다.", file=sys.stderr)
        sys.exit(1)
    
    # pathlib.Path를 사용해 틸다(~) 확장, 절대 경로 해소 및 OS별 경로 구분자 자동 정규화
    resolved_path = Path(storage_dir.strip()).expanduser().resolve()
    print(str(resolved_path))

if __name__ == "__main__":
    main()
