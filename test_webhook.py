"""
Test webhook sender for the contractor bot.
Simulates leads from Website, Facebook, Google Business, and Typeform
without needing real accounts on those platforms.
"""

import argparse
import json
import sys
import time

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip install requests")
    sys.exit(1)


def payload_generic(phone: str, name: str = "Test Lead"):
    return {"name": name, "phone": phone, "service": "Driveway sealing", "source": "website"}


def payload_facebook(phone: str, name: str = "Test FB Lead"):
    return {
        "entry": [{"changes": [{"value": {"field_data": [
            {"name": "full_name", "values": [name]},
            {"name": "phone_number", "values": [phone]},
            {"name": "service", "values": ["Concrete sealing quote"]}
        ]}}]}]
    }


def payload_google(phone: str, name: str = "Test GBP Lead"):
    return {"messageNotifications": [{"message": {
        "displayName": name, "phoneNumber": phone, "text": "Interested in a quote for driveway sealing"
    }}]}


def payload_typeform(phone: str, name: str = "Test Typeform Lead"):
    return {"form_response": {"answers": [
        {"ref": "name", "type": "text", "text": name},
        {"ref": "phone", "type": "phone_number", "phone_number": phone},
        {"ref": "service", "type": "text", "text": "Asphalt sealing"}
    ]}}


ENDPOINTS = {
    "website": ("/webhook/generic", payload_generic),
    "generic": ("/webhook/generic", payload_generic),
    "facebook": ("/webhook/facebook", payload_facebook),
    "google": ("/webhook/google", payload_google),
    "typeform": ("/webhook/typeform", payload_typeform),
    "auto": ("/webhook/lead", payload_generic),
}


def send_test(base_url, secret, source, phone, verbose=True):
    path, payload_fn = ENDPOINTS[source]
    payload = payload_fn(phone)
    url = f"{base_url.rstrip('/')}{path}"
    headers = {"Content-Type": "application/json", "x-webhook-secret": secret}

    if verbose:
        print(f"\n--- Testing source: {source} ---")
        print(f"POST {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {resp.status_code}")
        try:
            print(f"Response: {json.dumps(resp.json(), indent=2)}")
        except ValueError:
            print(f"Response (raw): {resp.text}")
        return resp.status_code == 200
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to {url}. Is the server running?")
        return False
    except requests.exceptions.Timeout:
        print(f"ERROR: Request to {url} timed out.")
        return False


def test_health(base_url):
    url = f"{base_url.rstrip('/')}/health"
    try:
        resp = requests.get(url, timeout=5)
        print(f"\n--- Health Check ---")
        print(f"GET {url}")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")


def test_unauthorized(base_url):
    url = f"{base_url.rstrip('/')}/webhook/generic"
    payload = payload_generic("+14055551234")
    print(f"\n--- Testing Unauthorized Request (no secret) ---")
    try:
        resp = requests.post(url, json=payload, timeout=10)
        print(f"Status: {resp.status_code} (expected 401)")
        if resp.status_code == 401:
            print("PASS: Webhook correctly rejected request without secret.")
        else:
            print("FAIL: Webhook accepted a request with no secret! Check _validate_secret().")
    except Exception as e:
        print(f"ERROR: {e}")

def test_wrong_secret(base_url):
    url = f"{base_url.rstrip('/')}/webhook/generic"
    payload = payload_generic("+14055551234")
    headers = {"Content-Type": "application/json", "x-webhook-secret": "wrong_secret"}
    print(f"\n--- Testing Unauthorized Request (wrong secret) ---")
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Status: {resp.status_code} (expected 401)")
        if resp.status_code == 401:
            print("PASS: Webhook correctly rejected request with wrong secret.")
        else:
            print("FAIL: Webhook accepted a request with wrong secret! Check _validate_secret().")
    except Exception as e:
        print(f"ERROR: {e}")

def test_rate_limit(base_url, secret):
    url = f"{base_url.rstrip('/')}/webhook/generic"
    payload = payload_generic("+14055551234")
    headers = {"Content-Type": "application/json", "x-webhook-secret": secret}
    print(f"\n--- Testing Rate Limiting ---")
    try:
        # Send 105 requests (should exceed default 100 limit)
        for i in range(105):
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 429:
                print(f"PASS: Rate limit triggered after {i+1} requests")
                return
        print("FAIL: Rate limit not triggered after 105 requests")
    except Exception as e:
        print(f"ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test webhook sender for contractor bot")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--secret", required=True)
    parser.add_argument("--source", default="all", choices=list(ENDPOINTS.keys()) + ["all"])
    parser.add_argument("--phone", default="+14055551234")
    parser.add_argument("--skip-security-check", action="store_true")
    parser.add_argument("--security-only", action="store_true", help="Run only security tests")
    parser.add_argument("--test-rate-limit", action="store_true", help="Include rate limiting test (slow)")

    args = parser.parse_args()

    test_health(args.url)

    if not args.skip_security_check:
        test_unauthorized(args.url)
        test_wrong_secret(args.url)
        # Only run rate limiting test if explicitly requested (too slow for quick testing)
        if args.test_rate_limit:
            test_rate_limit(args.url, args.secret)
    
    if args.security_only:
        return

    if args.source == "all":
        results = {}
        for src in ["generic", "facebook", "google", "typeform", "auto"]:
            results[src] = send_test(args.url, args.secret, src, args.phone)
            time.sleep(1)
        print("\n--- Summary ---")
        for src, ok in results.items():
            print(f"{src}: {'PASS' if ok else 'FAIL'}")
    else:
        send_test(args.url, args.secret, args.source, args.phone)


if __name__ == "__main__":
    main()
