from flask import Flask, render_template, jsonify, request
import boto3
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path to import lambda/config.py if needed, 
# but better to copy it or refer to it.
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda'))
import config
from database import init_db, save_scan, get_history

app = Flask(__name__)

# AWS Clients
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
ec2 = boto3.client('ec2', region_name=REGION)
cloudwatch = boto3.client('cloudwatch', region_name=REGION)

def get_idle_instances():
    """Finds EC2 instances with average CPU < CPU_THRESHOLD over the last week."""
    idle_instances = []
    try:
        print(f"Scanning EC2 in region: {REGION}")
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                state = instance['State']['Name']

                if state != "running":
                    continue

                end = datetime.utcnow()
                start = end - timedelta(days=config.IDLE_DAYS)

                metrics = cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start,
                    EndTime=end,
                    Period=86400,
                    Statistics=["Average"],
                )

                datapoints = metrics["Datapoints"]
                if not datapoints:
                    continue

                avg_cpu = sum(d["Average"] for d in datapoints) / len(datapoints)

                if avg_cpu < config.CPU_THRESHOLD:
                    idle_instances.append({
                        "id": instance_id,
                        "type": instance['InstanceType'],
                        "avg_cpu": avg_cpu
                    })
    except Exception as e:
        print(f"Error fetching EC2 metrics: {e}")
    
    return idle_instances

def get_unattached_volumes():
    """Finds EBS volumes in 'available' state."""
    zombies = []
    total_gb = 0
    try:
        print(f"Scanning EBS in region: {REGION}")
        volumes = ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )["Volumes"]

        for v in volumes:
            zombies.append({
                "id": v["VolumeId"],
                "size": v["Size"]
            })
            total_gb += v["Size"]
    except Exception as e:
        print(f"Error fetching EBS volumes: {e}")

    return zombies, total_gb

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
    try:
        idle_ec2 = get_idle_instances()
        zombie_vols, total_gb = get_unattached_volumes()
        
        storage_waste = total_gb * config.EBS_COST_PER_GB_MONTH
        compute_waste = len(idle_ec2) * config.EC2_IDLE_FIXED_COST
        total_waste = storage_waste + compute_waste
        
        data = {
            "idle_ec2": idle_ec2,
            "zombie_vols": zombie_vols,
            "total_gb": total_gb,
            "storage_waste": storage_waste,
            "compute_waste": compute_waste,
            "total_waste": total_waste,
            "timestamp": datetime.now().isoformat()
        }
        
        save_scan(data)
        return jsonify(data)
    except Exception as e:
        print(f"CRITICAL: Scan failed: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history')
def get_scan_history():
    history = get_history()
    return jsonify(history)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
