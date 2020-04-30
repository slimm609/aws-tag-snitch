# AWS Lambda tagger

replicate aws tags down from ec2 instances, ELBs and VPCs

## ec2_tagger.py

replicate tags from ec2 isntances and elb to volumes and enis


## vpc_tagger.py

replicate tags from vpc to subnets, IGWs, and route tables


## tag_snitch.py

snitch on systems to a webhook if a ec2 instance does not have the proper tags.

WEBHOOK env as the webhook endpoint
ACCOUNT_NAME env as a friendly name for the aws account, for when using a single webhook for multiple accounts
