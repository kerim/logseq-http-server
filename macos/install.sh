#!/bin/bash
# Logseq DB Sidekick Server - macOS Installer
# Installs LaunchAgent to auto-start HTTP server at login

set -e  # Exit on error

echo "🚀 Installing Logseq DB Sidekick Server for macOS..."
echo ""

# 1. Detect Python path
echo "Detecting Python installation..."
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo "❌ Error: python3 not found. Please install Python 3."
    echo "   You can install it with: brew install python3"
    exit 1
fi
echo "✓ Found Python at: $PYTHON_PATH"

# 2. Get server script location (assume running from macos/ directory)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVER_DIR="$(dirname "$SCRIPT_DIR")"
SERVER_SCRIPT="$SERVER_DIR/logseq_server.py"

if [ ! -f "$SERVER_SCRIPT" ]; then
    echo "❌ Error: Server script not found at $SERVER_SCRIPT"
    exit 1
fi
echo "✓ Found server script at: $SERVER_SCRIPT"

# 3. Check for logseq CLI
if ! command -v logseq &> /dev/null; then
    echo "⚠️  Warning: logseq command not found"
    echo "   You need to install @logseq/cli:"
    echo "   npm install -g @logseq/cli"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 4. Check if already installed
PLIST_PATH="$HOME/Library/LaunchAgents/com.logseq.sidekick.server.plist"
if [ -f "$PLIST_PATH" ]; then
    echo "⚠️  LaunchAgent already installed"
    read -p "Reinstall? This will restart the server. (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 0
    fi

    # Unload existing
    echo "Unloading existing LaunchAgent..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
fi

# 5. Create LaunchAgent plist (substitute paths)
echo "Creating LaunchAgent plist..."

cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.logseq.sidekick.server</string>

    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SERVER_SCRIPT</string>
    </array>

    <!-- Start at login -->
    <key>RunAtLoad</key>
    <true/>

    <!-- Restart if crashes -->
    <key>KeepAlive</key>
    <true/>

    <!-- Logging -->
    <key>StandardOutPath</key>
    <string>/tmp/logseq-server.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/logseq-server.log</string>

    <!-- Working directory -->
    <key>WorkingDirectory</key>
    <string>$SERVER_DIR</string>

    <!-- Environment variables -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

echo "✓ Created LaunchAgent plist"

# 6. Set correct permissions
chmod 644 "$PLIST_PATH"
echo "✓ Set permissions"

# 7. Load LaunchAgent
echo "Loading LaunchAgent..."
launchctl load -w "$PLIST_PATH"
echo "✓ Loaded LaunchAgent"

# 8. Wait and verify server started
echo "Waiting for server to start..."
sleep 3

if curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/health | grep -q "200"; then
    echo "✅ Server is running!"
else
    echo "⚠️  Server may not be running. Check logs at /tmp/logseq-server.log"
fi

# 9. Ask about copying control app to Applications
echo ""
if [ -d "$SCRIPT_DIR/Logseq Server Control.app" ]; then
    read -p "Copy control app to /Applications? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp -r "$SCRIPT_DIR/Logseq Server Control.app" /Applications/
        echo "✓ Control app installed to /Applications"
    fi
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "The server will now start automatically at login."
echo "You can control it using: /Applications/Logseq Server Control.app"
echo ""
echo "Manual commands:"
echo "  Start:   launchctl start com.logseq.sidekick.server"
echo "  Stop:    launchctl stop com.logseq.sidekick.server"
echo "  Logs:    tail -f /tmp/logseq-server.log"
echo ""
