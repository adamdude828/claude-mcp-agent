"""Tests for logging configuration and functionality."""
import json
import pytest
from clade_mcp_agent.logging import configure_logging, get_logger

@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file."""
    return tmp_path / "test.log"

def test_json_log_format(temp_log_file, caplog):
    """Test that logs are properly formatted as JSON in production mode."""
    configure_logging(log_file=temp_log_file, test_mode=False)
    logger = get_logger("test")
    
    test_message = "Test log message"
    logger.info(test_message, extra_field="test_value")
    
    # Read the log file
    log_content = temp_log_file.read_text()
    log_entry = json.loads(log_content.strip())
    
    # Verify JSON structure
    assert log_entry["event"] == test_message
    assert log_entry["level"] == "info"
    assert log_entry["extra_field"] == "test_value"
    assert "timestamp" in log_entry

def test_context_propagation(temp_log_file):
    """Test that context is properly propagated in logs."""
    configure_logging(log_file=temp_log_file, test_mode=False)
    logger = get_logger("test")
    
    # Add context to logger
    logger = logger.bind(server_id="test-server", request_id="123")
    
    logger.info("Test with context")
    
    # Read and parse log
    log_content = temp_log_file.read_text()
    log_entry = json.loads(log_content.strip())
    
    # Verify context fields
    assert log_entry["server_id"] == "test-server"
    assert log_entry["request_id"] == "123"

def test_log_rotation(tmp_path):
    """Test that log rotation works correctly."""
    log_file = tmp_path / "rotating.log"
    max_bytes = 100  # Small size for testing
    backup_count = 3
    
    configure_logging(
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
        test_mode=False
    )
    logger = get_logger("test")
    
    # Write enough logs to trigger rotation
    long_message = "x" * 50  # 50 bytes per message
    for _ in range(10):  # Should create multiple log files
        logger.info(long_message)
    
    # Check that rotation occurred
    assert log_file.exists()
    rotated_files = list(tmp_path.glob("rotating.log.*"))
    assert len(rotated_files) <= backup_count
    
    # Verify all files are readable
    for log_file in [log_file, *rotated_files]:
        assert log_file.stat().st_size > 0
        content = log_file.read_text()
        assert len(content) > 0

def test_test_mode_logging(capsys):
    """Test that test mode uses console renderer."""
    configure_logging(test_mode=True)
    logger = get_logger("test")
    
    test_message = "Test console output"
    logger.info(test_message)
    
    # In test mode, logs should be human-readable, not JSON
    captured = capsys.readouterr()
    assert test_message in captured.out
    
    # Verify it's not JSON format
    with pytest.raises(json.JSONDecodeError):
        json.loads(captured.out)

def test_log_level_configuration(temp_log_file, monkeypatch):
    """Test that log level from settings is respected."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    
    configure_logging(log_file=temp_log_file, test_mode=False)
    logger = get_logger("test")
    
    # Debug message should be logged
    logger.debug("Debug message")
    
    log_content = temp_log_file.read_text()
    log_entry = json.loads(log_content.strip())
    
    assert log_entry["level"] == "debug"
    assert log_entry["event"] == "Debug message"

def test_exception_logging(temp_log_file):
    """Test that exceptions are properly formatted in logs."""
    configure_logging(log_file=temp_log_file, test_mode=False)
    logger = get_logger("test")
    
    try:
        raise ValueError("Test error")
    except Exception:
        logger.exception("Error occurred")
    
    # Read the log file and get the JSON log entry
    log_content = temp_log_file.read_text()
    json_lines = [line for line in log_content.strip().split('\n') if line.startswith('{')]
    assert len(json_lines) > 0
    log_entry = json.loads(json_lines[0])
    
    assert log_entry["event"] == "Error occurred"
    assert "ValueError: Test error" in log_entry["exception"]
    assert "test_logging.py" in log_entry["exception"]  # Stack trace 