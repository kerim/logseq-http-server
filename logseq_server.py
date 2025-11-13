#!/usr/bin/env python3
"""
Logseq CLI HTTP Server

A simple HTTP server that provides REST API access to Logseq CLI commands.
Enables browser extensions and other applications to query Logseq graphs
without requiring the Logseq Desktop app to be running.

Usage:
    python3 logseq_server.py [--port PORT] [--host HOST]

API Endpoints:
    GET  /health                        - Health check
    GET  /version                       - Get server version
    GET  /list                          - List all graphs
    GET  /show?graph=name               - Show graph info
    GET  /search?q=query[&graph=name]   - Search graphs
    POST /query                         - Execute datalog query
         Body: {"graph": "name", "query": "..."}

"""

import http.server
import json
import subprocess
import urllib.parse
import argparse
import logging
import os
from pathlib import Path

# Version
VERSION = '0.0.2'

# Configuration
DEFAULT_PORT = 8765
DEFAULT_HOST = 'localhost'
LOG_FILE = Path(__file__).parent / 'logseq-http-server.log'
LOGSEQ_BIN = '/opt/homebrew/bin/logseq'  # Full path to logseq CLI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class LogseqHTTPHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for Logseq CLI commands."""

    def _set_headers(self, status=200, content_type='application/json'):
        """Set response headers including CORS."""
        self.send_response(status)
        self.send_header('Content-Type', content_type)

        # CORS headers - allow all origins for development
        # For production, restrict to specific extension origins
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

        self.end_headers()

    def _send_json(self, data, status=200):
        """Send JSON response."""
        self._set_headers(status)
        response = json.dumps(data, indent=2).encode('utf-8')
        self.wfile.write(response)

    def _send_error_json(self, message, status=400):
        """Send error response."""
        self._send_json({'success': False, 'error': message}, status)

    def _execute_logseq_command(self, command, args=None):
        """
        Execute a logseq CLI command.

        Args:
            command: Command name (list, show, search, query, etc.)
            args: List of additional arguments

        Returns:
            dict: Response with success, stdout, stderr, and optional data
        """
        if args is None:
            args = []

        cmd = [LOGSEQ_BIN, command] + args

        logging.info(f"Executing: {' '.join(cmd)}")

        try:
            # Use full environment to ensure CLI has access to all necessary paths
            env = os.environ.copy()

            # For query commands, pipe through jet to convert EDN to JSON
            if command == 'query':
                # Run logseq query and pipe to jet
                logseq_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=env
                )

                jet_process = subprocess.Popen(
                    ['jet', '--to', 'json'],
                    stdin=logseq_process.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Allow logseq_process to receive a SIGPIPE if jet_process exits
                logseq_process.stdout.close()

                # Get output from jet
                stdout, jet_stderr = jet_process.communicate(timeout=30)
                logseq_stderr = logseq_process.stderr.read() if logseq_process.stderr else ""

                returncode = jet_process.returncode
                stderr = jet_stderr + logseq_stderr
            else:
                # For non-query commands, run normally
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env=env
                )
                stdout = result.stdout
                stderr = result.stderr
                returncode = result.returncode

            response = {
                'success': returncode == 0,
                'stdout': stdout,
                'stderr': stderr,
                'returncode': returncode
            }

            # Try to parse stdout as JSON if it looks like JSON
            stdout_stripped = stdout.strip()
            if stdout_stripped and (stdout_stripped.startswith('{') or stdout_stripped.startswith('[')):
                try:
                    response['data'] = json.loads(stdout_stripped)
                except json.JSONDecodeError:
                    pass

            return response

        except subprocess.TimeoutExpired:
            logging.error("Command timed out")
            return {
                'success': False,
                'error': 'Command execution timed out after 30 seconds'
            }
        except FileNotFoundError:
            logging.error("logseq command not found")
            return {
                'success': False,
                'error': 'logseq CLI not found. Install with: npm install -g @logseq/cli'
            }
        except Exception as e:
            logging.error(f"Error executing command: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self._set_headers(204)

    def do_GET(self):
        """Handle GET requests."""
        # Parse URL
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        logging.info(f"GET {path} - {params}")

        # Route handlers
        if path == '/health':
            self._send_json({'status': 'healthy', 'message': 'Logseq HTTP Server is running'})

        elif path == '/version':
            self._send_json({'version': VERSION})

        elif path == '/list':
            response = self._execute_logseq_command('list')
            self._send_json(response)

        elif path == '/show':
            graph = params.get('graph', [None])[0]
            if not graph:
                self._send_error_json('Missing required parameter: graph')
                return

            response = self._execute_logseq_command('show', [graph])
            self._send_json(response)

        elif path == '/search':
            query = params.get('q', [None])[0]
            if not query:
                self._send_error_json('Missing required parameter: q')
                return

            graph = params.get('graph', [None])[0]

            # Use datalog query instead of search for structured results
            # DB graphs use :block/title for content, not :block/content
            # Build datalog query: find blocks where title contains search term
            if not graph:
                self._send_error_json('Missing required field: graph')
                return

            # Escape double quotes in query for safe inclusion in datalog
            escaped_query_lower = query.replace('"', '\\"').lower()
            escaped_query_orig = query.replace('"', '\\"')

            # Datalog query to search for PAGES (not blocks) by page name OR title
            # Search both name (lowercase) and title (mixed case) for better coverage
            # This provides case-insensitive search by matching either field
            # Returns page info: uuid, name, title, journal-day
            datalog_query = f'[:find (pull ?p [:db/id :block/uuid :block/name :block/title :block/journal-day]) :where [?p :block/name ?name] [?p :block/title ?title] (or [(clojure.string/includes? ?name "{escaped_query_lower}")] [(clojure.string/includes? ?title "{escaped_query_orig}")])]'

            response = self._execute_logseq_command('query', [graph, datalog_query])
            self._send_json(response)

        else:
            self._send_error_json(f'Unknown endpoint: {path}', 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        logging.info(f"POST {path}")

        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self._send_error_json('Invalid JSON in request body')
            return

        # Route handlers
        if path == '/query':
            graph = data.get('graph')
            query = data.get('query')

            if not graph:
                self._send_error_json('Missing required field: graph')
                return
            if not query:
                self._send_error_json('Missing required field: query')
                return

            response = self._execute_logseq_command('query', [graph, query])
            self._send_json(response)

        else:
            self._send_error_json(f'Unknown endpoint: {path}', 404)

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logging.info(format % args)


def main():
    """Start the HTTP server."""
    parser = argparse.ArgumentParser(description='Logseq CLI HTTP Server')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'Port to listen on (default: {DEFAULT_PORT})')
    parser.add_argument('--host', type=str, default=DEFAULT_HOST,
                        help=f'Host to bind to (default: {DEFAULT_HOST})')

    args = parser.parse_args()

    server_address = (args.host, args.port)
    httpd = http.server.HTTPServer(server_address, LogseqHTTPHandler)

    print(f"{'='*60}")
    print(f"Logseq HTTP Server v{VERSION}")
    print(f"{'='*60}")
    print(f"Listening on: http://{args.host}:{args.port}")
    print(f"Log file: {LOG_FILE}")
    print(f"\nEndpoints:")
    print(f"  GET  /health")
    print(f"  GET  /version")
    print(f"  GET  /list")
    print(f"  GET  /show?graph=NAME")
    print(f"  GET  /search?q=QUERY[&graph=NAME]")
    print(f"  POST /query (body: {{\"graph\": \"NAME\", \"query\": \"...\"}})")
    print(f"\nPress Ctrl+C to stop")
    print(f"{'='*60}\n")

    logging.info(f"Server v{VERSION} started on {args.host}:{args.port}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        logging.info("Server stopped by user")
        httpd.shutdown()


if __name__ == '__main__':
    main()
