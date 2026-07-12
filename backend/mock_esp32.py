import time
import requests
import json
import random

BASE_URL = "https://m9vtp9i2sl5xk7n28lktek4e.141.148.199.81.sslip.io/api"
DEVICE_ID = "ESP32_MAIN_GATE"
MOCK_RFIDS = ["RFID_001_ABC", "RFID_002_DEF", "RFID_005_MNO", "RFID_UNKNOWN_99"]

def run_simulation():
    print("=== STARTING ESP32 HARDWARE NETWORK FLOW SIMULATION ===")
    
    # 1. Device Registration
    print("\n1. ESP32 sends registration...")
    reg_payload = {
        "device_id": DEVICE_ID,
        "name": "Entrance Gate A Scanner",
        "mac_address": "24:0A:C4:F3:12:44",
        "ip_address": "192.168.1.150",
        "firmware_version": "v2.1.4",
        "location": "Main Gate",
        "classroom": "Foyer"
    }
    try:
        res = requests.post(f"{BASE_URL}/device/register", json=reg_payload)
        print(f"Response: {res.status_code} - {res.json()}")
    except Exception as e:
        print(f"Error connecting to backend: {e}. Ensure FastAPI backend is running!")
        return

    # 2. Heartbeat update
    print("\n2. ESP32 transmits heartbeat ping...")
    hb_payload = {
        "device_id": DEVICE_ID,
        "battery_status": 98,
        "wifi_signal": -50,
        "sim_network": "T-Mobile LTE",
        "current_status_message": "RFID Waiting"
    }
    res = requests.post(f"{BASE_URL}/device/heartbeat", json=hb_payload)
    print(f"Response: {res.status_code} - {res.json()}")

    # 3. Simulate RFID Scan (Select a random card)
    uid = random.choice(MOCK_RFIDS)
    print(f"\n3. Student scans RFID Card: {uid}...")
    scan_payload = {
        "uid": uid,
        "device_id": DEVICE_ID
    }
    res = requests.post(f"{BASE_URL}/rfid/scan", json=scan_payload)
    print(f"Scan response: {res.status_code}")
    scan_data = res.json()
    print(json.dumps(scan_data, indent=2))

    if res.status_code != 200:
        print("\nScan rejected or student blocked. Simulation ended.")
        return

    # 4. Student selects parent (Father)
    student_id = scan_data.get("student_id")
    student_name = scan_data.get("student_name")
    parent_type = "father"
    
    print(f"\n4. Student presses '{parent_type.upper()}' button on ESP32.")
    print(f"Querying parent number for Student ID: {student_id}...")
    res = requests.get(f"{BASE_URL}/parent-number/{student_id}/{parent_type}")
    print(f"Response: {res.status_code}")
    num_data = res.json()
    print(json.dumps(num_data, indent=2))
    
    phone_number = num_data.get("phone_number")
    
    # 5. Call Start
    print(f"\n5. ESP32 A7672S dials {phone_number} and sends Call Started...")
    start_payload = {
        "rfid_uid": uid,
        "device_id": DEVICE_ID,
        "parent_type": parent_type
    }
    res = requests.post(f"{BASE_URL}/call/start", json=start_payload)
    print(f"Response: {res.status_code}")
    call_data = res.json()
    print(json.dumps(call_data, indent=2))
    
    call_id = call_data.get("call_id")

    # 6. Call Connected
    time.sleep(2)
    print(f"\n6. Parent answered! ESP32 sends Call Connected (Call ID: {call_id})...")
    res = requests.post(f"{BASE_URL}/call/connected", json={"call_id": call_id})
    print(f"Response: {res.status_code} - {res.json()}")

    # 7. Call Active (simulate talking)
    print("\n7. Talking for 4 seconds...")
    time.sleep(4)

    # 8. Call End
    duration = 4
    print(f"\n8. Student hangs up. ESP32 sends Call End (Duration: {duration}s)...")
    end_payload = {
        "call_id": call_id,
        "duration": duration,
        "status": "completed",
        "reason": "hung_up"
      }
    res = requests.post(f"{BASE_URL}/call/end", json=end_payload)
    print(f"Response: {res.status_code} - {res.json()}")
    
    print("\n=== SIMULATION COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_simulation()
