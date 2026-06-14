# -*- coding: utf-8 -*-
"""설정 관리 모듈입니다."""

import os
from dotenv import load_dotenv


class Config:
  """Asset-jun-bot 설정을 관리하는 클래스입니다."""

  def __init__(
      self,
      telegram_bot_token: str,
      telegram_allowed_user_ids: set[int],
      asset_manager_api_url: str,
      gemini_api_key: str,
      storage_dir: str,
  ):
    """Config 클래스를 초기화합니다.

    Args:
        telegram_bot_token: Telegram 봇 토큰
        telegram_allowed_user_ids: 허용된 사용자 ID 집합
        asset_manager_api_url: AssetManager API 서버 주소
        gemini_api_key: Google Gemini API 키
        storage_dir: 공통 저장소 디렉터리 경로
    """
    self.telegram_bot_token = telegram_bot_token
    self.telegram_allowed_user_ids = telegram_allowed_user_ids
    self.asset_manager_api_url = asset_manager_api_url
    self.gemini_api_key = gemini_api_key
    self.storage_dir = storage_dir

  @classmethod
  def load(cls) -> "Config":
    """환경 변수 및 .env 파일로부터 설정을 로드합니다.

    Returns:
        로드 완료된 Config 객체

    Raises:
        ValueError: 필수 설정 누락 또는 잘못된 형식의 값이 있는 경우
    """
    # .env 파일 로드
    load_dotenv()

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_bot_token:
      raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 필요합니다.")

    allowed_user_ids_str = os.getenv("TELEGRAM_ALLOWED_USER_IDS")
    if not allowed_user_ids_str:
      raise ValueError("TELEGRAM_ALLOWED_USER_IDS 환경변수가 필요합니다.")

    # 사용자 ID 파싱
    telegram_allowed_user_ids = set()
    for item in allowed_user_ids_str.split(","):
      item = item.strip()
      if not item:
        continue
      try:
        telegram_allowed_user_ids.add(int(item))
      except ValueError as exc:
        raise ValueError(
            f"TELEGRAM_ALLOWED_USER_IDS는 숫자 리스트여야 합니다: {item}"
        ) from exc

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
      raise ValueError("GEMINI_API_KEY 환경변수가 필요합니다.")

    storage_dir = os.getenv("STORAGE_DIR")
    if not storage_dir:
      raise ValueError("STORAGE_DIR 환경변수가 필요합니다.")

    asset_manager_api_url = os.getenv(
        "ASSET_MANAGER_API_URL", "http://localhost:8000"
    )

    return cls(
        telegram_bot_token=telegram_bot_token,
        telegram_allowed_user_ids=telegram_allowed_user_ids,
        asset_manager_api_url=asset_manager_api_url,
        gemini_api_key=gemini_api_key,
        storage_dir=storage_dir,
    )
