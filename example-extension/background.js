/**
 * Background script for Logseq Copilot (HTTP version)
 * Communicates with the local HTTP server for Logseq CLI access
 */

const API_BASE_URL = 'http://localhost:8080';

/**
 * Make a request to the Logseq HTTP API
 * @param {string} endpoint - API endpoint (e.g., '/list', '/search')
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>}
 */
async function callAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('API call failed:', error);

    // Check if server is running
    if (error.message.includes('Failed to fetch')) {
      throw new Error('Cannot connect to Logseq server. Is it running? Start it with: python3 logseq_server.py');
    }

    throw error;
  }
}

/**
 * List all Logseq graphs
 */
async function listGraphs() {
  return await callAPI('/list');
}

/**
 * Show info about a specific graph
 */
async function showGraph(graphName) {
  return await callAPI(`/show?graph=${encodeURIComponent(graphName)}`);
}

/**
 * Search in graphs
 */
async function search(query, graphName = null) {
  let url = `/search?q=${encodeURIComponent(query)}`;
  if (graphName) {
    url += `&graph=${encodeURIComponent(graphName)}`;
  }
  return await callAPI(url);
}

/**
 * Execute a datalog query
 */
async function query(graphName, queryString) {
  return await callAPI('/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      graph: graphName,
      query: queryString
    })
  });
}

/**
 * Check if server is healthy
 */
async function checkHealth() {
  return await callAPI('/health');
}

// Message handler for popup and content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Received message:', request);

  switch (request.action) {
    case 'health':
      checkHealth()
        .then(sendResponse)
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;

    case 'listGraphs':
      listGraphs()
        .then(sendResponse)
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;

    case 'showGraph':
      showGraph(request.graph)
        .then(sendResponse)
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;

    case 'search':
      search(request.query, request.graph)
        .then(sendResponse)
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;

    case 'query':
      query(request.graph, request.query)
        .then(sendResponse)
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true;

    default:
      sendResponse({ success: false, error: 'Unknown action' });
  }
});

console.log('Logseq Copilot (HTTP) background script loaded');
