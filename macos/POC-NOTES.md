# macOS Background Service - POC Notes

**Date**: 2025-11-13
**Status**: ✅ Completed Successfully

## Overview

Proof of concept for running the Logseq HTTP server as a macOS background service using LaunchAgents. This allows the server to start automatically at login and stay running persistently.

## What We Built

1. **LaunchAgent plist** - Auto-starts server at login with KeepAlive
2. **AppleScript control app** - GUI for managing the server
3. **Automated installer** - One-command setup
4. **Automated uninstaller** - Clean removal

## Key Discoveries

### 1. LaunchAgents Don't Inherit Shell Environment

**Problem**: Server couldn't find the `logseq` command even though it was hardcoded as `/opt/homebrew/bin/logseq`.

**Root Cause**: LaunchAgents run with minimal environment variables and don't include user shell PATH.

**Solution**: Added `EnvironmentVariables` dict to plist with full PATH:
```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
</dict>
```

### 2. Python Writes All Logs to stderr

**Problem**: Initially had separate stdout and stderr log files, but stderr contained INFO-level messages (not just errors).

**Root Cause**: Python's logging module writes to stderr by default, including INFO level messages.

**Solution**: Simplified to single log file by pointing both streams to same location:
```xml
<key>StandardOutPath</key>
<string>/tmp/logseq-server.log</string>
<key>StandardErrorPath</key>
<string>/tmp/logseq-server.log</string>
```

### 3. KeepAlive Behavior

**Discovery**: With `KeepAlive` set to `true`, the LaunchAgent automatically restarts the server if it crashes.

**Side Effect**: `launchctl stop` doesn't work as expected - server immediately restarts.

**Workaround**: Use `launchctl unload/load` for full stop/start control.

## File Structure

```
macos/
├── com.logseq.sidekick.server.plist    # LaunchAgent template
├── Logseq Server Control.applescript   # Source code
├── Logseq Server Control.app           # Compiled app
├── install.sh                          # Automated installer
├── uninstall.sh                        # Automated uninstaller
├── README.md                           # User documentation
└── POC-NOTES.md                        # This file
```

## Testing Results

### Manual Testing (POC Phase)

- ✅ LaunchAgent loads successfully
- ✅ Server starts automatically at login
- ✅ Server restarts on crashes (KeepAlive works)
- ✅ `logseq` command found with PATH environment variable
- ✅ Extension successfully queries server
- ✅ AppleScript control app all functions work:
  - Check Status (shows loaded + HTTP responding)
  - Start Server (detects already running)
  - Stop Server (unloads LaunchAgent)
  - Restart Server (unload + load + verify)
  - View Logs (opens only non-empty logs)
  - Clear Logs (empties log file with confirmation)

### Search Functionality

Tested with "taiwan" query:
- ✅ Returns 22 pages from Logseq DB graph
- ✅ No "command not found" errors
- ✅ HTTP 200 responses
- ✅ Extension displays results correctly

## Lessons Learned

1. **Always test LaunchAgents with fresh environment**: What works in terminal may fail in LaunchAgent due to PATH differences.

2. **Single log file is simpler**: No confusion about where errors are, easier to debug.

3. **POC first approach worked well**: Testing manually before automating helped identify issues early.

4. **AppleScript is good for simple GUIs**: Easy to create user-friendly control without building full Cocoa app.

5. **Test with unload first**: Always unload existing LaunchAgents before testing changes to plist.

## Next Steps (Integration Phase)

- [ ] Test `install.sh` on clean setup (without existing LaunchAgent)
- [ ] Test `uninstall.sh` fully removes everything
- [ ] Commit to GitHub
- [ ] Update main project TODO.md
- [ ] Consider adding version to installer
- [ ] Test on different Mac architectures (Intel vs Apple Silicon)

## Commands Reference

```bash
# Manual installation (what install.sh automates)
cp com.logseq.sidekick.server.plist ~/Library/LaunchAgents/
chmod 644 ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
launchctl load -w ~/Library/LaunchAgents/com.logseq.sidekick.server.plist

# Check status
launchctl list | grep logseq
curl http://localhost:8765/health

# View logs
tail -f /tmp/logseq-server.log

# Unload
launchctl unload ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
```

## Known Limitations

1. **macOS only**: This approach doesn't work on Linux/Windows (need different solutions)
2. **Requires Python from Homebrew path**: Installer detects but assumes standard paths
3. **Port 8765 hardcoded**: No easy way to change port without editing server code
4. **No automatic updates**: If server code changes, user must manually restart

## Future Enhancements

- Add version checking to installer
- Create menu bar app (using Platypus or similar)
- Add configuration file support (change port, graph, etc.)
- Add notification support (notify user when server starts/stops/crashes)
- Create DMG installer for easier distribution

## Resources

- [Apple LaunchAgent Documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [launchd.info](https://www.launchd.info/) - Comprehensive LaunchAgent guide
