# -*- coding: utf-8 -*-
"""사용자별 대화 기록을 관리하고 보존 기간이 지난 로그를 자동으로 회전하는 모듈입니다."""

import asyncio
import datetime
import json
import logging
import os
import re

logger = logging.getLogger(__name__)


class ChatHistoryManager:
  """사용자별 대화 기록을 저장하고 60일(설정 가능) 보존 정책을 관리하는 클래스입니다."""

  def __init__(self, storage_dir: str, retention_days: int = 60):
    """ChatHistoryManager를 초기화합니다.

    Args:
        storage_dir: 대화 기록이 저장될 기본 저장소 디렉터리 경로
        retention_days: 대화 내역 보존 기간 (일 단위, 기본값 60일)
    """
    self.storage_dir = storage_dir
    self.retention_days = retention_days
    self.chats_base_dir = os.path.join(storage_dir, "chats")

  async def save_message(
      self,
      user_id: int,
      role: str,
      message: str,
      current_date: datetime.date | None = None,
  ) -> None:
    """사용자의 대화 메시지를 저장하고 오래된 기록을 정리합니다.

    이 작업은 디스크 I/O 블로킹을 방지하기 위해 별도의 스레드 풀에서 비동기로 실행됩니다.

    Args:
        user_id: 텔레그램 사용자 ID
        role: 메시지 발신 주체 ('user' 또는 'bot')
        message: 메시지 본문
        current_date: 처리 기준 날짜 (테스트용, 미지정 시 오늘 날짜 사용)
    """
    if current_date is None:
      current_date = datetime.date.today()

    await asyncio.to_thread(
        self._save_and_clean_sync, user_id, role, message, current_date
    )

  def _save_and_clean_sync(
      self, user_id: int, role: str, message: str, current_date: datetime.date
  ) -> None:
    """대화 기록을 저장하고 60일 지난 로그를 삭제하는 동기식 헬퍼 메서드입니다."""
    user_dir = os.path.join(self.chats_base_dir, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    date_str = current_date.isoformat()
    filepath = os.path.join(user_dir, f"{date_str}.json")

    # 새 메시지 데이터 생성
    # 로컬 시간대에 맞는 타임스탬프 저장
    timestamp = datetime.datetime.now().astimezone().isoformat()
    new_entry = {"timestamp": timestamp, "role": role, "message": message}

    history = []
    if os.path.exists(filepath):
      try:
        with open(filepath, "r", encoding="utf-8") as f:
          content = f.read().strip()
          if content:
            history = json.loads(content)
      except Exception as exc:
        logger.error(
            f"대화 기록 파일 로드 실패 (파일 손상 의심, 새로 생성함): {filepath}, 에러: {exc}"
        )

    history.append(new_entry)

    try:
      with open(filepath, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as exc:
      logger.error(f"대화 기록 저장 실패: {filepath}, 에러: {exc}")

    # 오래된 파일 정리
    self._clean_old_history_sync(user_id, current_date)

  def _clean_old_history_sync(
      self, user_id: int, current_date: datetime.date
  ) -> None:
    """해당 사용자 디렉터리 내의 60일이 지난 일별 JSON 파일을 삭제합니다."""
    user_dir = os.path.join(self.chats_base_dir, str(user_id))
    if not os.path.exists(user_dir):
      return

    # YYYY-MM-DD.json 형식 매칭용 정규식
    date_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")

    try:
      for filename in os.listdir(user_dir):
        match = date_pattern.match(filename)
        if not match:
          continue

        file_date_str = match.group(1)
        try:
          file_date = datetime.date.fromisoformat(file_date_str)
        except ValueError:
          # 유효하지 않은 날짜인 경우 건너뜀
          continue

        # 날짜 차이 계산
        delta = current_date - file_date
        if delta.days > self.retention_days:
          filepath = os.path.join(user_dir, filename)
          try:
            os.remove(filepath)
            logger.info(
                f"보존 기간 경과로 대화 기록 파일 삭제 완료: {filepath} ({delta.days}일 경과)"
            )
          except Exception as exc:
            logger.error(f"만료된 대화 파일 삭제 실패: {filepath}, 에러: {exc}")
    except Exception as exc:
      logger.error(
          f"사용자 {user_id}의 오래된 대화 기록 스캔 실패, 에러: {exc}"
      )
