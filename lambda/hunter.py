import boto3
from datetime import datetime, timedelta
import config

ec2 = boto3.client('ec2')
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

def get_idle_instances():
    """Finds EC2 instances with average CPU < CPU_THRESHOLD over the last week."""
    idle_instances = []

    instances = ec2.describe_instances()
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']

            # Only check running instances
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
                Period=86400, # Daily average
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

    return idle_instances

def get_unattached_volumes():
    """Finds EBS volumes in 'available' state (not attached to any instance)."""
    volumes = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )["Volumes"]

    zombies = []
    total_gb = 0

    for v in volumes:
        zombies.append({
            "id": v["VolumeId"],
            "size": v["Size"]
        })
        total_gb += v["Size"]

    return zombies, total_gb

def get_zombie_report_data():
    """Gathers all zombie resource data and returns it as a dictionary."""
    idle_ec2 = get_idle_instances()
    zombie_vols, total_gb = get_unattached_volumes()
    
    storage_waste = total_gb * config.EBS_COST_PER_GB_MONTH
    compute_waste = len(idle_ec2) * config.EC2_IDLE_FIXED_COST
    total_waste = storage_waste + compute_waste
    
    return {
        "idle_ec2": idle_ec2,
        "zombie_vols": zombie_vols,
        "total_gb": total_gb,
        "storage_waste": storage_waste,
        "compute_waste": compute_waste,
        "total_waste": total_waste
    }

def format_report_text(data):
    """Formats the gathered data into a human-readable report string."""
    idle_ec2 = data["idle_ec2"]
    zombie_vols = data["zombie_vols"]
    total_gb = data["total_gb"]
    total_waste = data["total_waste"]
    
    report = "🧟 Zombie Resources Hunter - System Status Report\n"
    report += "==============================================\n\n"

    if not idle_ec2 and not zombie_vols:
        report += "✅ No zombie resources found this week. Your infrastructure is highly efficient!\n\n"
    else:
        if zombie_vols:
            report += "📍 UNATTACHED EBS VOLUMES (Wasted Storage):\n"
            for v in zombie_vols:
                report += f"- {v['id']} | Size: {v['size']} GB\n"
            report += "\n"

        if idle_ec2:
            report += "📍 IDLE EC2 INSTANCES (Low CPU Utilization):\n"
            for i in idle_ec2:
                report += f"- {i['id']} | Type: {i['type']} | Avg CPU: {i['avg_cpu']:.2f}%\n"
            report += "\n"

    if total_waste > 0:
        report += "💸 FINANCIAL IMPACT:\n"
        report += f"- Estimated Storage Waste: ${data['storage_waste']:.2f}/month\n"
        report += f"- Estimated Compute Waste: ${data['compute_waste']:.2f}/month\n"
        report += f"- TOTAL ESTIMATED SAVINGS: ${total_waste:.2f}/month\n\n"
        report += "Action Required: Please review these resources in the AWS Console and delete or downsize where appropriate."
    else:
        report += "💸 FINANCIAL IMPACT: $0.00 (Perfect!)\n\n"
        report += "No action required at this time."
    
    return report

def lambda_handler(event, context):
    """Main entry point for AWS Lambda."""
    data = get_zombie_report_data()
    report = format_report_text(data)

    # Publish to SNS
    if config.SNS_TOPIC_ARN and "arn:aws:sns" in config.SNS_TOPIC_ARN:
        print(f"Publishing report to SNS: {config.SNS_TOPIC_ARN}")
        sns.publish(
            TopicArn=config.SNS_TOPIC_ARN,
            Subject="Zombie Resource Report 🚨 - Weekly Status",
            Message=report,
        )
        return {"status": "alert_sent", "waste": f"${data['total_waste']:.2f}"}
    else:
        print("No SNS Topic ARN configured (or invalid). Report generated successfully.")
        return {"status": "success", "report": report, "waste": f"${data['total_waste']:.2f}"}


