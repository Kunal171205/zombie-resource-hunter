# Manual AWS S3 Setup Guide 🪣

Follow these steps to manually create an S3 bucket and link it to your Zombie Resource Hunter app.

## Step 1: Create the S3 Bucket
1. Log in to the **AWS Management Console**.
2. Search for **S3** and click **Create bucket**.
3. **Bucket name**: Choose a unique name (e.g., `zombie-reports-yourname-2026`).
4. **Region**: Select `eu-north-1` (Stockholm) to match your EC2.
5. Keep all other settings as default and click **Create bucket**.

## Step 2: Update IAM Permissions (Crucial!)
Your EC2 instance needs permission to upload files to this new bucket.
1. Go to the **IAM Console** -> **Roles**.
2. Find the role attached to your EC2 instance (usually `ZombieHunterRole` or similar).
3. Click **Add permissions** -> **Create inline policy**.
4. Switch to the **JSON** tab and paste this:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```
*(Replace `your-bucket-name` with the name you chose in Step 1).*
5. Name it `ZombieHunterS3Policy` and save.

## Step 3: Update EC2 Service File
1. SSH into your EC2.
2. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/zombie-hunter.service
   ```
3. Add the bucket name:
   ```ini
   Environment="S3_BUCKET_NAME=your-bucket-name"
   ```
4. Save and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart zombie-hunter
   ```
