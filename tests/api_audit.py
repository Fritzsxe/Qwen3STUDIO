import requests
import json

def audit():
    base = "http://localhost:7860"
    endpoints = ["/api/status", "/api/models", "/api/history", "/api/diagnostics"]

    print("=== AUDITORIA DE API ===")
    for ep in endpoints:
        try:
            r = requests.get(base + ep, timeout=5)
            print(f"GET {ep} -> Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"  Response: {str(data)[:200]}...")
            else:
                print(f"  Error: {r.text}")
        except Exception as e:
            print(f"GET {ep} -> FALHA: {e}")

if __name__ == "__main__":
    audit()
