#!/bin/bash
# Logseq DB Sidekick Server - macOS Uninstaller
# Removes LaunchAgent and cleans up installation

echo "🗑️  Uninstalling Logseq DB Sidekick Server..."
echo ""

PLIST_PATH="$HOME/Library/LaunchAgents/com.logseq.sidekick.server.plist"

# Stop and unload LaunchAgent
if [ -f "$PLIST_PATH" ]; then
    echo "Stopping server..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true

    echo "Removing LaunchAgent..."
    rm "$PLIST_PATH"
    echo "✓ Removed LaunchAgent"
else
    echo "⚠️  LaunchAgent not found (already uninstalled?)"
fi

# Remove control app
if [ -d "/Applications/Logseq Server Control.app" ]; then
    echo "Removing control app..."
    rm -rf "/Applications/Logseq Server Control.app"
    echo "✓ Removed control app"
fi

# Ask about logs
echo ""
if [ -f "/tmp/logseq-server.log" ]; then
    read -p "Remove server log? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f /tmp/logseq-server.log
        echo "✓ Removed log"
    fi
fi

echo ""
echo "✅ Uninstall complete!"
echo ""
echo "Note: The HTTP server code and extension remain installed."
echo "To remove those, manually delete:"
echo "  - HTTP server: $(dirname "$(dirname "${BASH_SOURCE[0]}")")"
echo "  - Browser extension: Uninstall from your browser's extension settings"
echo ""
