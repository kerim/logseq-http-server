# macOS Background Service Setup

This directory contains tools to run the Logseq HTTP server automatically in the background on macOS using LaunchAgents.

## Features

- **Auto-start at login**: Server starts automatically when you log in
- **Persistent**: Automatically restarts if it crashes
- **GUI Control**: AppleScript app to manage the server
- **Simple installation**: One command to set up everything

## Quick Install

```bash
cd /path/to/logseq-http-server/macos
./install.sh
```

The installer will:
1. Detect your Python installation
2. Create a LaunchAgent to auto-start the server
3. Start the server immediately
4. Optionally install the control app to /Applications

## Requirements

- **Python 3**: Should be installed via Homebrew
- **@logseq/cli**: Install with `npm install -g @logseq/cli`
- **jet**: Install with `brew install borkdude/brew/jet`
- **Logseq DB graph**: Must have at least one DB (database) graph configured

## Usage

### Control App

Double-click `/Applications/Logseq Server Control.app` to:
- Check server status
- Start/stop/restart the server
- View logs
- Clear logs

### Manual Commands

```bash
# Check status
launchctl list | grep logseq

# Start server
launchctl start com.logseq.sidekick.server

# Stop server
launchctl unload ~/Library/LaunchAgents/com.logseq.sidekick.server.plist

# View logs
tail -f /tmp/logseq-server.log

# Clear logs
cat /dev/null > /tmp/logseq-server.log
```

## Uninstall

```bash
cd /path/to/logseq-http-server/macos
./uninstall.sh
```

This will:
- Stop and remove the LaunchAgent
- Remove the control app from /Applications
- Optionally delete log files

## Files

- **com.logseq.sidekick.server.plist**: Template for LaunchAgent configuration
- **Logseq Server Control.applescript**: Source code for control app
- **Logseq Server Control.app**: Compiled AppleScript application
- **install.sh**: Automated installer script
- **uninstall.sh**: Automated uninstaller script

## How It Works

The installer creates a LaunchAgent (`~/Library/LaunchAgents/com.logseq.sidekick.server.plist`) that:

1. Runs `python3 logseq_server.py` at login
2. Keeps it running (restarts on crashes)
3. Logs to `/tmp/logseq-server.log`
4. Sets the correct PATH environment variable to find the `logseq` CLI

## Troubleshooting

### Server not starting

Check the logs:
```bash
cat /tmp/logseq-server.log
```

Common issues:
- **"logseq command not found"**: Install @logseq/cli with `npm install -g @logseq/cli`
- **"jet command not found"**: Install jet with `brew install borkdude/brew/jet`
- **"Address already in use"**: Another process is using port 8765

### LaunchAgent not loading

Verify the plist file:
```bash
plutil -lint ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
launchctl load -w ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
```

### Reinstalling

Simply run `./install.sh` again. It will ask if you want to reinstall.

## Technical Details

### LaunchAgent Configuration

The LaunchAgent is configured with:
- **Label**: `com.logseq.sidekick.server`
- **RunAtLoad**: `true` (starts at login)
- **KeepAlive**: `true` (restarts on crashes)
- **WorkingDirectory**: Path to logseq-http-server directory
- **Environment PATH**: Includes Homebrew paths for CLI tools

### Log Location

All server output (both stdout and stderr) goes to:
- `/tmp/logseq-server.log`

This file persists across restarts but is cleared on system reboot.

## Platform Notes

This setup is **macOS only**. For other platforms:
- **Linux**: Use systemd user services
- **Windows**: Use Task Scheduler or NSSM

See the main README for manual server startup instructions.

## Related Documentation

- [Main README](../README.md) - HTTP server overview
- [Logseq DB Sidekick TODO](../../logseq-sidekick/docs/TODO.md) - Project roadmap
