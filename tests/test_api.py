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
    response = client.post(
        '/api/search',
        json={
            'extension_id': 'cjpalhdlnbpafiamejdnhcphjbkeiagm',
            'stores': ['chrome', 'safari']
        }
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'extension_id' in data
    assert 'results' in data
    assert isinstance(data['results'], list)


def test_search_extension_safari(client):
    """Test search endpoint for Safari store"""
    response = client.post(
        '/api/search',
        json={'extension_id': 'invalid', 'stores': ['safari']}
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'extension_id' in data
    assert 'results' in data
    assert isinstance(data['results'], list)

def test_search_invalid_request(client):
    """Test search with invalid request"""
    response = client.post('/api/search', json={})
    assert response.status_code == 400
    
    response = client.post('/api/search', data="invalid")
    assert response.status_code == 400

def test_bulk_search(client):
    """Test bulk search endpoint"""
    response = client.post(
        '/api/bulk-search',
        json={
            'extension_ids': ['cjpalhdlnbpafiamejdnhcphjbkeiagm'],
            'stores': ['chrome', 'safari']
        }
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'results' in data


def test_bulk_search_safari(client):
    """Test bulk search with Safari store"""
    response = client.post(
        '/api/bulk-search',
        json={'extension_ids': ['invalid'], 'stores': ['safari']}
    )
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

def test_api_key_required():
    """Test API key authentication when enabled"""
    app.config['TESTING'] = True
    app.config['API_KEY_REQUIRED'] = True
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
