# 🔧 GIT GUIDE - Trading Bot Project

## 📋 How to Use Git with Your Trading Bot

This guide will help you manage your trading bot project using Git version control.

---

## 🚀 Getting Started

### 1️⃣ **Initialize Git Repository**
```bash
# Navigate to your project folder
cd C:\Users\hp\scalper-bot

# Initialize Git repository
git init

# Add all files to Git
git add .

# Create first commit
git commit -m "Initial commit: Trading bot setup"
```

### 2️⃣ **Configure Git (First Time Only)**
```bash
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Check configuration
git config --list
```

---

## 📁 Project Structure

### 🗂️ **Files Tracked by Git:**
```
scalper-bot/
├── main.py                 # Main entry point
├── requirements.txt        # Dependencies
├── README.md              # Project documentation
├── SIGNAL_GUIDE.md        # Signal usage guide
├── GIT.md                 # This Git guide
├── .gitignore             # Files to ignore
├── start_bot.bat          # Start script
├── stop_bot.bat           # Stop script
├── cleanup_old_files.bat  # Cleanup script
├── src/                   # Source code
│   ├── config/
│   ├── core/
│   ├── data/
│   ├── notifications/
│   ├── strategies/
│   └── utils/
└── logs/                  # Log files (ignored)
```

### 🚫 **Files Ignored by Git:**
- `logs/` - Log files (too large)
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python files
- `.env` - Environment variables
- `*.log` - Log files

---

## 🔄 Daily Git Workflow

### 📝 **Making Changes:**
```bash
# 1. Check what files changed
git status

# 2. Add specific files
git add src/core/bot.py
git add src/config/settings.py

# 3. Or add all changes
git add .

# 4. Commit with descriptive message
git commit -m "Fix: Improved signal generation logic"
```

### 📋 **Good Commit Messages:**
```bash
# Feature additions
git commit -m "Feature: Add news feed with sentiment analysis"

# Bug fixes
git commit -m "Fix: Resolve Telegram API parsing errors"

# Configuration changes
git commit -m "Config: Update trading parameters for swing trading"

# Documentation
git commit -m "Docs: Add comprehensive signal guide"

# Refactoring
git commit -m "Refactor: Clean up performance tracking code"
```

---

## 🌿 Branch Management

### 🌳 **Create and Use Branches:**
```bash
# Create new branch for features
git checkout -b feature/news-alerts
git checkout -b feature/risk-management
git checkout -b bugfix/telegram-errors

# Switch between branches
git checkout main
git checkout feature/news-alerts

# List all branches
git branch

# Delete branch (after merging)
git branch -d feature/news-alerts
```

### 🔀 **Merge Branches:**
```bash
# Switch to main branch
git checkout main

# Merge feature branch
git merge feature/news-alerts

# Delete feature branch
git branch -d feature/news-alerts
```

---

## 📊 Viewing History and Changes

### 📈 **View Commit History:**
```bash
# Show all commits
git log

# Show commits with one line each
git log --oneline

# Show commits with graph
git log --graph --oneline

# Show last 10 commits
git log -10
```

### 🔍 **Compare Changes:**
```bash
# See what changed
git diff

# See changes in specific file
git diff src/core/bot.py

# See changes between commits
git diff HEAD~1 HEAD

# See changes between branches
git diff main feature/news-alerts
```

### 📋 **Check Status:**
```bash
# Show current status
git status

# Show short status
git status -s

# Show ignored files
git status --ignored
```

---

## 🔄 Undoing Changes

### ↩️ **Undo Uncommitted Changes:**
```bash
# Discard changes to specific file
git checkout -- src/core/bot.py

# Discard all changes
git checkout -- .

# Unstage files (keep changes)
git reset HEAD src/core/bot.py
```

### 🔙 **Undo Commits:**
```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo multiple commits
git reset --hard HEAD~3
```

### 🏷️ **Tag Important Versions:**
```bash
# Create tag for version
git tag -a v1.0.0 -m "First stable version"

# List tags
git tag

# Show tag details
git show v1.0.0
```

---

## ☁️ Remote Repository (GitHub/GitLab)

### 🔗 **Connect to Remote:**
```bash
# Add remote repository
git remote add origin https://github.com/yourusername/scalper-bot.git

# Check remote
git remote -v

# Push to remote
git push -u origin main

# Pull from remote
git pull origin main
```

### 📤 **Push Changes:**
```bash
# Push current branch
git push

# Push specific branch
git push origin feature/news-alerts

# Push all branches
git push --all

# Push tags
git push --tags
```

### 📥 **Pull Changes:**
```bash
# Pull latest changes
git pull

# Pull specific branch
git pull origin feature/news-alerts

# Fetch without merging
git fetch
```

---

## 🛠️ Advanced Git Commands

### 🔍 **Search in History:**
```bash
# Search for text in commits
git log --grep="signal"

# Search for text in code
git log -S "telegram" --oneline

# Search in specific file
git log -p src/core/bot.py
```

### 🧹 **Clean Up:**
```bash
# Remove untracked files
git clean -f

# Remove untracked files and directories
git clean -fd

# Show what would be removed
git clean -n
```

### 📊 **Statistics:**
```bash
# Show commit statistics
git log --stat

# Show author statistics
git log --author="Your Name" --oneline

# Show file statistics
git log --pretty=format: --name-only | sort | uniq -c | sort -rg
```

---

## 🚨 Common Git Issues and Solutions

### ❌ **"Your branch is ahead of origin"**
```bash
# Push your changes
git push origin main
```

### ❌ **"Merge conflict"**
```bash
# See conflicted files
git status

# Edit files to resolve conflicts
# Then add and commit
git add .
git commit -m "Resolve merge conflicts"
```

### ❌ **"Nothing to commit"**
```bash
# Check if files are staged
git status

# Add files if needed
git add .
git commit -m "Your message"
```

### ❌ **"Branch not found"**
```bash
# List all branches
git branch -a

# Create branch if needed
git checkout -b branch-name
```

---

## 📋 Git Best Practices

### ✅ **DO:**
- Commit frequently with descriptive messages
- Use branches for new features
- Keep commits small and focused
- Write clear commit messages
- Review changes before committing
- Use `.gitignore` for unnecessary files

### ❌ **DON'T:**
- Commit sensitive data (API keys, passwords)
- Commit large files (logs, databases)
- Force push to shared repositories
- Commit broken code
- Use vague commit messages like "fix" or "update"

---

## 🔐 Security Notes

### 🛡️ **Never Commit:**
- API keys or tokens
- Passwords or secrets
- Personal information
- Large log files
- Database files

### 🔒 **Use .gitignore:**
```gitignore
# Environment variables
.env
.env.local

# Logs
logs/
*.log

# Python cache
__pycache__/
*.pyc
*.pyo

# IDE files
.vscode/
.idea/

# OS files
.DS_Store
Thumbs.db
```

---

## 📚 Useful Git Aliases

### ⚡ **Add to Git Config:**
```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'
```

### 🎯 **Now You Can Use:**
```bash
git st          # git status
git co main     # git checkout main
git br          # git branch
git ci -m "msg" # git commit -m "msg"
```

---

## 🎯 Quick Reference

### 📝 **Daily Commands:**
```bash
git status              # Check status
git add .               # Add all changes
git commit -m "msg"     # Commit changes
git push                # Push to remote
git pull                # Pull from remote
```

### 🔄 **Branch Commands:**
```bash
git branch              # List branches
git checkout -b name    # Create branch
git checkout name       # Switch branch
git merge name          # Merge branch
```

### 📊 **View Commands:**
```bash
git log                 # View history
git diff                # View changes
git show                # View last commit
```

---

**Happy Coding! 🚀💻**

*Remember: Git is your friend for tracking changes and collaborating on code!*
