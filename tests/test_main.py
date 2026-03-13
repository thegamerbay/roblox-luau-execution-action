import os
import sys
import json
import urllib.error
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to sys.path to import main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import main

@pytest.fixture
def mock_env(monkeypatch, tmp_path):
    """Fixture for setting up the environment: fake files and environment variables."""
    place_file = tmp_path / "dist.rbxl"
    place_file.write_text("fake place content", encoding="utf-8")

    script_file = tmp_path / "runTests.luau"
    script_file.write_text("print('Hello Luau')", encoding="utf-8")

    github_output = tmp_path / "github_output.txt"

    monkeypatch.setenv("INPUT_API_KEY", "fake_roblox_key")
    monkeypatch.setenv("INPUT_UNIVERSE_ID", "12345")
    monkeypatch.setenv("INPUT_PLACE_ID", "67890")
    monkeypatch.setenv("INPUT_PLACE_FILE", str(place_file))
    monkeypatch.setenv("INPUT_SCRIPT_FILE", str(script_file))
    monkeypatch.setenv("INPUT_PUBLISH", "false")
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output))

    return {
        "place_file": place_file,
        "script_file": script_file,
        "github_output": github_output
    }

def create_mock_response(json_data):
    """Helper to create a fake response from urllib.request.urlopen."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(json_data).encode('utf-8')
    mock_resp.__enter__.return_value = mock_resp
    return mock_resp

@patch("urllib.request.urlopen")
@patch("time.sleep", return_value=None) # Remove polling delay
def test_main_success(mock_sleep, mock_urlopen, mock_env):
    """Successful execution scenario: upload -> task -> wait -> logs."""
    # Configure API response mock sequence
    mock_urlopen.side_effect = [
        create_mock_response({"versionNumber": 42}), # Upload response
        create_mock_response({"path": "task-123"}),  # Create Task response
        create_mock_response({"state": "PROCESSING"}), # Polling 1
        create_mock_response({"state": "COMPLETE"}),   # Polling 2
        create_mock_response({                         # Logs response
            "luauExecutionSessionTaskLogs": [
                {"messages": ["Test Passed", "100% coverage"]}
            ]
        })
    ]

    main.main()

    # Verify that GITHUB_OUTPUT was written out correctly (multiline format)
    output_content = mock_env["github_output"].read_text(encoding="utf-8")
    assert "task_status<<EOF\nCOMPLETE\nEOF" in output_content
    assert "task_logs<<EOF\nTest Passed\n100% coverage\nEOF" in output_content

@patch("sys.exit")
def test_main_missing_inputs(mock_exit, monkeypatch):
    """Verify that script fails when required variables are missing."""
    mock_exit.side_effect = Exception("SystemExit")
    monkeypatch.delenv("INPUT_API_KEY", raising=False) # Delete API key

    with pytest.raises(Exception, match="SystemExit"):
        main.main()
    
    mock_exit.assert_called_once_with(1)

@patch("urllib.request.urlopen")
@patch("time.sleep", return_value=None)
@patch("sys.exit")
def test_main_task_failed(mock_exit, mock_sleep, mock_urlopen, mock_env):
    """Scenario where the Luau script fails on Roblox servers."""
    mock_exit.side_effect = Exception("SystemExit")
    
    mock_urlopen.side_effect = [
        create_mock_response({"versionNumber": 42}),
        create_mock_response({"path": "task-123"}),
        create_mock_response({"state": "FAILED"}), # Task failed!
        create_mock_response({"luauExecutionSessionTaskLogs": [{"messages": ["Syntax error"]}]})
    ]

    with pytest.raises(Exception, match="SystemExit"):
        main.main()

    # The script should exit with code 1
    mock_exit.assert_called_once_with(1)
    
    # But the outputs should still be printed for debugging
    output_content = mock_env["github_output"].read_text(encoding="utf-8")
    assert "task_status<<EOF\nFAILED\nEOF" in output_content
    assert "task_logs<<EOF\nSyntax error\nEOF" in output_content

@patch("urllib.request.urlopen")
@patch("sys.exit")
def test_make_request_http_error(mock_exit, mock_urlopen, mock_env):
    """Scenario for testing HTTP error handling (e.g invalid API key 401)."""
    mock_exit.side_effect = Exception("SystemExit")
    
    # Simulate HTTP 401 Unauthorized
    error_response = MagicMock()
    error_response.read.return_value = b'{"message": "Unauthorized"}'
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="https://apis.roblox.com/...",
        code=401,
        msg="Unauthorized",
        hdrs={},
        fp=error_response
    )

    with pytest.raises(Exception, match="SystemExit"):
        main.main()

    mock_exit.assert_called_once_with(1)
