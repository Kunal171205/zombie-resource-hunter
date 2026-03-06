from database import init_db, save_scan, get_history
import os
import json

def test_db():
    print("Testing database persistence...")
    init_db()
    
    test_data = {
        "idle_ec2": [{"id": "i-123", "type": "t2.micro", "avg_cpu": 2.5}],
        "zombie_vols": [{"id": "vol-123", "size": 10}],
        "total_gb": 10,
        "storage_waste": 1.0,
        "compute_waste": 8.0,
        "total_waste": 9.0
    }
    
    save_scan(test_data)
    history = get_history()
    
    if len(history) > 0:
        print(f"Success: Found {len(history)} scan(s) in history.")
        latest = history[-1]
        assert latest['total_waste'] == 9.0
        print("Data integrity check passed.")
    else:
        print("Failure: No scan found in history.")

if __name__ == "__main__":
    test_db()
