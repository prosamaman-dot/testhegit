#!/usr/bin/env python3
"""
Auto cleanup script to organize old files into new structure.
"""

import os
import shutil
from pathlib import Path

def cleanup_and_organize():
    """Clean up old files and organize them properly."""
    
    print("Starting auto cleanup and organization...")
    
    # Create directories if they don't exist
    directories = [
        "logs",
        "data", 
        "src/config",
        "src/core",
        "src/data", 
        "src/strategies",
        "src/notifications",
        "src/utils"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Files to move to logs/
    log_files = [
        "bot.log",
        "bot.log.1", 
        "bot.log.2",
        "bot.log.3",
        "bot.log.4",
        "bot.log.5"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                shutil.move(log_file, f"logs/{log_file}")
                print(f"Moved {log_file} to logs/")
            except Exception as e:
                print(f"Could not move {log_file}: {e}")
    
    # Files to move to data/
    data_files = [
        "trade_history.json",
        "performance.json",
        "trades.json"
    ]
    
    for data_file in data_files:
        if os.path.exists(data_file):
            try:
                shutil.move(data_file, f"data/{data_file}")
                print(f"Moved {data_file} to data/")
            except Exception as e:
                print(f"Could not move {data_file}: {e}")
    
    # Files to remove (old duplicates)
    files_to_remove = [
        "bot.py",
        "config.py", 
        "data_fetcher.py",
        "mock_data_fetcher.py",
        "performance.py",
        "risk_manager.py",
        "strategy.py",
        "telegram_alerts.py",
        "logger.py",
        "simple_logger.py",
        "news_feed.py",
        "sentiment_analysis.py",
        "volume_strategies.py",
        "live_logs.py",
        "log_checker.py",
        "view_logs.py",
        "check_logs.bat",
        "live_logs.bat",
        "view_logs.bat"
    ]
    
    for file_to_remove in files_to_remove:
        if os.path.exists(file_to_remove):
            try:
                os.remove(file_to_remove)
                print(f"Removed old file: {file_to_remove}")
            except Exception as e:
                print(f"Could not remove {file_to_remove}: {e}")
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                pycache_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(pycache_path)
                    print(f"Removed __pycache__: {pycache_path}")
                except Exception as e:
                    print(f"Could not remove {pycache_path}: {e}")
    
    print("\nAuto cleanup completed!")
    print("New structure:")
    print("   main.py (entry point)")
    print("   src/ (organized source code)")
    print("   logs/ (log files)")
    print("   data/ (data files)")
    print("   venv/ (virtual environment)")

if __name__ == "__main__":
    cleanup_and_organize()
