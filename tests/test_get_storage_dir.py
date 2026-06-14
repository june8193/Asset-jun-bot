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


def test_get_storage_dir_windows(monkeypatch, capsys, mocker):
    """Windows 환경일 때 STORAGE_DIR_WINDOWS 환경 변수를 우선 채택하는지 검증합니다."""
    mocker.patch("platform.system", return_value="Windows")
    
    test_path_win = "C:\\test\\win_storage"
    test_path_mac = "/Users/test/mac_storage"
    
    monkeypatch.setenv("STORAGE_DIR_WINDOWS", test_path_win)
    monkeypatch.setenv("STORAGE_DIR_MAC", test_path_mac)
    
    main()
    
    captured = capsys.readouterr()
    assert captured.out.strip() == os.path.abspath(test_path_win)
    assert captured.err == ""


def test_get_storage_dir_mac(monkeypatch, capsys, mocker):
    """macOS (Darwin) 환경일 때 STORAGE_DIR_MAC 환경 변수를 우선 채택하는지 검증합니다."""
    mocker.patch("platform.system", return_value="Darwin")
    
    test_path_win = "C:\\test\\win_storage"
    test_path_mac = "~/mac_storage"  # 틸다 포함 경로 테스트
    
    monkeypatch.setenv("STORAGE_DIR_WINDOWS", test_path_win)
    monkeypatch.setenv("STORAGE_DIR_MAC", test_path_mac)
    
    main()
    
    captured = capsys.readouterr()
    expected_path = os.path.abspath(os.path.expanduser(test_path_mac))
    assert captured.out.strip() == expected_path
    assert captured.err == ""


def test_get_storage_dir_fallback(monkeypatch, capsys, mocker):
    """OS 전용 환경 변수가 없으면 공통 STORAGE_DIR 변수로 폴백하는지 검증합니다."""
    mocker.patch("platform.system", return_value="Darwin")
    
    test_path_common = "/Users/test/common_storage"
    monkeypatch.delenv("STORAGE_DIR_MAC", raising=False)
    monkeypatch.setenv("STORAGE_DIR", test_path_common)
    
    main()
    
    captured = capsys.readouterr()
    assert captured.out.strip() == os.path.abspath(test_path_common)
    assert captured.err == ""


def test_get_storage_dir_missing(monkeypatch, capsys, mocker):
    """모든 환경 변수가 설정되어 있지 않을 때 오류 메시지를 출력하고 SystemExit을 발생하는지 검증합니다."""
    mocker.patch("platform.system", return_value="Windows")
    monkeypatch.delenv("STORAGE_DIR_WINDOWS", raising=False)
    monkeypatch.delenv("STORAGE_DIR", raising=False)
    
    with pytest.raises(SystemExit) as excinfo:
        main()
        
    captured = capsys.readouterr()
    assert excinfo.value.code == 1
    assert "STORAGE_DIR 환경 변수가 설정되어 있지 않습니다." in captured.err
