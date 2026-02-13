"""
API endpoint tests
"""
import pytest
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    app.config['API_KEY_REQUIRED'] = False
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'version' in data

def test_search_extension(client):
    """Test search endpoint"""
    response = client.post('/api/search',
                          json={
                              'extension_id': 'cjpalhdlnbpafiamejdnhcphjbkeiagm',
                              'stores': ['chrome']
                          })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'extension_id' in data
    assert 'results' in data
    assert isinstance(data['results'], list)

def test_search_invalid_request(client):
    """Test search with invalid request"""
    response = client.post('/api/search', json={})
    assert response.status_code == 400

    # Sending invalid data without proper Content-Type returns 415
    response = client.post('/api/search', data="invalid")
    assert response.status_code == 415

def test_bulk_search(client):
    """Test bulk search endpoint"""
    response = client.post('/api/bulk-search',
                          json={
                              'extension_ids': ['cjpalhdlnbpafiamejdnhcphjbkeiagm'],
                              'stores': ['chrome']
                          })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'results' in data

def test_bulk_search_limit(client):
    """Test bulk search limit"""
    # Create list of 51 IDs (over the limit)
    ids = ['test' + str(i) for i in range(51)]
    response = client.post('/api/bulk-search',
                          json={
                              'extension_ids': ids,
                              'stores': ['chrome']
                          })
    assert response.status_code == 400

def test_stats_endpoint(client):
    """Test statistics endpoint"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_cached' in data

def test_404_error(client):
    """Test 404 error handling"""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_api_key_required(monkeypatch):
    """Test API key authentication when enabled"""
    # Set environment variable since decorator checks os.environ directly
    monkeypatch.setenv('API_KEY_REQUIRED', 'true')
    app.config['TESTING'] = True
    app.config['API_KEY'] = 'test-key-123'

    with app.test_client() as client:
        # Without API key
        response = client.post('/api/search',
                              json={'extension_id': 'test', 'stores': ['chrome']})
        assert response.status_code == 401

        # With wrong API key
        response = client.post('/api/search',
                              headers={'X-API-Key': 'wrong-key'},
                              json={'extension_id': 'test', 'stores': ['chrome']})
        assert response.status_code == 401

        # With correct API key
        response = client.post('/api/search',
                              headers={'X-API-Key': 'test-key-123'},
                              json={'extension_id': 'test', 'stores': ['chrome']})
        assert response.status_code != 401

def test_search_by_name(client):
    """Test the /api/search-by-name endpoint returns correct structure"""
    response = client.post('/api/search-by-name',
                          json={
                              'name': 'ublock origin',
                              'limit': 5
                          })
    assert response.status_code == 200
    data = json.loads(response.data)

    # Check response structure
    assert 'name' in data
    assert data['name'] == 'ublock origin'
    assert 'results' in data
    assert isinstance(data['results'], dict)
    assert 'search_urls' in data
    assert isinstance(data['search_urls'], dict)

    # Check that all stores have search URLs
    assert 'chrome' in data['search_urls']
    assert 'firefox' in data['search_urls']
    assert 'edge' in data['search_urls']

    # Check results has entries for stores
    assert 'chrome' in data['results']
    assert 'firefox' in data['results']
    assert 'edge' in data['results']

def test_search_by_name_missing_name(client):
    """Test validation when name is missing"""
    # Empty name
    response = client.post('/api/search-by-name',
                          json={
                              'name': ''
                          })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

    # Missing name field
    response = client.post('/api/search-by-name',
                          json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_search_with_include_permissions(client):
    """Test that include_permissions parameter is accepted in /api/search"""
    response = client.post('/api/search',
                          json={
                              'extension_id': 'cjpalhdlnbpafiamejdnhcphjbkeiagm',
                              'stores': ['chrome'],
                              'include_permissions': True
                          })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'extension_id' in data
    assert 'results' in data
    assert isinstance(data['results'], list)

def test_extension_history_missing_store(client):
    """Test extension history endpoint returns 400 when store parameter is missing"""
    response = client.get('/api/extension/test123/history')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'required' in data['error'].lower()

def test_extension_history_invalid_store(client):
    """Test extension history endpoint returns 400 for invalid store"""
    response = client.get('/api/extension/test123/history?store=invalid')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'invalid' in data['error'].lower()

def test_extension_history_empty(client):
    """Test extension history endpoint returns 200 with empty snapshots for unknown extension"""
    response = client.get('/api/extension/nonexistent123/history?store=chrome')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'extension_id' in data
    assert data['extension_id'] == 'nonexistent123'
    assert 'store' in data
    assert data['store'] == 'chrome'
    assert 'snapshots' in data
    assert isinstance(data['snapshots'], list)
    assert len(data['snapshots']) == 0
    assert 'total_snapshots' in data
    assert data['total_snapshots'] == 0
    assert 'has_permission_changes' in data
    assert data['has_permission_changes'] == False

def test_async_bulk_search_submit(client):
    """Test submitting async bulk search job"""
    response = client.post('/api/bulk-search-async',
                          json={
                              'extension_ids': ['cjpalhdlnbpafiamejdnhcphjbkeiagm'],
                              'stores': ['chrome']
                          })
    assert response.status_code == 202
    data = json.loads(response.data)
    assert 'job_id' in data
    assert 'status' in data
    assert data['status'] == 'pending'
    assert 'total_tasks' in data
    assert data['total_tasks'] == 1
    assert 'poll_url' in data
    assert 'stream_url' in data

def test_async_bulk_search_missing_ids(client):
    """Test async bulk search without extension_ids"""
    response = client.post('/api/bulk-search-async',
                          json={
                              'stores': ['chrome']
                          })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_async_bulk_search_too_many_ids(client):
    """Test async bulk search with too many extension IDs"""
    ids = ['test' + str(i) for i in range(51)]
    response = client.post('/api/bulk-search-async',
                          json={
                              'extension_ids': ids,
                              'stores': ['chrome']
                          })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_async_bulk_search_status(client):
    """Test getting async bulk search status"""
    # Submit job
    response = client.post('/api/bulk-search-async',
                          json={
                              'extension_ids': ['cjpalhdlnbpafiamejdnhcphjbkeiagm'],
                              'stores': ['chrome']
                          })
    assert response.status_code == 202
    data = json.loads(response.data)
    job_id = data['job_id']

    # Get status
    response = client.get(f'/api/bulk-search-async/{job_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'job_id' in data
    assert data['job_id'] == job_id
    assert 'status' in data
    assert 'total_tasks' in data
    assert 'completed_tasks' in data
    assert 'failed_tasks' in data
    assert 'progress_pct' in data

def test_async_bulk_search_status_not_found(client):
    """Test getting status for non-existent job"""
    response = client.get('/api/bulk-search-async/nonexistent-job-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data

def test_async_bulk_search_cancel(client):
    """Test cancelling async bulk search job"""
    # Submit job
    response = client.post('/api/bulk-search-async',
                          json={
                              'extension_ids': ['test1', 'test2', 'test3'],
                              'stores': ['chrome', 'firefox', 'edge']
                          })
    assert response.status_code == 202
    data = json.loads(response.data)
    job_id = data['job_id']

    # Cancel job
    response = client.delete(f'/api/bulk-search-async/{job_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'job_id' in data
    assert data['job_id'] == job_id
    assert 'status' in data
    assert data['status'] == 'cancelled'

def test_async_bulk_search_cancel_not_found(client):
    """Test cancelling non-existent job"""
    response = client.delete('/api/bulk-search-async/nonexistent-job-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
