import boto3

client = boto3.client(
    "ec2",
    region_name="us-east-1",
    endpoint_url="http://localhost:4566",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

client.stop_instances(
    InstanceIds=["i-6175b062b84a0dc00"]
)

print("Instance stopped")
