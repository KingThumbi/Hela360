"""
Hela360 command-line interface modules.
"""

from app.cli.platform import (
    platform_cli,
    register_platform_cli,
)

__all__ = [
    "platform_cli",
    "register_platform_cli",
]
