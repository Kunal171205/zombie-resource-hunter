# 🛠️ Deployment Guide: Zombie Resource Hunter

Follow these steps to deploy your FinOps bot to AWS.

## Step 1: Set Up Alerts (SNS)
1. Go to the **SNS** service in the AWS Console.
2. Click **Topics** -> **Create topic**.
3. Choose **Standard**, name it `ZombieAlerts`, and click **Create topic**.
4. Inside the topic, click **Create subscription**.
5. Choose **Email** as the protocol and enter your email address.
6. Check your inbox and click **Confirm Subscription**.
7. **Copy the ARN** of your new SNS topic.

## Step 2: Configure the Code
1. Open `lambda/config.py` in your local environment.
2. Paste your SNS ARN into the `SNS_TOPIC_ARN` variable.
3. Save the file.

## Step 3: Create the Lambda Function
1. Go to the **Lambda** service.
2. Click **Create function** -> **Author from scratch**.
3. Name: `ZombieResourceHunter`. Runtime: **Python 3.11**.
4. Click **Create function**.
5. In the **Code** tab, you will see a file named `lambda_function.py`. 
   - **Delete all code** inside it.
   - **Paste** the contents of your local `hunter.py` into it.
6. Click **File -> New File**, name it `config.py`, and paste the contents of your local `config.py` there.
7. Click the orange **Deploy** button. (This is critical!)

## Step 4: Add Permissions (IAM)
1. Go to the **Configuration** tab for your Lambda function.
2. Click **Permissions** on the left sidebar.
3. Click the **Role name** link to go to the IAM console.
4. Click **Add permissions** -> **Attach policies**.
5. Search for and attach:
   - `AmazonEC2ReadOnlyAccess`
   - `CloudWatchReadOnlyAccess`
   - `AmazonSNSFullAccess`

## Step 5: Schedule the Scan (EventBridge)
1. In the Lambda console, click **Add trigger**.
2. Select **EventBridge (CloudWatch Events)**.
3. Choose **Create a new rule**.
4. Rule name: `WeeklyZombieScan`.
5. Rule type: **Schedule expression**.
6. Schedule expression: `cron(0 0 ? * SUN *)` (Runs every Sunday at midnight).
7. Click **Add**.

## Step 6: Test It!
1. Go to the **Test** tab in your Lambda function.
2. Create a test event (default settings are fine).
3. Click **Test**.
4. Check your email for the Zombie Resource Report!
