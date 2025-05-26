/**
 * Main application logic for Browser Extension OSINT Tool
 */

// Initialize API client
const api = new ExtensionAPI();

// DOM elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const bulkInput = document.getElementById('bulkInput');
const resultsContent = document.getElementById('resultsContent');

// Store checkboxes
const storeCheckboxes = {
    chrome: document.getElementById('searchChrome'),
    firefox: document.getElementById('searchFirefox'),
    edge: document.getElementById('searchEdge'),
};

/**
 * Get selected stores
 */
function getSelectedStores() {
    return Object.entries(storeCheckboxes)
        .filter(([_, checkbox]) => checkbox.checked)
        .map(([store, _]) => store);
}

/**
 * Perform single extension search
 */
async function performSearch() {
    const extensionId = searchInput.value.trim();
    
    if (!extensionId) {
        showError('Please enter an extension ID');
        return;
    }

    // Validate extension ID format (basic check)
    if (!/^[a-zA-Z0-9\-_@.{}]{1,}$/.test(extensionId)) {
        showError('Invalid extension ID format');
        return;
    }

    const stores = getSelectedStores();
    if (stores.length === 0) {
        showError('Please select at least one store to search');
        return;
    }

    // Disable search button and show loading
    searchBtn.disabled = true;
    showLoading(`Searching ${stores.join(', ')} for ${extensionId}...`);

    try {
        const response = await api.searchExtension(extensionId, stores);
        displayResults(response.results, extensionId);
    } catch (error) {
        showError(`Error: ${error.message}`);
    } finally {
        searchBtn.disabled = false;
    }
}

/**
 * Perform bulk search
 */
async function performBulkSearch() {
    const bulkInputValue = bulkInput.value.trim();
    
    if (!bulkInputValue) {
        showError('Please enter extension IDs for bulk search');
        return;
    }

    const ids = bulkInputValue.split('\n')
        .map(id => id.trim())
        .filter(id => id);
    
    const stores = getSelectedStores();
    if (stores.length === 0) {
        showError('Please select at least one store to search');
        return;
    }

    showLoading(`Searching for ${ids.length} extensions...`);

    try {
        const response = await api.bulkSearch(ids, stores);
        displayBulkResults(response.results, ids.length);
    } catch (error) {
        showError(`Error: ${error.message}`);
    }
}

/**
 * Display search results
 */
function displayResults(results, query) {
    const foundResults = results.filter(r => r.found);
    
    if (foundResults.length === 0) {
        showNoResults(`Extension "${query}" not found in selected stores`);
        return;
    }

    // Check if any results are cached
    const hasCached = results.some(r => r.cached);
    const status = hasCached ? 
        '<span class="status-cached">✓ Some results from cache</span>' : 
        '<span class="status-fetched">✓ Fresh results</span>';

    const statsHtml = `
        <div class="stats">
            <span>Found in ${foundResults.length} store${foundResults.length !== 1 ? 's' : ''}</span>
            <span>Extension ID: ${escapeHtml(query)} ${status}</span>
        </div>
    `;

    const resultsHtml = foundResults.map(ext => `
        <div class="result-item">
            <div class="result-header">
                <div>
                    <div class="result-name">${escapeHtml(ext.name)}</div>
                    <span class="store-badge store-${ext.store_source}">${ext.store_source}</span>
                </div>
                <div class="result-id">${escapeHtml(ext.extension_id)}</div>
            </div>
            <div class="result-meta">
                <span><strong>Publisher:</strong> <span class="publisher">${escapeHtml(ext.publisher || 'Unknown')}</span></span>
                <span><strong>Users:</strong> ${escapeHtml(ext.user_count || 'N/A')}</span>
                <span><strong>Rating:</strong> ${ext.rating ? '⭐ ' + ext.rating : 'N/A'}</span>
                <span><strong>Version:</strong> ${escapeHtml(ext.version || 'N/A')}</span>
            </div>
            <div class="result-description">${escapeHtml(ext.description || 'No description available')}</div>
            ${ext.store_url ? `<a href="${escapeHtml(ext.store_url)}" target="_blank" rel="noopener noreferrer" style="color: var(--ctp-blue); text-decoration: none;">View in Store →</a>` : ''}
        </div>
    `).join('');

    resultsContent.innerHTML = statsHtml + resultsHtml;
}

/**
 * Display bulk search results
 */
function displayBulkResults(results, totalSearched) {
    const allResults = [];
    
    // Flatten results
    for (const [extensionId, extensionResults] of Object.entries(results)) {
        allResults.push(...extensionResults.filter(r => r.found));
    }
    
    if (allResults.length === 0) {
        showNoResults(`No extensions found from ${totalSearched} IDs`);
        return;
    }

    const statsHtml = `
        <div class="stats">
            <span>Found ${allResults.length} extension${allResults.length !== 1 ? 's' : ''} from ${totalSearched} IDs</span>
            <span>Bulk search complete</span>
        </div>
    `;

    const resultsHtml = allResults.map(ext => `
        <div class="result-item">
            <div class="result-header">
                <div>
                    <div class="result-name">${escapeHtml(ext.name)}</div>
                    <span class="store-badge store-${ext.store_source}">${ext.store_source}</span>
                </div>
                <div class="result-id">${escapeHtml(ext.extension_id)}</div>
            </div>
            <div class="result-meta">
                <span><strong>Publisher:</strong> <span class="publisher">${escapeHtml(ext.publisher || 'Unknown')}</span></span>
                <span><strong>Users:</strong> ${escapeHtml(ext.user_count || 'N/A')}</span>
                <span><strong>Rating:</strong> ${ext.rating ? '⭐ ' + ext.rating : 'N/A'}</span>
            </div>
            <div class="result-description">${escapeHtml(ext.description || 'No description available')}</div>
        </div>
    `).join('');

    resultsContent.innerHTML = statsHtml + resultsHtml;
}

/**
 * Show loading state
 */
function showLoading(message) {
    resultsContent.innerHTML = `
        <div class="loading">
            <div class="loading-spinner"></div>
            <div class="loading-text">${escapeHtml(message)}</div>
        </div>
    `;
}

/**
 * Show no results message
 */
function showNoResults(message) {
    resultsContent.innerHTML = `
        <div class="no-results">${escapeHtml(message)}</div>
    `;
}

/**
 * Show error message
 */
function showError(message) {
    resultsContent.innerHTML = `
        <div class="error-message">${escapeHtml(message)}</div>
    `;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

/**
 * Initialize the application
 */
async function init() {
    // Check API health
    const isHealthy = await api.healthCheck();
    if (!isHealthy) {
        console.warn('API health check failed - using mock data mode');
    }

    // Add event listeners
    searchBtn.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });

    // Load stats on page load
    try {
        const stats = await api.getStats();
        console.log('Cache stats:', stats);
    } catch (error) {
        console.log('Could not load stats:', error);
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Make performBulkSearch available globally for onclick
window.performSearch = performSearch;
window.performBulkSearch = performBulkSearch;
