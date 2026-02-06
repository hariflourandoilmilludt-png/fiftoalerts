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
