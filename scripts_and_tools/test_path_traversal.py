import httpx

# Test 1: GET /api/templates/../schema
r1 = httpx.get("http://127.0.0.1:8002/api/templates/..%2F../schema")
print("Test 1 status:", r1.status_code, r1.json())
assert r1.status_code == 404

# Test 2: POST /api/documents/generate
r2 = httpx.post("http://127.0.0.1:8002/api/documents/generate", json={
    "template_name": "../..",
    "data": {}
})
print("Test 2 status:", r2.status_code, r2.json())
assert r2.status_code == 400
assert "không hợp lệ" in r2.json()["detail"]

# Test 3: Normal template works
r3 = httpx.get("http://127.0.0.1:8002/api/templates/Gi%E1%BA%A3i%20th%E1%BB%83%20c%C3%B4ng%20ty%20TNHH%201%20TV/schema")
print("Test 3 status:", r3.status_code)
assert r3.status_code == 200

print("ALL PATH TRAVERSAL TESTS PASSED!")
