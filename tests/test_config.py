# -*- coding: utf-8 -*-
"""Config 관련 테스트 모듈입니다."""

import os
import pytest
from asset_jun_bot.config import Config


@pytest.fixture(autouse=True)
def mock_load_dotenv(mocker):
  """load_dotenv가 실제 .env 파일을 로드하지 못하게 모킹하여 테스트 환경을 격리합니다."""
  mocker.patch("asset_jun_bot.config.load_dotenv")


def setup_base_envs(monkeypatch):
  """기본 테스트 환경 변수 세트를 설정합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,67890")
  monkeypatch.setenv("GEMINI_API_KEY", "mock_gemini_key")
  monkeypatch.setenv("STORAGE_DIR", "mock_storage_dir")
  monkeypatch.setenv("MODEL_ROUTER", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_GENERAL_CONVERSATION", "gemini-2.5-flash")
  monkeypatch.setenv("MODEL_ASSET_INQUIRY", "gemini-1.5-flash")


def test_config_missing_telegram_token(monkeypatch):
  """TELEGRAM_BOT_TOKEN이 없을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "TELEGRAM_BOT_TOKEN" in str(excinfo.value)


def test_config_missing_allowed_user_ids(monkeypatch):
  """TELEGRAM_ALLOWED_USER_IDS가 없을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "TELEGRAM_ALLOWED_USER_IDS" in str(excinfo.value)


def test_config_invalid_allowed_user_ids(monkeypatch):
  """TELEGRAM_ALLOWED_USER_IDS에 숫자가 아닌 값이 있을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,abc")

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "숫자" in str(excinfo.value) or "invalid" in str(excinfo.value).lower()


def test_config_missing_gemini_api_key(monkeypatch):
  """GEMINI_API_KEY가 없을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("GEMINI_API_KEY", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "GEMINI_API_KEY" in str(excinfo.value)


def test_config_valid_parsing(monkeypatch):
  """올바른 환경 변수가 있을 때 정상적으로 로드 및 파싱되는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("ASSET_MANAGER_API_URL", raising=False)

  config = Config.load()
  assert config.telegram_bot_token == "mock_token"
  assert config.telegram_allowed_user_ids == {12345, 67890}
  assert config.gemini_api_key == "mock_gemini_key"
  assert config.storage_dir == "mock_storage_dir"
  assert config.model_router == "gemini-2.5-flash"
  assert config.model_general_conversation == "gemini-2.5-flash"
  assert config.model_asset_inquiry == "gemini-1.5-flash"
  # 기본값 확인
  assert config.asset_manager_api_url == "http://localhost:8000"


def test_config_custom_asset_url(monkeypatch):
  """ASSET_MANAGER_API_URL이 지정되었을 때 올바르게 가져오는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://my-asset-server:9000")

  config = Config.load()
  assert config.asset_manager_api_url == "http://my-asset-server:9000"


def test_config_missing_storage_dir(monkeypatch):
  """STORAGE_DIR이 없을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("STORAGE_DIR", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "STORAGE_DIR" in str(excinfo.value)


def test_config_missing_model_router(monkeypatch):
  """MODEL_ROUTER가 없을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("MODEL_ROUTER", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "MODEL_ROUTER" in str(excinfo.value)


def test_config_missing_model_general_conversation(monkeypatch):
  """MODEL_GENERAL_CONVERSATION이 없을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("MODEL_GENERAL_CONVERSATION", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "MODEL_GENERAL_CONVERSATION" in str(excinfo.value)


def test_config_missing_model_asset_inquiry(monkeypatch):
  """MODEL_ASSET_INQUIRY가 없을 때 ValueError를 발생하는지 테스트합니다."""
  setup_base_envs(monkeypatch)
  monkeypatch.delenv("MODEL_ASSET_INQUIRY", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "MODEL_ASSET_INQUIRY" in str(excinfo.value)
