#!/bin/bash
# setup_github.sh
# ─────────────────────────────────────────────────────────────
# Run this once from inside the bed_exit_monitor folder.
# It will create a new GitHub repo and push all project files.
#
# Usage:
#   cd bed_exit_monitor
#   bash setup_github.sh
# ─────────────────────────────────────────────────────────────

# ── EDIT THESE TWO VALUES ─────────────────────────────────────
GITHUB_TOKEN="YOUR_TOKEN_HERE"
REPO_NAME="bed-exit-monitor"
# ─────────────────────────────────────────────────────────────

echo "🔍 Looking up your GitHub username..."
USERNAME=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user | python3 -c "import sys,json; print(json.load(sys.stdin)['login'])")

if [ -z "$USERNAME" ]; then
  echo "❌ Could not get username. Check that your token is valid."
  exit 1
fi
echo "✅ Logged in as: $USERNAME"

echo ""
echo "📦 Creating GitHub repository '$REPO_NAME'..."
RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  https://api.github.com/user/repos \
  -d "{
    \"name\": \"$REPO_NAME\",
    \"description\": \"Real-time bed exit detection using YOLOv8 pose estimation\",
    \"private\": false,
    \"auto_init\": false
  }")

REPO_URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('html_url',''))")

if [ -z "$REPO_URL" ]; then
  echo "❌ Failed to create repo. It may already exist, or the token lacks 'repo' permissions."
  echo "   Raw response: $RESPONSE"
  exit 1
fi

echo "✅ Repo created: $REPO_URL"

echo ""
echo "📁 Initializing git and pushing files..."

git init
git add .
git commit -m "Initial commit — bed exit monitor v1.0

- YOLOv8 pose estimation via USB camera
- Draggable bed-edge threshold line
- Alert system: beep + Jitsi video call
- Configurable via config.py"

git branch -M main

# Use token-authenticated HTTPS URL so no password prompt appears
git remote add origin "https://$USERNAME:$GITHUB_TOKEN@github.com/$USERNAME/$REPO_NAME.git"

git push -u origin main

echo ""
echo "🎉 All done! Your project is live at:"
echo "   $REPO_URL"
echo ""
echo "⚠️  Security tip: delete your Personal Access Token now that the push is done."
echo "   https://github.com/settings/tokens"
