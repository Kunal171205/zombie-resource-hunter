import os

# Configuration for Zombie Resource Hunter

# --- AWS SNS Configuration ---
# Use environment variables for the ARN to make the code portable
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")

# --- Thresholds ---
# CPU usage below this percentage (over 7 days) marks an EC2 instance as idle
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", 5.0))

# Number of days to look back for CPU metrics
IDLE_DAYS = int(os.getenv("IDLE_DAYS", 7))

# --- Cost Estimates (Approximate) ---
# Monthly cost per GB for EBS (gp3/gp2 roughly $0.08 - $0.10)
EBS_COST_PER_GB_MONTH = float(os.getenv("EBS_COST_PER_GB_MONTH", 0.10))

# Monthly cost for t2.micro (as an example)
EC2_IDLE_FIXED_COST = float(os.getenv("EC2_IDLE_FIXED_COST", 8.00))

