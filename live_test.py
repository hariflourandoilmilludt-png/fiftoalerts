import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def run_checks():
    print("Checking Dashboard...")
    try:
        r = requests.get(BASE_URL)
        print(f"Dashboard Status: {r.status_code}")
        if r.status_code == 200:
            print("Dashboard Validated.")
        else:
            print(f"Dashboard Failed Body: {r.text}")
    except Exception as e:
        print(f"Dashboard Failed: {e}")

    print("\nAdding Instrument...")
    try:
        r = requests.post(f"{BASE_URL}/add_instrument", data={"symbol": "LIVE_TEST", "timeframe": "1m"})
        print(f"Add Instrument Status: {r.status_code}")
        if r.status_code not in [200, 302]:
             print(f"Add Instrument Error: {r.text}")
    except Exception as e:
        print(f"Add Instrument Failed: {e}")

    print("\nSetting Quantman URL...")
    # Update Instrument with a dummy Quantman URL (using httpbin for testing if possible, or just localhost)
    # For test, we just assume the endpoint works.
    try:
        # We need the ID of the instrument "LIVE_TEST". Since we don't know it easily without querying, 
        # we might skip this or assume ID 1 if it's fresh. 
        # Better: run a GET to dashboard to scrape it? No, too complex for this script.
        # Let's just print a reminder to test manually or check logs.
        print("To verify Quantman, manually set a URL in Dashboard and check logs.")
    except Exception as e:
        print(f"Quantman Setup Failed: {e}")

    print("\nSending Webhook (ENTRY)...")
    payload = {
        "symbol": "LIVE_TEST",
        "signal": "ENTRY_LONG",
        "price": "100",
        "timestamp": "2024-01-01T12:00:00Z"
    }
    try:
        r = requests.post(f"{BASE_URL}/webhook", json=payload)
        print(f"Webhook Entry Status: {r.status_code}")
        print(f"Webhook Entry Response: {r.text}")
    except Exception as e:
        print(f"Webhook Failed: {e}")

    print("\nSending Webhook (CLOSE)...")
    payload["signal"] = "EXIT_LONG"
    payload["timestamp"] = "2024-01-01T12:05:00Z"
    try:
        r = requests.post(f"{BASE_URL}/webhook", json=payload)
        print(f"Webhook Exit Response: {r.text}")
    except Exception as e:
        print(f"Webhook Exit Failed: {e}")

    print("\nSending Webhook (FLIP - Same Candle)...")
    payload["signal"] = "ENTRY_SHORT"
    # SAME TIMESTMAP AS EXIT
    payload["timestamp"] = "2024-01-01T12:05:00Z" 
    try:
        r = requests.post(f"{BASE_URL}/webhook", json=payload)
        print(f"Webhook Flip Response: {r.text}")
    except Exception as e:
        print(f"Webhook Flip Failed: {e}")

if __name__ == "__main__":
    time.sleep(2) # Wait for server
    run_checks()
