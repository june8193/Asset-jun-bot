# -*- coding: utf-8 -*-
"""로깅 설정 모듈의 테스트입니다."""

import logging
from logging.handlers import TimedRotatingFileHandler
import pytest
from asset_jun_bot.logging_config import setup_logging


def test_setup_logging_creates_directory_and_file(tmp_path):
  """setup_logging 호출 시 로그 디렉터리 및 파일이 잘 생성되는지 검증합니다."""
  storage_dir = tmp_path / "storage"
  logs_dir = storage_dir / "logs"
  log_file = logs_dir / "bot.log"

  assert not logs_dir.exists()

  # 로깅 설정 실행
  setup_logging(str(storage_dir))

  assert logs_dir.exists()
  assert logs_dir.is_dir()

  # 로그 파일 생성 여부 확인을 위해 루트 로거로 로그 기록
  root_logger = logging.getLogger()
  root_logger.info("테스트 로그 메시지 - 한글")

  # 파일이 생성되었는지 확인
  assert log_file.exists()

  # 파일에 내용이 기록되었는지 확인
  with open(log_file, "r", encoding="utf-8") as f:
    content = f.read()
  assert "테스트 로그 메시지 - 한글" in content


def test_setup_logging_timed_rotation(tmp_path):
  """setup_logging이 TimedRotatingFileHandler를 올바르게 설정하는지 검증합니다."""
  storage_dir = tmp_path / "storage"
  setup_logging(str(storage_dir))

  root_logger = logging.getLogger()
  file_handlers = [
      h for h in root_logger.handlers if isinstance(h, TimedRotatingFileHandler)
  ]

  assert len(file_handlers) == 1
  handler = file_handlers[0]

  # Daily rotation 설정 값들 확인
  assert handler.when == "MIDNIGHT"  # Python logging 내부적으로 MIDNIGHT로 관리
  assert handler.backupCount == 30
