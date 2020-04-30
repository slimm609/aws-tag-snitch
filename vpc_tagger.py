import boto3
from concurrent.futures import ThreadPoolExecutor as PoolExecutor

# Tags that are copyable to subnets, route tables, and IGWs
COPYABLE = ["Name", "Environment", "Project"]

def vpc(region):
    print('Processing VPCs')
    client = boto3.client('ec2',region_name=region)
    ec2 = boto3.resource('ec2',region_name=region)
    vpcs = client.describe_vpcs()
    for vpc in vpcs['Vpcs']:
        ID = vpc['VpcId']
        try:
            tags = [t for t in vpc['Tags'] or [] if t['Key'] in COPYABLE]
            if not tags:
                continue
        except:
            continue

        # copy down VPC tags to internet gateways
        igw_filter = [{'Name':'attachment.vpc-id', 'Values': [ID] }]
        internet_gateways = client.describe_internet_gateways(Filters=igw_filter)
        igws = internet_gateways['InternetGateways']
        if igws:
            for igw in igws:
                ec2_igw = ec2.InternetGateway(igw['InternetGatewayId'])
                ec2_igw.create_tags(Tags=tags)

        # copy down VPC tags to subnets and route tables
        subnet_filter = [{'Name':'vpc-id', 'Values': [ID] }]
        subnets = client.describe_subnets(Filters=subnet_filter)
        for subnet in subnets['Subnets']:
            ec2_subnet = ec2.Subnet(subnet['SubnetId'])
            ec2_subnet.create_tags(Tags=tags)
            subnet_ID = subnet['SubnetId']
            route_filter= [{'Name':'vpc-id', 'Values': [ID], 'Name': 'association.subnet-id', 'Values': [ subnet_ID ] }]
            route = client.describe_route_tables(Filters=route_filter)
            rts = route['RouteTables']
            if rts:
                for rt in rts:
                    ec2_routeTable = ec2.RouteTable(rt['RouteTableId'])
                    ec2_routeTable.create_tags(Tags=tags)


def lambda_handler(event, context):
    client = boto3.client('ec2')
    regions = [region['RegionName'] for region in client.describe_regions()['Regions']]
    for region in regions:
        print('Starting Region = {}'.format(region))
        vpc(region)