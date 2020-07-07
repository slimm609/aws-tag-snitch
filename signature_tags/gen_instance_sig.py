import boto3
import base64
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from botocore.vendored import requests
import os
import sys

SIGNATURE_ALGORITHM=os.environ.get('SIGNATURE_ALGORITHM','ECDSA_SHA_256')
SIGNATURE_TAG = "auth_sig"
kms_key_id=os.environ.get('KMS_KEY_ID', '9979620f-73d9-44ec-8f3e-ced9460e1dae')

def sign_instance(instance):
        kms = boto3.client('kms')
        ec2 = boto3.client('ec2')
        instance_id=instance.encode("utf-8")
        response=kms.sign(KeyId=kms_key_id,Message=base64.b64encode(instance_id),SigningAlgorithm=SIGNATURE_ALGORITHM)
        signature=base64.b64encode(response['Signature']).decode("utf-8")
        response = ec2.create_tags(
            Resources=[instance],
            Tags = [
                {
                    'Key': SIGNATURE_TAG,
                    'Value': signature
                }
            ]
        )
        print(response)


if len(sys.argv)>1:
    for inst in sys.argv[1:]:
        sign_instance(inst)