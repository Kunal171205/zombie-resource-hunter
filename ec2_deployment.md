# 🚀 Detailed Step-by-Step EC2 Deployment Guide

Follow this granular guide to deploy the **Zombie Resource Hunter** dashboard to AWS correctly.

---

## Phase 1: AWS Infrastructure Setup

### 1.1 Create the IAM Role (Permissions)
The EC2 instance needs "Identity" to talk to AWS services without you manually giving it keys.
1.  Navigate to the [IAM Console](https://console.aws.amazon.com/iam).
2.  Click **Roles** > **Create role**.
3.  **Trusted entity type**: AWS service.
4.  **Service or use case**: EC2. Click **Next**.
5.  **Add permissions**: Search and check the box for:
    -   `AmazonEC2ReadOnlyAccess`
    -   `CloudWatchReadOnlyAccess`
    -   `AmazonSNSFullAccess` (Optional: Only if you want email alerts).
6.  Click **Next**.
7.  **Role name**: `ZombieHunterEC2Role`.
8.  Click **Create role**.

### 1.2 Launch the EC2 Instance
1.  Go to the [EC2 Dashboard](https://console.aws.amazon.com/ec2).
2.  Click **Launch Instance**.
3.  **Name**: `Zombie-Hunter-Dashboard`.
4.  **AMI**: Amazon Linux 2023 (Default).
5.  **Instance Type**: `t2.micro` (Free Tier).
6.  **Key pair**: Choose an existing one or create a new one (e.g., `my-key.pem`). **Download and save this safely!**
7.  **Network Settings** (Click Edit):
    -   **Security Group**: Create security group.
    -   **Rule 1 (SSH)**: Port 22 | Source: `My IP`.
    -   **Rule 2 (HTTP)**: Port 80 | Source: `0.0.0.0/0` (Anywhere).
8.  **Advanced Details**: Scroll to the bottom to **IAM instance profile** and select `ZombieHunterEC2Role`.
9.  Click **Launch Instance**.

---

## Phase 2: Connecting and Preparing the Server

### 2.1 Connect via SSH
-   **Windows (CMD/PowerShell)**:
    ```bash
    ssh -i "path/to/my-key.pem" ec2-user@<Instance-Public-IP>
    ```
-   **Mac/Linux**:
    ```bash
    chmod 400 my-key.pem
    ssh -i my-key.pem ec2-user@<Instance-Public-IP>
    ```

## 3. Troubleshooting: The "Brackets" Pitfall

The user encountered an error: `ssh: Could not resolve hostname <...>: No such host is known.`

**Resolution:**
- Explained that angle brackets `< >` are placeholders and must be removed from the final command.
- Provided the corrected command format: `ec2-user@13.62.57.253`.

## 4. Verification

Once connected and updated, the user can verify their environment with:
- `python3 --version`
- `git --version`

## 6. Troubleshooting: Missing `iptables` on AL2023

Amazon Linux 2023 (AL2023) does not include `iptables` by default as it prioritizes `nftables`.

**Resolution:**
- Instructed the user to install `iptables` using `sudo dnf install iptables -y`.
- Once installed, the port forwarding command will work as expected.

## Phase 3: Deploying the Application

### 3.1 Clone and Setup
```bash
# Clone your code (replace with your actual repo or upload files)
git clone <your-repo-url>
cd "cloud Project"

# Create a Virtual Environment (Best Practice)
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install flask boto3
```

### 3.2 Configure Networking (Port 80 to 5000)
Standard web traffic uses Port 80, but Flask runs on 5000. Run this to bridge them:
```bash
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 5000
```

---

## Phase 4: Production Setup (Systemd)

Instead of just running it manually, we'll create a "Service" so it restarts automatically if the server reboots.

1.  **Create the service file**:
    ```bash
    sudo nano /etc/systemd/system/zombie-hunter.service
    ```
2.  **Paste the following** (Adjust `/home/ec2-user/.../` paths to your actual directory):
    ```ini
    [Unit]
    Description=Zombie Resource Hunter Flask App
    After=network.target

    [Service]
    User=ec2-user
    WorkingDirectory=/home/ec2-user/cloud Project/app
    Environment="PATH=/home/ec2-user/cloud Project/venv/bin"
    Environment="AWS_DEFAULT_REGION=us-east-1"
    ExecStart=/home/ec2-user/cloud Project/venv/bin/python app.py

    [Install]
    WantedBy=multi-user.target
    ```
    *(Press `Ctrl+O`, `Enter`, `Ctrl+X` to save and exit)*

3.  **Start and Enable the service**:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl start zombie-hunter
    sudo systemctl enable zombie-hunter
    ```

---

## Phase 5: Verification
1.  Copy the **Public IPv4 address** of your instance from the EC2 Console.
2.  Paste it into your browser: `http://<your-ip>`.
3.  **Done!** Your dashboard is now live and persistent.
