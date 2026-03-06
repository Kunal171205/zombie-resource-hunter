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
sns = boto3.client('sns', region_name=REGION)

def send_sns_email(data):
    """Sends a scan summary email via SNS."""
    if not config.SNS_TOPIC_ARN:
        print("SNS Alert: No Topic ARN configured. Skipping email.")
        return

    subject = "🚀 Zombie Resource Hunter: Scan Report"
    body = f"""
    Zombie Resource Hunter Scan Results
    -----------------------------------
    Timestamp: {data['timestamp']}
    Region: {REGION}

    💰 Monthly Waste: ${data['total_waste']:.2f}
    🖥️ Idle Instances: {len(data['idle_ec2'])} (${data['compute_waste']:.2f})
    📦 Zombie Volumes: {len(data['zombie_vols'])} (${data['storage_waste']:.2f})
    📊 Total Storage: {data['total_gb']} GB

    Check the dashboard at: http://13.62.57.253
    """

    try:
        sns.publish(
            TopicArn=config.SNS_TOPIC_ARN,
            Message=body,
            Subject=subject
        )
        print("SNS Alert: Email sent successfully.")
    except Exception as e:
        print(f"SNS Alert Error: {e}")

def get_idle_instances():
    """Finds EC2 instances with average CPU < CPU_THRESHOLD over the last week."""
    idle_instances = []
    total_found = 0
    try:
        print(f"Scanning EC2 in region: {REGION}")
        instances = ec2.describe_instances()
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                total_found += 1
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
    
    return idle_instances, total_found

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
def run_scan():
    try:
        idle_ec2, total_instances_checked = get_idle_instances()
        zombie_vols, total_gb = get_unattached_volumes()
        
        storage_waste = total_gb * config.EBS_COST_PER_GB_MONTH
        compute_waste = len(idle_ec2) * config.EC2_IDLE_FIXED_COST
        total_waste = storage_waste + compute_waste
        
        data = {
            "idle_ec2": idle_ec2,
            "zombie_vols": zombie_vols,
            "total_gb": total_gb,
            "total_instances_checked": total_instances_checked,
            "storage_waste": storage_waste,
            "compute_waste": compute_waste,
            "total_waste": total_waste,
            "timestamp": datetime.now().isoformat()
        }
        
        save_scan(data)
        send_sns_email(data)
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
