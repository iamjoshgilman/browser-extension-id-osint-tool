/**
 * API client for Browser Extension OSINT Tool
 */

class ExtensionAPI {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.headers = {
            'Content-Type': 'application/json',
        };
        
        // Check if API key is required
        const apiKey = localStorage.getItem('api_key');
        if (apiKey) {
            this.headers['X-API-Key'] = apiKey;
        }
    }

    /**
     * Set API key for authenticated requests
     */
    setAPIKey(apiKey) {
        if (apiKey) {
            this.headers['X-API-Key'] = apiKey;
            localStorage.setItem('api_key', apiKey);
        } else {
            delete this.headers['X-API-Key'];
            localStorage.removeItem('api_key');
        }
    }

    /**
     * Make an API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.headers,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Search for an extension
     */
    async searchExtension(extensionId, stores = ['chrome', 'firefox', 'edge']) {
        return this.request('/search', {
            method: 'POST',
            body: JSON.stringify({
                extension_id: extensionId,
                stores: stores,
            }),
        });
    }

    /**
     * Bulk search for multiple extensions
     */
    async bulkSearch(extensionIds, stores = ['chrome', 'firefox', 'edge']) {
        return this.request('/bulk-search', {
            method: 'POST',
            body: JSON.stringify({
                extension_ids: extensionIds,
                stores: stores,
            }),
        });
    }

    /**
     * Get cache statistics
     */
    async getStats() {
        return this.request('/stats', {
            method: 'GET',
        });
    }

    /**
     * Health check
     */
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }
}

// Export for use in other scripts
window.ExtensionAPI = ExtensionAPI;
