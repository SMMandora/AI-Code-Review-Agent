import boto3

AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"


def upload_file(bucket: str, key: str, data: bytes) -> None:
    client = boto3.client("s3", aws_access_key_id=AWS_ACCESS_KEY,
                          aws_secret_access_key=AWS_SECRET_KEY)
    client.put_object(Bucket=bucket, Key=key, Body=data)
