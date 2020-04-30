import boto3
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from botocore.vendored import requests
import os

ACTIONABLE = ["Project"]
REPORTABLE = ["Name"]
webhook=os.environ.get('WEBHOOK')
account=os.environ.get('ACCOUNT_NAME')

def tag_instance(instance):
        tags = [t for t in instance.tags or [] if t['Key'] in ACTIONABLE]
        if not tags:
            rtags = [t for t in instance.tags or [] if t['Key'] in REPORTABLE]
            if rtags:
                x = rtags[0]
                message="Instance {} in {} account does not have the Project tag, but does have Name {}".format(instance.id,account, x['Value'])
            else:
                message="Instance {} in {} account does not have the Project tag and no Name tag".format(instance.id,account)
            body={ "channel": "#aws-missing-tags", "username": "Missing Tags", "attachments": [{ "color": "red", "fields": [{"title": "missing-tags","value": message }]}]}
            requests.post(webhook, json=body)

def ec2():
    print('Processing EC2 Instances')

    instances = boto3.resource('ec2').instances.all()
    with PoolExecutor(max_workers=4) as executor:
        for _ in executor.map(tag_instance, instances):
            pass

def lambda_handler(event, context):
    ec2()