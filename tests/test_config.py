# -*- coding: utf-8 -*-
"""Config 관련 테스트 모듈입니다."""

import os
import pytest
from src.config import Config


def test_config_missing_telegram_token(monkeypatch):
  """TELEGRAM_BOT_TOKEN이 없을 때 ValueError를 발생하는지 테스트합니다."""
  monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,67890")

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "TELEGRAM_BOT_TOKEN" in str(excinfo.value)


def test_config_missing_allowed_user_ids(monkeypatch):
  """TELEGRAM_ALLOWED_USER_IDS가 없을 때 ValueError를 발생하는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.delenv("TELEGRAM_ALLOWED_USER_IDS", raising=False)

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "TELEGRAM_ALLOWED_USER_IDS" in str(excinfo.value)


def test_config_invalid_allowed_user_ids(monkeypatch):
  """TELEGRAM_ALLOWED_USER_IDS에 숫자가 아닌 값이 있을 때 ValueError를 발생하는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,abc")

  with pytest.raises(ValueError) as excinfo:
    Config.load()
  assert "숫자" in str(excinfo.value) or "invalid" in str(excinfo.value).lower()


def test_config_valid_parsing(monkeypatch):
  """올바른 환경 변수가 있을 때 정상적으로 로드 및 파싱되는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345,67890")
  monkeypatch.delenv("ASSET_MANAGER_API_URL", raising=False)

  config = Config.load()
  assert config.telegram_bot_token == "mock_token"
  assert config.telegram_allowed_user_ids == {12345, 67890}
  # 기본값 확인
  assert config.asset_manager_api_url == "http://localhost:8000"


def test_config_custom_asset_url(monkeypatch):
  """ASSET_MANAGER_API_URL이 지정되었을 때 올바르게 가져오는지 테스트합니다."""
  monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "mock_token")
  monkeypatch.setenv("TELEGRAM_ALLOWED_USER_IDS", "12345")
  monkeypatch.setenv("ASSET_MANAGER_API_URL", "http://my-asset-server:9000")

  config = Config.load()
  assert config.asset_manager_api_url == "http://my-asset-server:9000"
