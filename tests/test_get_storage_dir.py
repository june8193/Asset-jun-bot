# -*- coding: utf-8 -*-
"""scripts/get_storage_dir.py 에 대한 테스트 모듈입니다."""

import os
import sys
import pytest
from unittest.mock import patch

# scripts 폴더를 sys.path에 추가하여 직접 임포트할 수 있게 설정
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.get_storage_dir import main


@pytest.fixture(autouse=True)
def mock_load_dotenv(mocker):
    """load_dotenv가 실제 .env 파일을 로드하지 못하게 모킹하여 테스트 환경을 격리합니다."""
    mocker.patch("scripts.get_storage_dir.load_dotenv")


def test_get_storage_dir_success(monkeypatch, capsys):
    """STORAGE_DIR 환경 변수가 설정되어 있을 때 올바른 절대 경로를 출력하는지 검증합니다."""
    test_path = "C:\\test\\storage_dir"
    monkeypatch.setenv("STORAGE_DIR", test_path)

    main()

    captured = capsys.readouterr()
    expected_path = os.path.abspath(test_path)
    assert captured.out.strip() == expected_path
    assert captured.err == ""


def test_get_storage_dir_missing(monkeypatch, capsys):
    """STORAGE_DIR 환경 변수가 없을 때 에러 메시지를 출력하고 SystemExit을 발생하는지 검증합니다."""
    monkeypatch.delenv("STORAGE_DIR", raising=False)

    with pytest.raises(SystemExit) as excinfo:
        main()

    captured = capsys.readouterr()
    assert excinfo.value.code == 1
    assert "STORAGE_DIR 환경 변수가 설정되어 있지 않습니다." in captured.err
