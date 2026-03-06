import boto3
import os
import json
from botocore.exceptions import ClientError

class S3Storage:
    def __init__(self):
        self.bucket_name = os.environ.get('S3_BUCKET_NAME')
        self.s3 = boto3.client('s3')

    def upload_report(self, data):
        """Uploads a scan report to S3 as a JSON file."""
        if not self.bucket_name:
            print("S3 Alert: No bucket configured. Skipping upload.")
            return False

        file_name = f"reports/scan_{data['timestamp'].replace(':', '-')}.json"
        
        try:
            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(data, indent=4),
                ContentType='application/json'
            )
            print(f"S3: Report uploaded to {file_name}")
            return True
        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            return False

# Singleton instance
s3_storage = S3Storage()
