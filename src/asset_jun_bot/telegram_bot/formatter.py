# -*- coding: utf-8 -*-
"""텔레그램 메시지 서식 변환 및 텍스트 이스케이프 유틸리티 모듈입니다.

(renderer.py 모듈로의 하위 호환 re-export를 제공합니다.)
"""

from .renderer import markdown_to_html, remove_markdown_markup, MessageRenderer

__all__ = ["markdown_to_html", "remove_markdown_markup", "MessageRenderer"]
