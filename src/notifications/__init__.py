"""
Notifications module for sending alerts and messages.
"""

from .telegram import TelegramNotifier

__all__ = ["TelegramNotifier"]
