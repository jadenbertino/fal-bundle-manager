import requests


def test_status_endpoint():
    """Test that the /status endpoint returns 200 OK"""
    response = requests.get("http://localhost:8000/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
