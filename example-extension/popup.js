/**
 * Popup script for Logseq Copilot (HTTP version)
 */

const resultsDiv = document.getElementById('results');
const graphSelect = document.getElementById('graphSelect');
const searchInput = document.getElementById('searchInput');
const queryInput = document.getElementById('queryInput');
const statusSpan = document.getElementById('status');
const serverInfo = document.getElementById('serverInfo');

// Display results
function displayResults(data, isError = false) {
  resultsDiv.className = isError ? 'error show' : 'success show';

  if (typeof data === 'object') {
    resultsDiv.textContent = JSON.stringify(data, null, 2);
  } else {
    resultsDiv.textContent = data;
  }
}

// Hide results
function hideResults() {
  resultsDiv.classList.remove('show');
}

// Update connection status
function updateStatus(connected) {
  if (connected) {
    statusSpan.textContent = 'Connected';
    statusSpan.className = 'status connected';
    serverInfo.style.display = 'none';
  } else {
    statusSpan.textContent = 'Disconnected';
    statusSpan.className = 'status disconnected';
    serverInfo.style.display = 'block';
  }
}

// Send message to background script
function sendMessage(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

// Check server health
async function checkHealth() {
  try {
    const response = await sendMessage({ action: 'health' });
    updateStatus(response.success || response.status === 'healthy');
    return response.success || response.status === 'healthy';
  } catch (error) {
    updateStatus(false);
    return false;
  }
}

// List graphs
async function listGraphs() {
  try {
    displayResults('Loading graphs...', false);

    const response = await sendMessage({ action: 'listGraphs' });

    if (response.success) {
      const output = response.stdout;
      displayResults(output, false);

      // Parse graph names (simplified)
      const lines = output.split('\n');
      const graphNames = lines
        .filter(line => line.trim() && !line.includes(':') &&
                line.trim() !== 'DB Graphs' && line.trim() !== 'File Graphs')
        .map(line => line.trim());

      // Populate dropdown
      graphSelect.innerHTML = '<option value="">-- Select a graph --</option>';
      graphNames.forEach(name => {
        const option = document.createElement('option');
        option.value = name;
        option.textContent = name;
        graphSelect.appendChild(option);
      });

    } else {
      displayResults(`Error: ${response.error || response.stderr}`, true);
    }
  } catch (error) {
    displayResults(`Failed to list graphs: ${error.message}`, true);
  }
}

// Search
async function search() {
  const query = searchInput.value.trim();
  const graph = graphSelect.value;

  if (!query) {
    displayResults('Please enter a search query', true);
    return;
  }

  try {
    displayResults('Searching...', false);

    const response = await sendMessage({
      action: 'search',
      query: query,
      graph: graph || null
    });

    if (response.success) {
      displayResults(response.stdout || 'No results found', false);
    } else {
      displayResults(`Error: ${response.error || response.stderr}`, true);
    }
  } catch (error) {
    displayResults(`Search failed: ${error.message}`, true);
  }
}

// Execute query
async function executeQuery() {
  const query = queryInput.value.trim();
  const graph = graphSelect.value;

  if (!query) {
    displayResults('Please enter a query', true);
    return;
  }

  if (!graph) {
    displayResults('Please select a graph', true);
    return;
  }

  try {
    displayResults('Executing query...', false);

    const response = await sendMessage({
      action: 'query',
      graph: graph,
      query: query
    });

    if (response.success) {
      displayResults(response.data || response.stdout || 'Query executed successfully', false);
    } else {
      displayResults(`Error: ${response.error || response.stderr}`, true);
    }
  } catch (error) {
    displayResults(`Query failed: ${error.message}`, true);
  }
}

// Event listeners
document.getElementById('listGraphs').addEventListener('click', listGraphs);
document.getElementById('refreshGraphs').addEventListener('click', listGraphs);
document.getElementById('searchBtn').addEventListener('click', search);
document.getElementById('queryBtn').addEventListener('click', executeQuery);

searchInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') search();
});

queryInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && e.metaKey) executeQuery();
});

// Initialize
checkHealth().then(connected => {
  if (connected) {
    listGraphs();
  }
});
