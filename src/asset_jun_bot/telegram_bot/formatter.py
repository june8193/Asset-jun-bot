# -*- coding: utf-8 -*-
"""텔레그램 메시지 서식 변환 및 텍스트 이스케이프 유틸리티 모듈입니다."""

import re


def markdown_to_html(text: str) -> str:
  """마크다운 텍스트를 텔레그램용 HTML 서식으로 변환합니다.

  Args:
      text: 원본 마크다운 텍스트

  Returns:
      텔레그램 HTML 규격에 맞춰 이스케이프 및 변환된 텍스트
  """
  if not text:
    return ""

  # 1. 텔레그램 필수 HTML 이스케이프 (태그 충돌 방지)
  # &를 가장 먼저 변환하여 &lt; 등의 &가 이중 변환되지 않도록 함
  text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

  # 2. 코드 블록 변환 (```code``` -> <pre>code</pre>)
  text = re.sub(r"```([\s\S]*?)```", r"<pre>\1</pre>", text)

  # 3. 인라인 코드 변환 (`code` -> <code>code</code>)
  text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)

  # 4. 강조 (Bold) 변환
  text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
  text = re.sub(r"\*([^*]+)\*", r"<b>\1</b>", text)

  # 5. 하이퍼링크 변환 ([text](url) -> <a href="url">text</a>)
  text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

  # 6. 블록 인용구 (줄 시작 > 텍스트 -> <blockquote>텍스트</blockquote>)
  # HTML 이스케이프 처리 후 '>'가 '&gt;'로 변경되었으므로 이를 매칭
  text = re.sub(
      r"^\s*&gt;\s*(.*?)$", r"<blockquote>\1</blockquote>", text, flags=re.MULTILINE
  )

  # 7. 헤더 (# 제목 -> <b>제목</b>)
  text = re.sub(r"^\s*#{1,6}\s*(.*?)$", r"<b>\1</b>", text, flags=re.MULTILINE)

  # 8. 수평선 (--- -> ━━━━━━━━━━━━━━━━━━━━)
  text = re.sub(r"^\s*---\s*$", "━━━━━━━━━━━━━━━━━━━━", text, flags=re.MULTILINE)

  return text


def remove_markdown_markup(text: str) -> str:
  """텍스트에서 마크다운 마크업 서식을 지우고 일반 텍스트로 변환합니다.

  Args:
      text: 마크다운 서식이 포함된 원본 텍스트

  Returns:
      서식 마크업이 지워진 순수 일반 텍스트
  """
  if not text:
    return ""

  # 1. 코드블록 마크업 제거
  text = text.replace("```", "")
  # 2. 인라인 코드 마크업 제거
  text = text.replace("`", "")
  # 3. 굵게/강조 마크업 제거
  text = text.replace("**", "").replace("*", "")
  # 4. 링크 마크업 단순화 ([text](url) -> text)
  text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
  # 5. 블록 인용 기호 제거
  text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)
  # 6. 헤더 # 기호 제거
  text = re.sub(r"^\s*#{1,6}\s*", "", text, flags=re.MULTILINE)
  # 7. 수평선 제거
  text = re.sub(r"^\s*---\s*$", "", text, flags=re.MULTILINE)

  return text
