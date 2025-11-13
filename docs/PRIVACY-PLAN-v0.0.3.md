# Privacy Update Plan - Version 0.0.3

**Date Created:** 2025-11-13
**Status:** Planned (Not Yet Implemented)
**Priority:** High (Privacy Issue)

---

## Problem Statement

The current server logs all search queries in plain text, creating a privacy risk:

```
2025-11-13 13:55:07,423 - INFO - GET /search - {'q': ['joyce'], 'graph': ['Chrome Import 2025-11-09']}
2025-11-13 13:55:13,224 - INFO - GET /search - {'q': ['taiwan'], 'graph': ['Chrome Import 2025-11-09']}
2025-11-13 13:55:38,611 - INFO - GET /search - {'q': ['www.facebook.com/'], 'graph': ['Chrome Import 2025-11-09']}
```

This creates a complete, plain-text history of:
- Every search query
- Every graph accessed
- Every URL visited (when extension queries pages)
- Timestamps of activity

**Impact:** Users may not realize their activity is being logged locally in `/tmp/logseq-server.log`

---

## Solution: Two Logging Modes

### Mode 1: Default (Privacy Mode) ✅ Recommended
**What gets logged:**
- ✅ Server startup with version
- ✅ Server shutdown
- ✅ Health checks (`GET /health`)
- ✅ Critical errors (server crashes, command failures)
- ❌ Search queries and parameters
- ❌ Graph names
- ❌ Datalog queries
- ❌ URLs being queried

**Log example:**
```
2025-11-13 14:04:36,774 - INFO - Server v0.0.3 started on localhost:8765 (Privacy Mode)
2025-11-13 14:04:45,148 - INFO - GET /health - OK
2025-11-13 14:05:12,234 - INFO - GET /health - OK
2025-11-13 14:30:00,000 - INFO - Server stopped by user
```

### Mode 2: Debug Mode (Opt-In)
**What gets logged:**
- ✅ Everything from Mode 1
- ✅ All requests with full parameters
- ✅ Search queries
- ✅ Graph names
- ✅ Datalog queries being executed
- ✅ Full HTTP request/response details

**Warning displayed on startup:**
```
============================================================
⚠️  WARNING: DEBUG MODE ENABLED
============================================================
Full request logging is active. This will log:
- All search queries
- Graph names
- Visited URLs

This creates a plain-text history of your activity.

Remember to:
1. Clear logs when done debugging: cat /dev/null > /tmp/logseq-server.log
2. Disable debug mode after fixing your issue

To start without debug mode, run: python3 logseq_server.py
============================================================
```

---

## Implementation Plan

### 1. Add Command-Line Flag

**Location:** `logseq_server.py` - `main()` function (around line 277)

**Changes:**
```python
parser.add_argument('--debug', action='store_true',
                    help='Enable debug logging (logs all queries - privacy warning!)')
```

---

### 2. Create Custom Logger Filter

**Location:** After imports, before `main()` (around line 45)

**New code:**
```python
class PrivacyFilter(logging.Filter):
    """Filter that blocks sensitive logging unless debug mode is enabled."""

    def __init__(self, debug_mode=False):
        super().__init__()
        self.debug_mode = debug_mode

    def filter(self, record):
        # Always allow startup, shutdown, errors
        if record.levelno >= logging.ERROR:
            return True

        # If debug mode, allow everything
        if self.debug_mode:
            return True

        # In privacy mode, only allow health checks and system messages
        message = record.getMessage()
        if 'GET /health' in message or 'Server' in message:
            return True

        # Block all other requests
        return False
```

---

### 3. Update Logging Configuration

**Location:** `main()` function, after parsing arguments

**Replace:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
```

**With:**
```python
# Set up logging with privacy filter
privacy_filter = PrivacyFilter(debug_mode=args.debug)

file_handler = logging.FileHandler(LOG_FILE)
file_handler.addFilter(privacy_filter)

console_handler = logging.StreamHandler()
console_handler.addFilter(privacy_filter)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[file_handler, console_handler]
)
```

---

### 4. Display Debug Warning

**Location:** `main()` function, in startup banner (around line 288)

**Add after argument parsing:**
```python
if args.debug:
    print("\n" + "="*60)
    print("⚠️  WARNING: DEBUG MODE ENABLED")
    print("="*60)
    print("Full request logging is active. This will log:")
    print("- All search queries")
    print("- Graph names")
    print("- Visited URLs")
    print()
    print("This creates a plain-text history of your activity.")
    print()
    print("Remember to:")
    print("1. Clear logs when done: cat /dev/null > /tmp/logseq-server.log")
    print("2. Disable debug mode after fixing your issue")
    print()
    print("To start without debug: python3 logseq_server.py")
    print("="*60 + "\n")

    # Give user time to see warning
    import time
    time.sleep(3)
```

---

### 5. Update Documentation

#### a) Update logseq_server.py docstring

**Location:** Top of file (around line 2-19)

**Update to:**
```python
"""
Logseq CLI HTTP Server

A simple HTTP server that provides REST API access to Logseq CLI commands.
Enables browser extensions and other applications to query Logseq graphs
without requiring the Logseq Desktop app to be running.

Usage:
    python3 logseq_server.py [--port PORT] [--host HOST] [--debug]

Options:
    --port PORT    Port to listen on (default: 8765)
    --host HOST    Host to bind to (default: localhost)
    --debug        Enable debug logging (WARNING: logs all queries)

API Endpoints:
    GET  /health                        - Health check
    GET  /version                       - Get server version
    GET  /list                          - List all graphs
    GET  /show?graph=name               - Show graph info
    GET  /search?q=query[&graph=name]   - Search graphs
    POST /query                         - Execute datalog query
         Body: {"graph": "name", "query": "..."}

Privacy:
    By default, only health checks and errors are logged.
    Debug mode logs all requests including search queries.
"""
```

#### b) Update macos/README.md

**Location:** `macos/README.md`

**Add new section after "Troubleshooting":**
```markdown
## Privacy & Logging

By default, the server uses privacy-safe logging:
- Only logs health checks and errors
- Does NOT log search queries or graph names
- Log file: `/tmp/logseq-server.log`

### Debug Mode

If you need to troubleshoot, enable debug mode:

**Manual start:**
```bash
python3 /path/to/logseq_server.py --debug
```

**LaunchAgent:** Edit the plist to add `--debug` flag:

1. Stop the server:
   ```bash
   launchctl unload ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
   ```

2. Edit the plist:
   ```bash
   nano ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
   ```

3. Add `<string>--debug</string>` to ProgramArguments:
   ```xml
   <key>ProgramArguments</key>
   <array>
       <string>/opt/homebrew/bin/python3</string>
       <string>/Users/your-username/Documents/Code/logseq-http-server/logseq_server.py</string>
       <string>--debug</string>  <!-- Add this line -->
   </array>
   ```

4. Restart the server:
   ```bash
   launchctl load -w ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
   ```

⚠️ **Warning:** Debug mode logs all search queries in plain text.

**After debugging, remember to:**
1. Remove the `--debug` flag from the plist
2. Clear logs: `cat /dev/null > /tmp/logseq-server.log`
3. Restart: `launchctl unload ~/Library/LaunchAgents/com.logseq.sidekick.server.plist && launchctl load -w ~/Library/LaunchAgents/com.logseq.sidekick.server.plist`
```

#### c) Update VERSION.md

**Location:** `VERSION.md`

**Add new version entry at top:**
```markdown
## Version 0.0.3 (TBD)

**Privacy Improvements:**
- 🔒 Default mode no longer logs search queries or graph names
- 🔒 Only logs health checks, startup, shutdown, and errors
- Added `--debug` flag for troubleshooting (with privacy warning)
- Debug mode displays prominent warning about logging user activity
- Clear messaging about privacy protection

**Breaking Changes:**
- Request logging now minimal by default (may affect debugging)
- Use `--debug` flag to see detailed request logs when needed
- Existing logs may contain historical search queries - consider clearing

**Migration:**
- No action required - privacy mode is automatic
- Clear existing logs: `cat /dev/null > /tmp/logseq-server.log`
- For debugging: add `--debug` flag when starting server

---
```

#### d) Update macos/install.sh

**Location:** `macos/install.sh` - end of file (after "Installation complete!")

**Add:**
```bash
echo ""
echo "Privacy Note:"
echo "  The server uses privacy-safe logging by default."
echo "  Search queries and graph names are NOT logged."
echo "  To enable debug logging (if needed): add --debug flag to plist"
echo "  See macos/README.md for details"
```

---

### 6. Update Startup Message

**Location:** `main()` function startup banner (around line 302)

**Change:**
```python
logging.info(f"Server v{VERSION} started on {args.host}:{args.port}")
```

**To:**
```python
if args.debug:
    logging.info(f"Server v{VERSION} started on {args.host}:{args.port} (DEBUG MODE)")
else:
    logging.info(f"Server v{VERSION} started on {args.host}:{args.port} (Privacy Mode)")
```

---

### 7. Update VERSION Constant

**Location:** `logseq_server.py` (around line 31)

**Change:**
```python
VERSION = '0.0.2'
```

**To:**
```python
VERSION = '0.0.3'
```

---

## Testing Plan

### Test Case 1: Default Mode (Privacy) ✅
```bash
# Start server normally
cd /Users/niyaro/Documents/Code/logseq-http-server
python3 logseq_server.py

# Expected startup message:
# "Server v0.0.3 started on localhost:8765 (Privacy Mode)"

# Make some searches via extension
# Search for: "taiwan", "joyce", "test query"

# Check log file
cat /tmp/logseq-server.log

# Expected: Only startup and health checks visible
# Should NOT see: search queries, graph names, or URLs
```

### Test Case 2: Debug Mode ⚠️
```bash
# Start with debug flag
python3 logseq_server.py --debug

# Expected: Should display warning banner
# Should wait 3 seconds before continuing
# Startup message: "Server v0.0.3 started on localhost:8765 (DEBUG MODE)"

# Make some searches via extension
# Check log file
cat /tmp/logseq-server.log

# Expected: Full logging with all search queries visible
```

### Test Case 3: LaunchAgent with Default Mode
```bash
# Ensure LaunchAgent plist does NOT have --debug flag
cat ~/Library/LaunchAgents/com.logseq.sidekick.server.plist | grep debug

# Should return nothing

# Restart LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
launchctl load -w ~/Library/LaunchAgents/com.logseq.sidekick.server.plist

# Use extension to make searches
# Check logs
tail -20 /tmp/logseq-server.log

# Expected: Health checks only, no search history
```

### Test Case 4: Error Logging Works in Privacy Mode
```bash
# Start server in privacy mode
python3 logseq_server.py

# Trigger an error (query non-existent graph, invalid command, etc.)
# Example: curl "http://localhost:8765/search?q=test&graph=NonExistentGraph"

# Check logs
tail /tmp/logseq-server.log

# Expected: Error IS logged even in privacy mode
```

### Test Case 5: Health Checks Still Logged
```bash
# Start server in privacy mode
python3 logseq_server.py

# Run health check
curl http://localhost:8765/health

# Check logs
tail /tmp/logseq-server.log

# Expected: Health check request logged
```

---

## Migration Notes

### For Existing Users Upgrading to 0.0.3

**Behavior Change:**
- Logs will be much quieter after upgrade (privacy mode by default)
- Existing logs may contain historical search queries from v0.0.2

**Recommended Actions:**
1. **Clear existing logs:** `cat /dev/null > /tmp/logseq-server.log`
2. **Restart server** to apply new privacy mode
3. **If debugging needed:** Use `--debug` flag (with awareness of privacy implications)

**Communication to Users:**
```
Version 0.0.3 Privacy Update

We've updated logging to protect your privacy. By default:
✅ No more plain-text search history in logs
✅ Health checks still logged for monitoring
✅ Errors still captured for troubleshooting

Your existing log file may contain search history from before this update.
Consider clearing it: cat /dev/null > /tmp/logseq-server.log

Need to debug an issue? Use: python3 logseq_server.py --debug
(Remember to clear logs after: cat /dev/null > /tmp/logseq-server.log)
```

---

## File Summary

### Files to Modify:
1. ✏️ `logseq_server.py` - Add flag, filter, warning, update VERSION
2. ✏️ `macos/README.md` - Document debug mode and privacy
3. ✏️ `macos/install.sh` - Add privacy note to installer
4. ✏️ `VERSION.md` - Document v0.0.3 changes

### New Code Sections:
- `PrivacyFilter` class (~25 lines)
- Debug warning banner (~20 lines)
- Argument parser addition (~2 lines)
- Logger configuration update (~10 lines)
- Documentation updates (~100 lines across files)

**Total Estimated Changes:** ~60 lines of code + ~100 lines of documentation

---

## Implementation Checklist

When implementing this plan, follow this order:

- [ ] **Step 1:** Update VERSION constant to 0.0.3
- [ ] **Step 2:** Add `--debug` argument to parser
- [ ] **Step 3:** Create `PrivacyFilter` class
- [ ] **Step 4:** Update logging configuration to use filter
- [ ] **Step 5:** Add debug warning banner
- [ ] **Step 6:** Update startup logging message
- [ ] **Step 7:** Update docstring at top of file
- [ ] **Step 8:** Test manually (both modes)
- [ ] **Step 9:** Update VERSION.md
- [ ] **Step 10:** Update macos/README.md
- [ ] **Step 11:** Update macos/install.sh
- [ ] **Step 12:** Test with LaunchAgent
- [ ] **Step 13:** Clear existing logs
- [ ] **Step 14:** Commit changes to git
- [ ] **Step 15:** Push to GitHub

---

## Benefits

### For Users:
- 🔒 Privacy by default - no search history logged
- 📊 Health monitoring still works
- 🐛 Debug mode available when needed
- ⚠️ Clear warnings when privacy is affected

### For Developers:
- 🛠️ Debug mode for troubleshooting
- 📝 Errors still logged for bug reports
- 🔍 Health checks help diagnose issues
- ✅ Industry-standard approach

---

## Risks & Mitigation

### Risk 1: Users can't debug issues
**Mitigation:** Clear documentation on enabling debug mode

### Risk 2: Users don't know about privacy improvement
**Mitigation:** Announce in release notes, update README prominently

### Risk 3: Debug mode left on accidentally
**Mitigation:**
- Prominent warning on startup
- 3-second pause to read warning
- Instructions to disable in warning message

### Risk 4: Breaking change for users who relied on logs
**Mitigation:**
- Debug mode provides same functionality
- Document migration path
- Explain benefits outweigh costs

---

## Future Enhancements (Post-0.0.3)

Consider for later versions:
- Config file to persist debug mode preference
- Log rotation to prevent log file growth
- Sanitized summary logs (e.g., "5 searches performed" without content)
- Option to encrypt logs when debug mode is enabled
- Separate log levels (ERROR, WARNING, INFO) with finer control

---

## Questions / Discussion Notes

**Q: Should health checks be logged?**
A: Yes - they contain no sensitive data and help verify server is running.

**Q: What about error messages that might contain queries?**
A: Errors are always logged (needed for debugging). If query is in error message, it will be logged even in privacy mode. This is acceptable trade-off for troubleshooting critical issues.

**Q: Should we add config file support?**
A: Not in v0.0.3 - keep it simple. Command-line flag is sufficient for now.

---

**Status:** Ready to implement
**Next Step:** Follow implementation checklist above
