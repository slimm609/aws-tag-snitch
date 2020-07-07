import boto3
import base64
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from botocore.vendored import requests
import os
import time


SIGNATURE_ALGORITHM=os.environ.get('SIGNATURE_ALGORITHM','ECDSA_SHA_256')
SIGNATURE_TAG = ["auth_sig"]
webhook=os.environ.get('WEBHOOK')
account=os.environ.get('ACCOUNT_NAME')
kms_key_id=os.environ.get('KMS_KEY_ID', '9979620f-73d9-44ec-8f3e-ced9460e1dae')
alert_time="86400" # 24 hours

def delete_item(instance_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ec2_signatures')
    try:
        response = table.delete_item(
            Key={
                'instance_id': instance_id,
            }
        )
    except ClientError as e:
        raise
    else:
        return response


def put_item(instance_id):
    epoch_time = int(time.time())
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ec2_signatures')
    try:
        response = table.put_item(
            Item={ 'instance_id': instance_id,
                   'added_time': epoch_time
            },
            ConditionExpression='attribute_not_exists(instance_id)'
        )
    except:
      pass


def tag_instance(instance):
        kms = boto3.client('kms')
        tags = [t for t in instance.tags or [] if t['Key'] in SIGNATURE_TAG]
        instance_id=instance.id.encode("utf-8")
        if tags:
            x = tags[0]
            signature = base64.b64decode(x['Value'].encode("utf-8"))
            try:
                kms.verify(KeyId=kms_key_id,Message=base64.b64encode(instance_id),Signature=signature,SigningAlgorithm=SIGNATURE_ALGORITHM)
            except:
                put_item(instance.id)
        else:
            put_item(instance.id)


def ec2():
    print('Processing EC2 Instances')

    instances = boto3.resource('ec2').instances.all()
    with PoolExecutor(max_workers=4) as executor:
        for _ in executor.map(tag_instance, instances):
            pass


def prune_db():
    epoch_time = int(time.time())
    ec2_resource = boto3.resource('ec2')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ec2_signatures')
    x=table.scan()
    for i in x['Items']:
        instance = ec2_resource.Instance(i['instance_id'])
        try:
            # try to get the isntance state, if it fails then delete the instance from the database
            instance.state
            time_diff=epoch_time - i['added_time']
            if int(time_diff) > int(alert_time):
                message="Instance {} does not have {} tag".format(i['instance_id'], SIGNATURE_TAG[0])
                body={ "channel": "#aws-missing-tags", "username": "Missing Tags", "attachments": [{ "color": "red", "fields": [{"title": "missing-tags","value": message }]}]}
                requests.post(webhook, json=body)
            else:
                pass
        except:
            # delete the instance from the table if that instance ID no longer exists
            delete_item(i['instance_id'])


def lambda_handler(event, context):
    ec2()
    prune_db()