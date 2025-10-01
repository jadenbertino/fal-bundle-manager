import requests
from api.tests.helpers import BASE_URL


def test_status_endpoint():
    """Test that the /status endpoint returns 200 OK"""
    response = requests.get(f"{BASE_URL}/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
