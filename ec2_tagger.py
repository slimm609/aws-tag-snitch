import boto3
from concurrent.futures import ThreadPoolExecutor as PoolExecutor

# Copy tags down to ELBs, ec2 volumes and eni
COPYABLE = ["Name", "Environment", "Project"]

def tag_instance(instance):
    tags = [t for t in instance.tags or [] if t['Key'] in COPYABLE]
    if not tags:
        return

    # Tag the EBS Volumes
    for vol in instance.volumes.all():
        print('Updating tags for {} from {}'.format(vol.id, instance))
        try:
            vol.create_tags(Tags=tags)
        except:
            pass

        # Tag the Elastic Network Interfaces
    for eni in instance.network_interfaces:
        print('Updating tags for {} from {}'.format(eni.id, instance))
        try:
            eni.create_tags(Tags=tags)
        except:
            pass


def ec2(region):
    print('Processing EC2 Instances')

    instances = boto3.resource('ec2', region_name=region).instances.all()
    print('ec2 - {}'.format(region))
    with PoolExecutor(max_workers=4) as executor:
        for _ in executor.map(tag_instance, instances):
            pass


def elb(region):
    print('Processing ELB Instances')

    def filter(i):
        return (i.get('RequesterId') == 'amazon-elb' and
                i['Description'].startswith('ELB') and
                '/' not in i['Description'])

    tags = _get_elb_tags('elb',region)
    for interface in _network_interfaces(filter,region=region):
        name = interface['Description'].split(' ')[1]
        if name not in tags:
            continue
        _tag_network_interface(interface['NetworkInterfaceId'], tags[name])

def elbv2(region):
    print('Processing ELBv2 Instances')

    def filter(i):
        return (i.get('RequesterId') == 'amazon-elb' and
                i['Description'].startswith('ELB') and
                '/' in i['Description'])

    tags = _get_elb_tags('elbv2',region=region)
    for interface in _network_interfaces(filter,region=region):
        name = interface['Description'].split('/')[1]
        if name not in tags:
            continue
        _tag_network_interface(interface['NetworkInterfaceId'], tags[name],region=region)


def _get_elb_tags(name='elb',region='us-west-2'):
    if name == 'elb':
        page_name = 'LoadBalancerDescriptions'
        key = 'LoadBalancerName'
        kwname = 'LoadBalancerNames'
    elif name == 'elbv2':
        page_name = 'LoadBalancers'
        key = 'LoadBalancerArn'
        kwname = 'ResourceArns'
    else:
        raise ValueError('Invalid name: {}'.format(name))

    tags = {}
    client = boto3.client(name, region_name=region)
    paginator = client.get_paginator('describe_load_balancers')
    for page in paginator.paginate():
        for lb in page[page_name]:
            response = client.describe_tags(**{kwname: [lb[key]]})
            lb_tags = [item for sublist in
                       [r.get('Tags', []) for r in response['TagDescriptions']]
                       for item in sublist]
            tags[lb['LoadBalancerName']] = [t for t in lb_tags if
                                            t['Key'] in COPYABLE]
            tags[lb['LoadBalancerName']].append(
                {'Key': 'Name', 'Value': lb['LoadBalancerName']})
    return tags


def _network_interfaces(filter=None,region='us-west-2'):
    client = boto3.client('ec2',region_name=region)
    print('ec2_network - {}'.format(region))
    paginator = client.get_paginator('describe_network_interfaces')
    for page in paginator.paginate():
        for interface in page['NetworkInterfaces']:
            if filter and not filter(interface):
                continue
            yield interface


def _tag_network_interface(eni_id, tags,region='us-west-2'):
    print('Updating tags for {}'.format(eni_id))
    ec2 = boto3.resource('ec2',region_name=region)
    eni = ec2.NetworkInterface(eni_id)
    eni.create_tags(Tags=tags)


def lambda_handler(event, context):
    client = boto3.client('ec2')
    regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    for region in regions:
        print('Starting Region = {}'.format(region))
        ec2(region)
        elb(region)
        elbv2(region)
