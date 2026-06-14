# -*- coding: utf-8 -*-
"""로깅 설정을 관리하는 모듈입니다."""

import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys


def setup_logging(storage_dir: str) -> None:
  """로깅 설정을 구성합니다.

  지정된 저장소 경로 하위에 'logs' 디렉터리를 생성하고,
  콘솔과 파일(Daily Rotation, 최대 30일 보존)로 로그가 출력되도록 구성합니다.

  Args:
      storage_dir: 로그가 저장될 기본 저장소 경로
  """
  # 1. logs 폴더 경로 생성
  logs_dir = os.path.join(storage_dir, "logs")
  os.makedirs(logs_dir, exist_ok=True)

  log_filepath = os.path.join(logs_dir, "bot.log")

  # 2. 루트 로거 획득 및 설정
  logger = logging.getLogger()
  logger.setLevel(logging.INFO)

  # 포맷터 정의
  formatter = logging.Formatter(
      "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  )

  # Stream 핸들러 (콘솔 출력용)
  stream_handler = logging.StreamHandler(sys.stdout)
  stream_handler.setFormatter(formatter)

  # TimedRotatingFileHandler (매일 자정에 로그 파일 교체, 최대 30일 보존)
  file_handler = TimedRotatingFileHandler(
      filename=log_filepath,
      when="midnight",
      interval=1,
      backupCount=30,
      encoding="utf-8",
  )
  file_handler.setFormatter(formatter)

  # 기존 핸들러들 제거 후 추가 (중복 방지)
  logger.handlers.clear()
  logger.addHandler(stream_handler)
  logger.addHandler(file_handler)
