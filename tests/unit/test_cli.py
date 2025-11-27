"""
Tests for CLI Entry Point

Tests for watch command and CLI argument parsing.
"""

from pathlib import Path
from unittest.mock import patch

import pytest


class TestCLIParser:
    """Test CLI argument parser."""

    def test_watch_command_default_args(self):
        """Test watch command with default arguments."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["watch"])

        assert args.command == "watch"
        assert args.path == Path.cwd()
        assert args.debounce == 1.0
        assert args.community is False

    def test_watch_command_with_path(self):
        """Test watch command with custom path."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["watch", "/tmp/test"])

        assert args.command == "watch"
        assert args.path == Path("/tmp/test")

    def test_watch_command_with_debounce(self):
        """Test watch command with custom debounce."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["watch", "--debounce", "2.5"])

        assert args.debounce == 2.5

    def test_watch_command_with_community(self):
        """Test watch command with community flag."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()
        args = parser.parse_args(["watch", "--community"])

        assert args.community is True

    def test_all_commands_available(self):
        """Test that all expected commands are available."""
        from codegraph_mcp.__main__ import create_parser

        parser = create_parser()

        # Test each command parses without error
        commands = [
            ["start"],
            ["stop"],
            ["status"],
            ["serve"],
            ["index", "."],
            ["watch"],
            ["query", "test"],
            ["stats"],
            ["community"],
        ]

        for cmd in commands:
            args = parser.parse_args(cmd)
            assert args.command == cmd[0]


class TestMainFunction:
    """Test main entry point."""

    def test_main_no_args(self):
        """Test main with no arguments prints help."""
        from codegraph_mcp.__main__ import main

        with patch('sys.argv', ['codegraph-mcp']):
            result = main()
            assert result == 0

    def test_main_version(self):
        """Test main with --version flag."""
        from codegraph_mcp.__main__ import main

        with patch('sys.argv', ['codegraph-mcp', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_commands_dict_contains_watch(self):
        """Test that commands dictionary includes watch."""
        from codegraph_mcp.__main__ import cmd_watch

        # Verify cmd_watch exists and is callable
        assert callable(cmd_watch)
