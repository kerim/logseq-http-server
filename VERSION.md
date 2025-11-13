# Logseq HTTP Server - Version History

## Version 0.0.2 (2025-11-13)

**Major Features:**
- Added macOS background service support via LaunchAgent
- Created AppleScript control app for managing server
- Automated install/uninstall scripts
- Single unified log file (`/tmp/logseq-server.log`)
- Fixed PATH environment variable for logseq CLI access

**New Files:**
- `macos/com.logseq.sidekick.server.plist` - LaunchAgent configuration
- `macos/Logseq Server Control.app` - GUI control application
- `macos/install.sh` - Automated installer
- `macos/uninstall.sh` - Automated uninstaller
- `macos/README.md` - macOS setup documentation
- `macos/POC-NOTES.md` - Technical implementation notes

**API Changes:**
- Added `GET /version` endpoint - Returns server version

**Improvements:**
- Server now displays version in startup banner
- Version logged in startup message
- Comprehensive documentation for macOS setup

**Bug Fixes:**
- Fixed logseq CLI not found in LaunchAgent environment

---

## Version 0.0.1 (2025-11-09)

**Initial Release:**
- Basic HTTP server for Logseq CLI commands
- REST API endpoints for graph operations
- Support for DB (database) graphs
- Datalog query execution via @logseq/cli
- EDN to JSON conversion using jet
- CORS support for browser extensions

**API Endpoints:**
- `GET /health` - Health check
- `GET /list` - List all graphs
- `GET /show?graph=NAME` - Show graph info
- `GET /search?q=QUERY&graph=NAME` - Search graphs
- `POST /query` - Execute datalog queries

**Requirements:**
- Python 3
- @logseq/cli (npm package)
- jet (Clojure EDN processor)
