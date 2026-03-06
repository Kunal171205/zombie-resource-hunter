# 🧟 Zombie Resource Hunter - FinOps Dashboard

A portable, user-centric tool for any AWS user to discover idle EC2 instances and unattached EBS volumes. This tool is designed to be run **locally** or as a **private server** to scan your own AWS account without needing centralized deployment.

## Features
- **Idle EC2 Discovery**: Finds instances with low average CPU utilization.
- **Wasted Storage Detection**: Locates EBS volumes not attached to any instance.
- **Financial Dashboard**: Premium Web UI to visualize monthly waste.
- **Optional Alerts**: Send weekly reports via AWS SNS.

## Getting Started

### 1. Prerequisites
- Python 3.11+
- AWS CLI configured with your credentials (`aws configure`)
- IAM Permissions: `AmazonEC2ReadOnlyAccess`, `CloudWatchReadOnlyAccess`

### 2. Installation
```bash
# Clone or download this project
pip install -r requirements.txt
```

### 3. Run Locally (Web Dashboard)
You can run the dashboard on your own machine to scan your account:
```bash
python app/app.py
```
Then open `http://localhost:5000` in your browser.

### 4. Optional: Configuration
You can customize the detection thresholds using environment variables:
- `CPU_THRESHOLD`: Default `5.0` (%)
- `IDLE_DAYS`: Default `7` (days)
- `SNS_TOPIC_ARN`: Optional SNS topic for alerts.

## Deployment Options
- **AWS EC2**: Run as a standalone web application for your team.
- **AWS Lambda**: Deploy `lambda/hunter.py` for automated weekly reporting.

---
Built with ❤️ for Cloud Efficiency.
