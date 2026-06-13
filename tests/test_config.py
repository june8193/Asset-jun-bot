# -*- coding: utf-8 -*-
"""Config 관련 테스트 모듈입니다."""

import os
import pytest
from src.config import Config


@pytest.fixture(autouse=True)
def mock_load_dotenv(mocker):
  """load_dotenv가 실제 .env 파일을 로드하지 못하게 모킹하여 테스트 환경을 격리합니다."""
  mocker.patch("src.config.load_dotenv")


def test_config_missing_telegram_token(monkeypatch):
  """TELEGRAM_BOT_TOKEN이 없을 때 ValueError를 발생하는지 테스트합니다."""
  monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,67890")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "TELEGRAM_BOT_TOKEN" in str(excinfo.value)


def test_config_missing_allowed_user_ids(monkeypatch):
  """TELEGRAM_ALLOWED_USER_IDS가 없을 때 ValueError를 발생하는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "TELEGRAM_ALLOWED_USER_IDS" in str(excinfo.value)


def test_config_invalid_allowed_user_ids(monkeypatch):
  """TELEGRAM_ALLOWED_USER_IDS에 숫자가 아닌 값이 있을 때 ValueError를 발생하는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,abc")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "숫자" in str(excinfo.value) or "invalid" in str(excinfo.value).lower()


def test_config_missing_gemini_api_key(monkeypatch):
  """GEMINI_API_KEY가 없을 때 ValueError를 발생하는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.delenv("GEMINI_API_KEY", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "GEMINI_API_KEY" in str(excinfo.value)


def test_config_valid_parsing(monkeypatch):
  """올바른 환경 변수가 있을 때 정상적으로 로드 및 파싱되는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,67890")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.delenv("ASSET_MANAGER_API_URL", raising=False)

  config = Config.load()
  assert config.telegram_bot_token == "mock_token"
  assert config.telegram_allowed_user_ids == {12345, 67890}
  assert config.gemini_api_key == "mock_gemini_key"
  # 기본값 확인
  assert config.asset_manager_api_url == "http://localhost:8000"


def test_config_custom_asset_url(monkeypatch):
  """ASSET_MANAGER_API_URL이 지정되었을 때 올바르게 가져오는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://my-asset-server:9000")

  config = Config.load()
  assert config.asset_manager_api_url == "http://my-asset-server:9000"
