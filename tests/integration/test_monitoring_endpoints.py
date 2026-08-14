# test application health
def test_health_endpoint(client):
    res = client.get("/health")
    
    assert res.status_code == 200
    assert res.is_json
    assert res.get_json() == {
        "status": "ok"
    }
    
# test application metrics
def test_metrics_endpoint(client):
    res = client.get("/metrics")
    
    assert res.status_code == 200
    assert res.is_json
    
    body = res.get_json()
    
    assert "total_requests" in body
    assert "requests_per_second" in body
    assert "uptime" in body
    
    assert body["total_requests"] >= 0
    assert body["requests_per_second"] >= 0
    assert body["uptime"] >= 0