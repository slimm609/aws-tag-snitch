import boto3
import sys
from random import randint

def vpc(region='us-west-2'):
    print('Processing VPCs')
    client = boto3.client('ec2',region_name=region)
    ec2 = boto3.resource('ec2',region_name=region)
    vpcs = client.describe_vpcs()
    for vpc in vpcs['Vpcs']:
        ID = vpc['VpcId']
        nacl_filter = [{'Name':'vpc-id', 'Values': [ID] }]
        network_acls = client.describe_network_acls(Filters=nacl_filter)
        nacls = network_acls['NetworkAcls']
        if nacls:
            for nacl in nacls:
                print('{}'.format(nacl['NetworkAclId']))
                # Block all Inbound traffic
                client.create_network_acl_entry(
                    DryRun=True,
                    CidrBlock='0.0.0.0/0',
                    Egress=False,
                    Protocol='-1',
                    RuleAction='deny',
                    RuleNumber=1,
                    NetworkAclId=nacl['NetworkAclId'] 
                )
                client.create_network_acl_entry(
                    DryRun=True,
                    Ipv6CidrBlock='::0/0',
                    Egress=False,
                    Protocol='-1',
                    RuleAction='deny',
                    RuleNumber=2,
                    NetworkAclId=nacl['NetworkAclId'] 
                )
                # Block all Outbound traffic
                client.create_network_acl_entry(
                    DryRun=True,
                    CidrBlock='0.0.0.0/0',
                    Egress=True,
                    Protocol='-1',
                    RuleAction='deny',
                    RuleNumber=1,
                    NetworkAclId=nacl['NetworkAclId'] 
                )
                client.create_network_acl_entry(
                    DryRun=True,
                    Ipv6CidrBlock='::0/0',
                    Egress=True,
                    Protocol='-1',
                    RuleAction='deny',
                    RuleNumber=2,
                    NetworkAclId=nacl['NetworkAclId'] 
                )



#make them verify a random number because it will block traffic for all VPCs in all regions for that account.
rannum=randint(1000, 9999)
print("Please enter the following number to continue {}: ".format(rannum))
data = input()
if int(data) != rannum:
    print('Error: verification number does not match')
    sys.exit(1)

client = boto3.client('ec2')
regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
for region in regions:
    print('Starting Region = {}'.format(region))
    vpc(region)