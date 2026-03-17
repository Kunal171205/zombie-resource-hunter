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
    print(f"DEBUG: Checking SNS configuration... ARN found: {config.SNS_TOPIC_ARN[:15]}...")
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
    🖥️ Idle Instances: {data['idle_ec2_count']} (${data['compute_waste']:.2f})
    📦 Zombie Volumes: {data['zombie_vols_count']} (${data['storage_waste']:.2f})
    📊 Total Storage: {data['total_gb']} GB

    Check the dashboard at: http://13.62.224.178
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

from mongo_db import mongo_handler
from s3_storage import s3_storage

@app.route('/api/scan', methods=['POST'])
def run_scan():
    """Triggers a resource scan and saves results to Cloud + Local DB."""
    try:
        # Get EC2 and EBS results
        idle_instances, total_checked = get_idle_instances()
        zombie_vols, total_gb = get_unattached_volumes()
        
        # Calculate waste
        compute_waste = len(idle_instances) * config.EC2_IDLE_FIXED_COST
        storage_waste = total_gb * config.EBS_COST_PER_GB_MONTH
        total_waste = compute_waste + storage_waste
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_waste': total_waste,
            'compute_waste': compute_waste,
            'storage_waste': storage_waste,
            'idle_ec2_count': len(idle_instances),
            'zombie_vols_count': len(zombie_vols),
            'total_gb': total_gb,
            'total_instances_checked': total_checked
        }

        # 1. Save to MongoDB Atlas (Cloud DB)
        saved_to_cloud = mongo_handler.save_scan(data)
        
        # 2. Upload detailed report to S3
        s3_storage.upload_report(data)
        
        # 3. Local Backup (SQLite)
        save_scan(data)

        # 4. Send Alerts
        send_sns_email(data)

        msg = f"Scan complete! Region: {REGION}. "
        if saved_to_cloud:
            msg += "Results synced to MongoDB Atlas."
        
        return jsonify({"status": "success", "message": msg, "data": data})
    except Exception as e:
        print(f"Scan Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/history')
def get_history_api():
    """Retrieves history, prioritizing MongoDB Atlas."""
    history = mongo_handler.get_history()
    
    # Fallback to local SQLite if cloud is empty
    if not history:
        from database import get_history as get_scans_history
        history = get_scans_history()
        
    return jsonify(history)


@app.route('/api/health')
def health_check():
    """Health check endpoint to verify server is running."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
