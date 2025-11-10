# Logseq HTTP Server

A simple HTTP server that provides REST API access to Logseq CLI commands. Enables browser extensions and other applications to query Logseq DB graphs without requiring the Logseq Desktop app to be running.

## Features

- ✅ **Works independently** - Logseq Desktop does NOT need to be running
- ✅ **DB Graphs only** - Works with Logseq database graphs
- ✅ **Full-text search** - Search across all block content, not just titles
- ✅ **Simple setup** - Just run one command
- ✅ **Browser agnostic** - Works with any browser
- ✅ **Easy to debug** - Test with curl or browser
- ✅ **CORS enabled** - Works with browser extensions
- ✅ **Comprehensive logging** - All requests logged

## Prerequisites

### Required

1. **Python 3** (macOS ships with Python 3)
   ```bash
   python3 --version
   ```

2. **Logseq CLI**
   ```bash
   npm install -g @logseq/cli
   # or
   yarn global add @logseq/cli
   ```

   Verify:
   ```bash
   logseq --version
   ```

3. **jet** (EDN to JSON converter)
   ```bash
   brew install borkdude/brew/jet
   ```

   Verify:
   ```bash
   jet --version
   ```

4. **Logseq DB graphs** - The CLI only works with Logseq DB (database) graphs, not file-based/markdown graphs.

## Quick Start

### 1. Start the Server

```bash
cd /Users/niyaro/Documents/Code/logseq-http-server
python3 logseq_server.py
```

The server will start on `http://localhost:8765`

### 2. Test It

Open a browser and visit:
- Health check: http://localhost:8765/health
- List graphs: http://localhost:8765/list

Or use curl:
```bash
curl http://localhost:8765/list
```

### 3. Use the Example Extension

1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `/Users/niyaro/Documents/Code/logseq-http-server/example-extension`
5. Click the extension icon - it should connect automatically!

## API Documentation

### Base URL
```
http://localhost:8765
```

### Endpoints

#### Health Check
```
GET /health
```
Check if server is running.

**Response:**
```json
{
  "status": "healthy",
  "message": "Logseq HTTP Server is running"
}
```

#### List Graphs
```
GET /list
```
List all available Logseq DB graphs.

**Response:**
```json
{
  "success": true,
  "stdout": "DB Graphs:\n  research-notes\n  personal\n",
  "stderr": "",
  "returncode": 0
}
```

#### Show Graph Info
```
GET /show?graph=GRAPH_NAME
```
Show information about a specific graph.

**Parameters:**
- `graph` (required) - Graph name

**Example:**
```bash
curl "http://localhost:8765/show?graph=research-notes"
```

#### Search
```
GET /search?q=QUERY[&graph=GRAPH_NAME]
```
Search across graphs or in a specific graph. Performs full-text search across all block content.

**Parameters:**
- `q` (required) - Search query
- `graph` (optional) - Limit search to specific graph

**Example:**
```bash
curl "http://localhost:8765/search?q=anthropology"
curl "http://localhost:8765/search?q=anthropology&graph=research-notes"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "block/uuid": "...",
      "block/title": "...",
      "block/page": {...}
    }
  ],
  "returncode": 0
}
```

#### Execute Query
```
POST /query
Content-Type: application/json

{
  "graph": "GRAPH_NAME",
  "query": "DATALOG_QUERY"
}
```
Execute a datalog query on a graph.

**Body:**
```json
{
  "graph": "research-notes",
  "query": "[:find (pull ?b [:block/uuid :block/title :block/page]) :where [?b :block/title ?t] [(clojure.string/includes? ?t \"keyword\")]]"
}
```

**Example:**
```bash
curl -X POST http://localhost:8765/query \
  -H "Content-Type: application/json" \
  -d '{"graph":"research-notes","query":"[:find (pull ?b [*]) :where [?b :block/content]]"}'
```

### Response Format

All endpoints return JSON with this structure:

```json
{
  "success": true|false,
  "stdout": "command output",
  "stderr": "error output if any",
  "returncode": 0,
  "data": {}  // Parsed JSON if stdout is JSON
}
```

## Usage from Chrome Extension

### manifest.json
```json
{
  "manifest_version": 3,
  "permissions": ["storage"],
  "host_permissions": ["http://localhost:8765/*"]
}
```

### JavaScript
```javascript
// List graphs
const response = await fetch('http://localhost:8765/list');
const data = await response.json();
console.log(data.stdout);

// Search
const searchResponse = await fetch(
  'http://localhost:8765/search?q=keyword'
);
const searchData = await searchResponse.json();

// Execute query
const queryResponse = await fetch('http://localhost:8765/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    graph: 'my-graph',
    query: '[:find (pull ?b [:block/uuid :block/title]) :where [?b :block/title]]'
  })
});
```

## Command Line Options

```bash
python3 logseq_server.py [--port PORT] [--host HOST]
```

**Options:**
- `--port` - Port to listen on (default: 8765)
- `--host` - Host to bind to (default: localhost)

**Examples:**
```bash
# Use a different port
python3 logseq_server.py --port 9000

# Allow connections from other machines (be careful!)
python3 logseq_server.py --host 0.0.0.0
```

## Logging

All requests are logged to:
- **File**: `logseq-http-server.log` (in server directory)
- **Console**: stdout

View logs in real-time:
```bash
tail -f logseq-http-server.log
```

## Security Considerations

### CORS Policy

By default, the server allows requests from **any origin** (`Access-Control-Allow-Origin: *`). This is fine for local development.

For production, edit `logseq_server.py` and restrict CORS:

```python
# In _set_headers method, change:
self.send_header('Access-Control-Allow-Origin', '*')

# To:
self.send_header('Access-Control-Allow-Origin', 'chrome-extension://YOUR_EXTENSION_ID')
```

### Network Binding

By default, the server only listens on `localhost`, making it inaccessible from other machines. Keep it this way unless you specifically need remote access.

### Command Whitelist

The server only executes safe Logseq CLI commands (`list`, `show`, `search`, `query`, `export`). No arbitrary shell execution is possible.

## Troubleshooting

### "logseq command not found"

Install the Logseq CLI:
```bash
npm install -g @logseq/cli
```

Verify installation:
```bash
which logseq
logseq --version
```

### "jet command not found"

Install jet:
```bash
brew install borkdude/brew/jet
```

Verify installation:
```bash
which jet
jet --version
```

### "Cannot connect to server"

Make sure the server is running:
```bash
python3 logseq_server.py
```

Check the logs:
```bash
tail -f logseq-http-server.log
```

### "No graphs listed" or "Graph not found"

The CLI only works with **Logseq DB graphs**.

Verify graphs are accessible:
```bash
logseq list
```

### Port already in use

Use a different port:
```bash
python3 logseq_server.py --port 9000
```

Then update your extension to use the new port.

## Running in Background

### macOS/Linux - Using nohup
```bash
nohup python3 logseq_server.py > /dev/null 2>&1 &
```

Stop it:
```bash
pkill -f logseq_server.py
```

### macOS - Using launchd (Auto-start on login)

Create `~/Library/LaunchAgents/com.logseq.sidekick.server.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.logseq.sidekick.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/niyaro/Documents/Code/logseq-http-server/logseq_server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
```

Unload it:
```bash
launchctl unload ~/Library/LaunchAgents/com.logseq.sidekick.server.plist
```

## Integration with Logseq DB Sidekick

To use this server with the Logseq DB Sidekick extension:

1. Start the HTTP server (see Quick Start above)

2. Install and configure the extension:
   - Set server URL to `http://localhost:8765`
   - Select your graph from the dropdown
   - Click "Connect" to verify connection

3. Browse the web - relevant notes will appear when you search!

## Technical Details

### How It Works

1. Extension sends HTTP request to server
2. Server executes `logseq` CLI command
3. CLI returns results in EDN format (Clojure data notation)
4. Server pipes output through `jet` to convert EDN → JSON
5. Server returns JSON to extension
6. Extension displays results in browser

### Dependencies

- **@logseq/cli** - Official Logseq command-line interface
- **jet** - EDN to JSON converter (https://github.com/borkdude/jet)
- **Python 3** - Standard library only, no pip packages needed

## License

MIT

## Contributing

Contributions welcome! This is a simple tool - feel free to fork and improve.
