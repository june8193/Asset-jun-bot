# -*- coding: utf-8 -*-
"""ChatHistoryManager 테스트 모듈입니다."""

import asyncio
import datetime
import json
import os
import pytest
from asset_jun_bot.chat_history_manager import ChatHistoryManager


def test_save_message_creates_file(tmp_path):
  """대화 메시지를 저장할 때 올바른 디렉터리와 파일이 생성되는지 테스트합니다.

  Args:
      tmp_path: pytest가 제공하는 임시 디렉터리 경로
  """
  storage_dir = str(tmp_path)
  manager = ChatHistoryManager(storage_dir=storage_dir)

  # 테스트용 날짜 고정
  fixed_date = datetime.date(2026, 6, 14)
  user_id = 12345

  # 첫 번째 메시지 저장
  asyncio.run(
      manager.save_message(
          user_id=user_id,
          role="user",
          message="안녕하세요",
          current_date=fixed_date,
      )
  )

  # 파일이 생성되었는지 검증
  expected_dir = os.path.join(storage_dir, "chats", str(user_id))
  expected_file = os.path.join(expected_dir, "2026-06-14.json")
  assert os.path.exists(expected_file)

  # 파일 내용 확인
  with open(expected_file, "r", encoding="utf-8") as f:
    data = json.load(f)

  assert len(data) == 1
  assert data[0]["role"] == "user"
  assert data[0]["message"] == "안녕하세요"
  assert "timestamp" in data[0]

  # 두 번째 메시지 저장 (동일 날짜)
  asyncio.run(
      manager.save_message(
          user_id=user_id,
          role="bot",
          message="반갑습니다",
          current_date=fixed_date,
      )
  )

  with open(expected_file, "r", encoding="utf-8") as f:
    data = json.load(f)

  assert len(data) == 2
  assert data[1]["role"] == "bot"
  assert data[1]["message"] == "반갑습니다"


def test_clean_old_history(tmp_path):
  """60일이 경과한 오래된 로그 파일만 삭제(회전)되는지 테스트합니다.

  Args:
      tmp_path: pytest가 제공하는 임시 디렉터리 경로
  """
  storage_dir = str(tmp_path)
  # 보존 기간을 60일로 설정
  manager = ChatHistoryManager(storage_dir=storage_dir, retention_days=60)

  user_id = 99999
  user_chat_dir = os.path.join(storage_dir, "chats", str(user_id))
  os.makedirs(user_chat_dir, exist_ok=True)

  # 기준 날짜: 2026-06-14
  base_date = datetime.date(2026, 6, 14)

  # 1. 60일 이전의 과거 파일 생성 (삭제 대상)
  # 2026-06-14 - 61일 = 2026-04-14
  old_date_str = "2026-04-14"
  old_file_path = os.path.join(user_chat_dir, f"{old_date_str}.json")
  with open(old_file_path, "w", encoding="utf-8") as f:
    json.dump([{"timestamp": "2026-04-14T12:00:00+09:00", "role": "user", "message": "옛날 메시지"}], f)

  # 2. 60일 이내의 파일 생성 (보존 대상)
  # 2026-06-14 - 59일 = 2026-04-16
  keep_date_str = "2026-04-16"
  keep_file_path = os.path.join(user_chat_dir, f"{keep_date_str}.json")
  with open(keep_file_path, "w", encoding="utf-8") as f:
    json.dump([{"timestamp": "2026-04-16T12:00:00+09:00", "role": "user", "message": "유지할 메시지"}], f)

  # 3. 신규 메시지 저장 (트리거)
  asyncio.run(
      manager.save_message(
          user_id=user_id,
          role="user",
          message="오늘 메시지",
          current_date=base_date,
      )
  )

  # 4. 검증:
  # - 61일 전 파일(2026-04-14.json)은 삭제되어야 함.
  # - 59일 전 파일(2026-04-16.json)은 남아 있어야 함.
  # - 오늘 자 파일(2026-06-14.json)은 생성되어 있어야 함.
  assert not os.path.exists(old_file_path)
  assert os.path.exists(keep_file_path)
  assert os.path.exists(os.path.join(user_chat_dir, "2026-06-14.json"))
