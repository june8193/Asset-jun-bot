import os
import sys
import platform
from dotenv import load_dotenv

def main():
    """OS 환경에 맞춰 STORAGE_DIR 환경 변수 값을 출력합니다."""
    # .env 파일 로드
    load_dotenv()
    
    current_os = platform.system()
    
    # 1. OS별 전용 환경 변수 확인
    if current_os == "Windows":
        storage_dir = os.environ.get("STORAGE_DIR_WINDOWS")
    elif current_os == "Darwin":  # macOS
        storage_dir = os.environ.get("STORAGE_DIR_MAC")
    else:
        storage_dir = None
        
    # 2. 전용 변수가 없을 경우 공통 변수 폴백
    if not storage_dir:
        storage_dir = os.environ.get("STORAGE_DIR")
        
    if not storage_dir:
        print(f"Error: {current_os} 환경을 위한 STORAGE_DIR 환경 변수가 설정되어 있지 않습니다.", file=sys.stderr)
        sys.exit(1)
    
    # 공백 제거, 틸다(~) 확장 및 절대 경로 변환
    resolved_path = os.path.abspath(os.path.expanduser(storage_dir.strip()))
    print(resolved_path)

if __name__ == "__main__":
    main()
