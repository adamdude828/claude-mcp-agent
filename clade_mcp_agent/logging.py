"""Logging configuration for the Clade MCP Agent."""
import logging.handlers
import sys
import structlog
from pathlib import Path
from typing import Any, Dict, Optional
from .config import get_settings

def configure_logging(
    log_file: Optional[Path] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    test_mode: bool = False,
) -> None:
    """Configure structured logging for the application.
    
    Args:
        log_file: Optional path to log file. If None, logs to stdout only.
        max_bytes: Maximum size of each log file before rotation.
        backup_count: Number of backup files to keep.
        test_mode: Whether to configure logging for test environment.
    """
    settings = get_settings()
    
    # Configure stdlib logging
    handlers = []
    
    # Always add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)
    
    # Add file handler if log_file specified
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8',
        )
        handlers.append(file_handler)
    
    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    
    # Remove any existing handlers to prevent duplicate logging
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Add our handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Configure structlog
    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        add_context_processor,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if test_mode:
        # Use plain console renderer for tests
        renderer = structlog.dev.ConsoleRenderer(colors=True)
    else:
        # Use JSON renderer for production
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Set formatters for handlers
    if test_mode:
        formatter = logging.Formatter('%(message)s')
    else:
        formatter = logging.Formatter('%(message)s')
        
    for handler in handlers:
        handler.setFormatter(formatter)

def add_context_processor(
    logger: Any,
    method_name: str,
    event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """Add context information to log events.
    
    Args:
        logger: The logger instance.
        method_name: The name of the logging method.
        event_dict: The current event dictionary.
        
    Returns:
        Updated event dictionary with context.
    """
    # Add server ID if available in context
    if hasattr(logger, "server_id"):
        event_dict["server_id"] = logger.server_id
        
    # Add request ID if available in context
    if hasattr(logger, "request_id"):
        event_dict["request_id"] = logger.request_id
        
    return event_dict

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance with the given name.
    
    Args:
        name: The name for the logger.
        
    Returns:
        A configured structlog logger instance.
    """
    return structlog.get_logger(name) 