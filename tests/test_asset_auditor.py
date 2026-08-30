# -*- coding: utf-8 -*-
"""asset-auditor 스킬 및 docs/references 공용 경로 무결성 검증 테스트 모듈입니다."""

import os
import pytest


def test_docs_references_structure():
  """docs/references 경로에 필수 공용 레퍼런스 파일들이 위치하고 유효한 내용을 포함하는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  project_root = os.path.abspath(os.path.join(current_dir, ".."))
  references_dir = os.path.join(project_root, "docs", "references")

  principles_md = os.path.join(references_dir, "investment-principles.md")
  index_md = os.path.join(references_dir, "trade-cases-index.md")
  case_md = os.path.join(references_dir, "cases", "001_samsung_hynix_semiconductor_2026.md")

  assert os.path.exists(principles_md), f"투자원칙 파일 없음: {principles_md}"
  assert os.path.exists(index_md), f"매매사례 인덱스 파일 없음: {index_md}"
  assert os.path.exists(case_md), f"매매사례 파일 없음: {case_md}"

  # 내용 무결성 검증
  with open(principles_md, "r", encoding="utf-8") as f:
    principles_content = f.read()
    assert "손절 및 포지션 관리" in principles_content

  with open(index_md, "r", encoding="utf-8") as f:
    index_content = f.read()
    assert "001_samsung_hynix_semiconductor_2026.md" in index_content


def test_asset_auditor_skill_integrity():
  """asset-auditor 스킬 파일이 docs/references 경로를 올바르게 참조하고 스킬 내부 references 디렉터리는 제거되었는지 검증합니다."""
  current_dir = os.path.dirname(os.path.abspath(__file__))
  skill_dir = os.path.abspath(os.path.join(current_dir, "..", ".agents", "skills", "asset-auditor"))

  skill_md = os.path.join(skill_dir, "SKILL.md")
  old_references_dir = os.path.join(skill_dir, "references")

  assert os.path.exists(skill_md), f"asset-auditor SKILL.md 없음: {skill_md}"
  assert not os.path.exists(old_references_dir), f"asset-auditor 내부 references 디렉터리가 여전히 존재함: {old_references_dir}"

  with open(skill_md, "r", encoding="utf-8") as f:
    skill_content = f.read()
    assert "name: asset-auditor" in skill_content
    assert "docs/references/investment-principles.md" in skill_content
    assert "docs/references/trade-cases-index.md" in skill_content
