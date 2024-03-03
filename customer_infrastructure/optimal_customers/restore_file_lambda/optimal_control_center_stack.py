import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_efs as efs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_rds as rds,
    aws_servicediscovery as sd,
    aws_ssm as ssm,
    aws_s3 as s3,
    App, Duration,
)
import os

DEFAULT_ACCOUNT = (os.environ['CDK_DEFAULT_ACCOUNT'])
DEFAULT_REGION = (os.environ['CDK_DEFAULT_REGION'])
DEPLOYMENT_ENVIRONMENT = os.environ['DEPLOYMENT_ENVIRONMENT']

print(f'Optimal Control Center Stack Deployment to: {DEPLOYMENT_ENVIRONMENT}')
print(f'DEPLOYMENT_ENVIRONMENT: {DEPLOYMENT_ENVIRONMENT}')
print(f'Region: {DEFAULT_REGION}')

customer_name = 'controlcenter'
cost_center_customer_name = 'optimal'
tags = {
    'Environment': f'{DEPLOYMENT_ENVIRONMENT}',
    'cost_center': f'{cost_center_customer_name}',
}

linux_maint_host_ami = ec2.MachineImage.generic_linux(ami_map={
    #"us-east-1": "ami-01234567",  # Replace with your desired AMI ID
    "us-east-2": "ami-059261ff7474f56fe",  # Ubuntu 22.04 LTS
})

windows_maintenance_host_user_data ="""\
<powershell>
# Set the hostname
$NewHostname = "maint-host-win"
Rename-Computer -NewName $NewHostname -Force -Restart

# Set the password for the Administrator user
$NewPassword = ConvertTo-SecureString -String "P@ssw@rd" -AsPlainText -Force
$UserAccount = Get-LocalUser -Name "administrator"
$UserAccount | Set-LocalUser -Password $NewPassword
</powershell>
"""
    
if os.environ['DEPLOYMENT_ENVIRONMENT'] == 'sandbox':
    aurora_backup_retention= Duration.days(5)
    auto_pause = Duration.hours(2)
    min_serverless_capacity = rds.AuroraCapacityUnit.ACU_2
    max_serverless_capacity = rds.AuroraCapacityUnit.ACU_4
    control_center_memory_limit_mib = 4096
    control_center_cpu = 2048
    #new optimalpipeline.io cert arn:
    optimal_control_center_certificate_arn = 'arn:aws:acm:us-east-2:545244250143:certificate/4bba2000-2815-4c01-ae6f-2e71c68880e9'
    #new optimalpipeline.io cert arn:
    customer_control_center_certificate_arn = 'arn:aws:acm:us-east-2:545244250143:certificate/4bba2000-2815-4c01-ae6f-2e71c68880e9'
    dep_env_prefix = 'dev-'
    # ignition_environment_variables
    ACCEPT_IGNITION_EULA = "Y"
    DISABLE_QUICKSTART = "true"
    CONTROL_CENTER_RESTORE_FILE_NAME = "controlcenter.gwbk"
    GATEWAY_SYSTEM_NAME = "controlcenter"
    #'GATEWAY_ADMIN_USERNAME': control_center_gateway_admin_username,
    #'GATEWAY_ADMIN_PASSWORD': control_center_gateway_admin_password,
    GATEWAY_MODULES_ENABLED = "alarm-notification,perspective,tag-historian,reporting,sms-notification,sfc,vision,sql-bridge,opc-ua,symbol-factory"
    IGNITION_EDITION = "standard"
    IGNITION_LICENSE_KEY = ""
    IGNITION_ACTIVATION_TOKEN = ""
    TZ = "America/Chicago"
    maintenance_host_ssh_key = 'maintenance_host_ssh_key'
    windows_host_ami = ec2.GenericWindowsImage({
        "us-east-2": "ami-0007e91afefcd1257"
        }
    )
    maintenance_host_ssh_key = 'maintenance_host_ssh_key'
    windows_maintenance_host_instance_size = ec2.InstanceSize.SMALL
    
elif os.environ['DEPLOYMENT_ENVIRONMENT'] == 'demo':
    aurora_backup_retention= Duration.days(5)
    auto_pause = Duration.hours(2)
    min_serverless_capacity = rds.AuroraCapacityUnit.ACU_2
    max_serverless_capacity = rds.AuroraCapacityUnit.ACU_4
    control_center_memory_limit_mib = 4096
    control_center_cpu = 2048
    #new optimalpipeline.io cert arn:
    optimal_control_center_certificate_arn = 'arn:aws:acm:us-east-2:905418000319:certificate/de212ec1-219e-4974-9ac1-1527d47460c4'
    #new optimalpipeline.io cert arn:
    customer_control_center_certificate_arn = 'arn:aws:acm:us-east-2:905418000319:certificate/de212ec1-219e-4974-9ac1-1527d47460c4'
    dep_env_prefix = 'demo-'
    # ignition_environment_variables
    ACCEPT_IGNITION_EULA = "Y"
    DISABLE_QUICKSTART = "true"
    CONTROL_CENTER_RESTORE_FILE_NAME = "controlcenter.gwbk"
    GATEWAY_SYSTEM_NAME = "controlcenter"
    #'GATEWAY_ADMIN_USERNAME': control_center_gateway_admin_username,
    #'GATEWAY_ADMIN_PASSWORD': control_center_gateway_admin_password,
    GATEWAY_MODULES_ENABLED = "alarm-notification,perspective,tag-historian,reporting,sms-notification,sfc,vision,sql-bridge,opc-ua,symbol-factory,modbus-driver-v2"
    IGNITION_EDITION = "standard"
    IGNITION_LICENSE_KEY = ""
    IGNITION_ACTIVATION_TOKEN = ""
    #IGNITION_LICENSE_KEY = "77862ARD"
    #IGNITION_ACTIVATION_TOKEN = "eyJrdHkiOiJSU0EiLCJraWQiOiIyNmIyZGZlMS03NThiLTRiZDItYTFiNS0wNDFjYzBlN2FlOTIiLCJ1c2UiOiJzaWciLCJhbGciOiJSUzI1NiIsIm4iOiJrMnVTZmk4MTFmVHFoZlRFX2dnZlNtcXdIYVFqRWs5TFlpMy10UXZ4YnV1b09qUHZsUG1VQkNfTzQ5UzRIT0FTd2dGa0ZZQ1laMUllbGVvQkU0eXRVejdBSHFXYmJQMFRqQXRQUV85Yk1qclUwbXI5alV5U3pZRGVudkdoZGpNZGxZSHhRblB0MTB2RTd5MEhYbGx5YlhJYW4yM254QlNtSGd4Zk05Ny1QS0puU1B2UGZrc0thc1dIeXhtRnI3THgzME81cE94dmkwUWJtTjNncFZzN25yNi1lT21VanVKSGh1d3ZlZ0txeVdna1Q1LTNqRXlsYV9hZ3V0STRfMkpqcndfRE12bFhud2hWeDFRck9NR0x4OTBqUWduUlZFQ0dqeXBtZE0yV0gwZmwtOGtlNmU5b21CbG5panRYZllaYjVSVkw1VmQzczFlbVRCUERMLW5VUHciLCJlIjoiQVFBQiIsImQiOiJSRlNqTlR2YXYwNWplaTNITlZ3OGJMamc0d3hXZVVFcDF0c3M2V3djdjJZWnRzaWw3eTV6empELXU1bTRzU0duY0NkRzViU1NiNm1mcGFzdVRvcHhPRm1vb1V2dnEtZnVMSVo5ZWk0ZGJqM1lzYU9IM1B1Mk8telV3MldLaW9nTTJXUy1tQ2UyQVlvTVFUUms2dldZMVdRRE5ReXpWYTZnaE9NRktiemRxT3FBenJxOXZsUTFvTFFsMlVObnZkdURrZy1PbVU4UklYeFdVZEJ4TVVZcnpLTUZETmxQQ21iRFNuektnWm5WNURRQmVIMFo0S3dZSVBYWDZRT1NEOU1NczR6ZmtQc3YtOFdzamZqV01kZmVYWWE4UmdsN0RENDhLM3FpS1VxdmVQZWVyeXdkeVVuQ1VlRUNjeWFSVWtWTHM1OEFzM1FKalRFaHVSQVF0eWVkb1EiLCJwIjoiOWNlMzZwTWMyaDdBc19ka1NzRVd0UmtOMHYtclBVWnpYdGh4c0FqNndwUExWRjR5LXhfMVU4ZE9Bb2w3QkRueFJVc3NrOGRhNXpiNDZlREtfbHNValE1UVBjWlhGUDJFcEVJY2pvS0dhajdUbDJab0I4RjRNVExxYnMwNEVSQmdnYnlnMmsxMm41MGp2bDRDMkFRLXc4M3BLbEhCUmI5SWk0UGJ0bTNsU0RFIiwicSI6Im1ZelUyYldvZ1RXY3VpbDR3MnVsV2k1Zlc3ekM5M1VpWWtZRUp6bWZCVVMwbmF4Q3A5ME9rRFhGRFNPN2FHSHNZczlOTkd4X3FaNUt3a2ZNeEhHY3RNMjRjUEJCWjNXSTJTaFYwcldGeFY2ZkJucWI2OU1qOF9WaTV2R1VBMk5ucVBVUXBYS0lSeXJROHJ3Q1k4N1FGLWozb0NUcmYxMmo5Nm5TcjhTTk4yOCIsImRwIjoiU2NsQ3FyYXRzOElGd2tHa0oxa2VreEhKZDYzdjM3NTF4bVNlaE9XOU9vc2FRT0xpMVVkNzVFSHlab3FWbHVnNlNiNU96TExOMUpwSlVoVjllNjBtVjA2VHdtZjRIc0laZnlLbDVoYkRlY1FReS1RZm1TeDVBX1F3TTBHQzhvU0RKSV9YanBJdzZheElYYzlsZFNxWkdUbUpKWDVUMHJlaGROa0tMaE9DQVJFIiwiZHEiOiJPTDNjSWgtSkIwWmloa0N4Q2JZTHdvbUVYNGdmbkFaREVJSERJeU9kNmZwN3JCQnVDVTRkQlpsNUdlUHNheVJVa0NiLTVySjVjcHEyRVprcXlDVWJ2WXlQN2R3NnJ4cTEyVm1ZYldiNjZmYVBXWHVSaHRIZFpWZDJsdFVLMXoyeW5yTUExY0tfTFYxYkhYZndnaVY0ckgxQWxJTlFLeDdWYXIzc3gxc2d2QzAiLCJxaSI6IkdndDlZcm9DSDVvcTJyTDU1bU0wRTRhR0FEMXp5RXRScEtBUUpBV1hQZDhvbFJkeHZkdXlfSnlrbXVVNkRwLW90QnJhUEdudzRpaDlPSjNEY19Fb0R3VUY3ZWRWQU15LXhoemM3WTVCYUllcFQwTjhPZmxfTXJXT04wLTA4OThlX1JwcTNtSVU5dGpVRkRIc3Y5V0laVXBERzNSMWRBazBrTkNYd1NuMmNrVSJ9"
    TZ = "America/Chicago"

    maintenance_host_ssh_key = 'maintenance_host_ssh_key'
    windows_host_ami = ec2.GenericWindowsImage({
        "us-east-2": "ami-0007e91afefcd1257"
        }
    )
    maintenance_host_ssh_key = 'maintenance_host_ssh_key_demo'
    windows_maintenance_host_instance_size = ec2.InstanceSize.SMALL
    
elif os.environ['DEPLOYMENT_ENVIRONMENT'] == 'production':
    aurora_backup_retention = Duration.days(30)
    auto_pause = Duration.hours(8)
    min_serverless_capacity = rds.AuroraCapacityUnit.ACU_4
    max_serverless_capacity = rds.AuroraCapacityUnit.ACU_8
    control_center_memory_limit_mib = 4096
    control_center_cpu = 2048
    optimal_control_center_certificate_arn = 'arn:aws:acm:us-east-2:490995646713:certificate/7b281d83-8e95-49c3-9e1d-20d578d16c75'
    customer_control_center_certificate_arn = 'arn:aws:acm:us-east-2:490995646713:certificate/7b281d83-8e95-49c3-9e1d-20d578d16c75'
    dep_env_prefix = ''
    # ignition_environment_variables
    ACCEPT_IGNITION_EULA = "Y"
    DISABLE_QUICKSTART = "true"
    CONTROL_CENTER_RESTORE_FILE_NAME = "controlcenter.gwbk"
    GATEWAY_SYSTEM_NAME = "controlcenter"
    #'GATEWAY_ADMIN_USERNAME': control_center_gateway_admin_username,
    #'GATEWAY_ADMIN_PASSWORD': control_center_gateway_admin_password,
    GATEWAY_MODULES_ENABLED = "alarm-notification,perspective,tag-historian,reporting,sms-notification,sfc,vision,sql-bridge,opc-ua,symbol-factory"
    IGNITION_EDITION = "standard"
    IGNITION_LICENSE_KEY = ""
    IGNITION_ACTIVATION_TOKEN = ""
    TZ = "America/Chicago"
    maintenance_host_ssh_key = 'maintenance_host_ssh_key_prod'
    windows_host_ami = ec2.GenericWindowsImage({
        "us-east-2": "ami-0007e91afefcd1257"
        }
    )
    maintenance_host_ssh_key = 'maintenance_host_ssh_key_prod'
    windows_maintenance_host_instance_size = ec2.InstanceSize.LARGE
    
control_center_default_file_bucket = f'{dep_env_prefix}control-center-default-file-bucket'

class OptimalControlCenterStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        

# ....................................................
# S3 Bucket for control center init data files
# ....................................................
        control_center_init_file_bucket = s3.Bucket(self, f'{dep_env_prefix}control-center-init-file-bucket', bucket_name=f'{dep_env_prefix}control-center-init-file-bucket', versioned=True, removal_policy=cdk.RemovalPolicy.DESTROY)
        control_center_restore_files_bucket = s3.Bucket(self, f'{dep_env_prefix}control-center-restore-files-bucket', bucket_name=f'{dep_env_prefix}control-center-restore-files-bucket', versioned=True, removal_policy=cdk.RemovalPolicy.DESTROY)

# ....................................................
# VPC
# ....................................................
        self.vpc = ec2.Vpc(self, "VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=3,
            subnet_configuration=[],
            vpc_name='OPTIMAL_VPC' 
        )
        
# ....................................................
#  Create a Private DNS Namespace for dns records of ecs tasks and aurora database
# ....................................................
        self.private_dns_namespace = sd.PrivateDnsNamespace(self, "PrivateNamespace",
            name="optimal.local",
            vpc=self.vpc
        )

# ....................................................
# Subnets
# ....................................................
        optimal_control_center_public_subnet_a = ec2.Subnet(
            self, "Optimal_control_center_public_subnet_a",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.1.0/24",
            availability_zone="us-east-2a",
            map_public_ip_on_launch=True,
        )
        optimal_control_center_public_subnet_b = ec2.Subnet(
            self, "optimal_control_center_public_subnet_b",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.2.0/24",
            availability_zone="us-east-2b",
            map_public_ip_on_launch=True,
        )
        optimal_control_center_public_subnet_c = ec2.Subnet(
            self, "optimal_control_center_public_subnet_c",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.3.0/24",
            availability_zone="us-east-2c",
            map_public_ip_on_launch=True,
        )
        Optimal_database_private_subnet_a = ec2.Subnet(
            self, "Optimal_database_private_subnet_a",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.4.0/24",
            availability_zone="us-east-2a",
        )
        Optimal_database_private_subnet_b = ec2.Subnet(
            self, "Optimal_database_private_subnet_b",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.5.0/24",
            availability_zone="us-east-2b",
        )
        Optimal_database_private_subnet_c = ec2.Subnet(
            self, "Optimal_database_private_subnet_c",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.6.0/24",
            availability_zone="us-east-2c",      
        )
        Customer_subnet_a = ec2.Subnet(
            self, "Customer_subnet_a",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.7.0/24",
            availability_zone="us-east-2a",
            map_public_ip_on_launch=True,
        )
        Customer_subnet_b = ec2.Subnet(
            self, "Customer_subnet_b",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.8.0/24",
            availability_zone="us-east-2b",
            map_public_ip_on_launch=True,
        )
        Customer_subnet_c = ec2.Subnet(
            self, "Customer_subnet_c",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.9.0/24",
            availability_zone="us-east-2c",
            map_public_ip_on_launch=True,
        )
        vpn_subnet_a = ec2.Subnet(
            self, "vpn_subnet_a",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.253.0/24",
            availability_zone="us-east-2a",
            map_public_ip_on_launch=True,
        )
        vpn_subnet_b = ec2.Subnet(
            self, "vpn_subnet_b",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.254.0/24",
            availability_zone="us-east-2b",
            map_public_ip_on_launch=True,
        )
        vpn_subnet_c = ec2.Subnet(
            self, "vpn_subnet_c",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.255.0/24",
            availability_zone="us-east-2c",
            map_public_ip_on_launch=True,
        )
        lambda_subnet_a = ec2.Subnet(
            self, "lambda_subnet_a",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.10.0/24",
            availability_zone="us-east-2a",
        )
        lambda_subnet_b = ec2.Subnet(
            self, "lambda_subnet_b",
            vpc_id=self.vpc.vpc_id,
            cidr_block="10.0.11.0/24",
            availability_zone="us-east-2b",
        )
        
    #Create subnet group for customer substacks to reference      
        self.customer_public_subnet_group = [Customer_subnet_a, Customer_subnet_b, Customer_subnet_c ]

# ....................................................
# Security Groups
# ....................................................
        optimal_control_center_primary_sg = ec2.SecurityGroup(self, "optimal_control_center_primary_sg",
            vpc=self.vpc,
            security_group_name='Optimal control center primary server sg',
            description='Security group that allows inbound traffic to the optimal control center server.',
            allow_all_outbound=True,
        )
        optimal_control_center_backup_sg = ec2.SecurityGroup(self, "optimal_control_center_backup_sg",
            vpc=self.vpc,
            security_group_name='Optimal ignition backup server sg',
            description='Security group that allows inbound traffic to the optimal control center server.',
            allow_all_outbound=True,
        )
        self.optimal_control_center_maintenance_host_sg = ec2.SecurityGroup(self, "optimal_control_center_maintenance_host_sg",
            vpc=self.vpc,
            security_group_name='Optimal control center maintenance hosts sg',
            #security_group_name='Optimal control center maintenance host sg',
            description='Security group that will allow inbound traffic to the optimal control center maintenance host.',
            allow_all_outbound=True,
        )
        optimal_control_center_loadbalancer_sg = ec2.SecurityGroup(self, "optimal_control_center_loadbalancer_sg",
            vpc=self.vpc,
            security_group_name='Optimal control center load balancer sg',
            description='Security group that allows inbound traffic to the optimal control center load balancer.',
            allow_all_outbound=True,
        )
        self.customer_control_center_loadbalancer_sg = ec2.SecurityGroup(self, "customer_control_center_loadbalancer_sg",
            vpc=self.vpc,
            security_group_name='Customer control center load balancer sg',
            description='Security group that allows inbound traffic to the customer control center load balancer.',
            allow_all_outbound=True,
        )
        alarm_query_lambda_sg = ec2.SecurityGroup(self, "alarm_query_lambda_sg",
            vpc=self.vpc,
            security_group_name='Alarm Query Lambda SG',
            description='Alarm Query Lambda SG.',
            allow_all_outbound=True,
        )
        Optimal_database_sg = ec2.SecurityGroup(self, "OptimalDatabaseSG",
            vpc=self.vpc,
            security_group_name='Optimal Database Security Group',
            description='Optimal Database Security Group.',
            allow_all_outbound=True,
        )
        self.Optimal_General_Customer_sg = ec2.SecurityGroup(self, "OptimalGeneralCustomerSG",
            vpc=self.vpc,
            security_group_name='Optimal General Customer SG',
            description='Optimal General Customer Security Group.',
            allow_all_outbound=True,
        )
        optimal_control_center_efs_sg = ec2.SecurityGroup(self, "OptimalControlCenterEFSSG",
            vpc=self.vpc,
            security_group_name='Optimal Control Center EFS SG',
            description='Optimal Control Center EFS Security Group.',
            allow_all_outbound=True,
        )
        vpn_sg = ec2.SecurityGroup(self, "vpnSG",
            vpc=self.vpc,
            security_group_name='Client VPN SG',
            description='Client VPN SG.',
            allow_all_outbound=True,
        )

    #ingress rule creation
        optimal_control_center_efs_sg.add_ingress_rule(
            peer=optimal_control_center_primary_sg,
            connection=ec2.Port.tcp(2049),
            description="Allow NFS from primary control center sg",
        )
        optimal_control_center_efs_sg.add_ingress_rule(
            peer=optimal_control_center_backup_sg,
            connection=ec2.Port.tcp(2049),
            description="Allow NFS from back control center sg",
        )
    #Optimal Control Center ALB port 443 inbound rules (for cloudflare proxy to access only)
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("103.21.244.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("103.22.200.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("103.31.4.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("104.16.0.0/13"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("104.24.0.0/14"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("108.162.192.0/18"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("131.0.72.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("141.101.64.0/18"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("162.158.0.0/15"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("172.64.0.0/13"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("173.245.48.0/20"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("188.114.96.0/20"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("190.93.240.0/20"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("197.234.240.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        optimal_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("198.41.128.0/17"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
# #Optimal Control Center ALB port 80 inbound rules (for cloudflare proxy to access only)
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("103.21.244.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("103.22.200.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("103.31.4.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("104.16.0.0/13"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("104.24.0.0/14"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("108.162.192.0/18"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("131.0.72.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("141.101.64.0/18"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("162.158.0.0/15"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("172.64.0.0/13"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("173.245.48.0/20"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("188.114.96.0/20"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("190.93.240.0/20"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("197.234.240.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         optimal_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("198.41.128.0/17"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
        
   #Optimal Customer Control Center ALB port 443 inbound rules (for cloudflare proxy to access only)
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("103.21.244.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("103.22.200.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("103.31.4.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("104.16.0.0/13"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("104.24.0.0/14"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("108.162.192.0/18"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("131.0.72.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("141.101.64.0/18"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("162.158.0.0/15"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("172.64.0.0/13"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("173.245.48.0/20"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("188.114.96.0/20"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("190.93.240.0/20"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("197.234.240.0/22"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
        self.customer_control_center_loadbalancer_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("198.41.128.0/17"),
            connection=ec2.Port.tcp(443),
            description="Allow communication from cloudflare IP addresses",
        )
#  #Optimal Customer Control Center ALB port 80 inbound rules (for cloudflare proxy to access only)
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("103.21.244.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("103.22.200.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("103.31.4.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("104.16.0.0/13"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("104.24.0.0/14"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("108.162.192.0/18"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("131.0.72.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("141.101.64.0/18"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("162.158.0.0/15"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("172.64.0.0/13"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("173.245.48.0/20"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("188.114.96.0/20"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("190.93.240.0/20"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("197.234.240.0/22"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
#         self.customer_control_center_loadbalancer_sg.add_ingress_rule(
#             peer=ec2.Peer.ipv4("198.41.128.0/17"),
#             connection=ec2.Port.tcp(80),
#             description="Allow communication from cloudflare IP addresses",
#         )
        
    #Optimal Ignition Primary
        optimal_control_center_primary_sg.add_ingress_rule(
            peer=optimal_control_center_backup_sg,
            connection=ec2.Port.tcp(8060),
            description="Allow communication between ignition server main and failover instances",
        )
        optimal_control_center_primary_sg.add_ingress_rule(
            peer=self.Optimal_General_Customer_sg,
            connection=ec2.Port.tcp(8060),
            description="Allow communication between ignition server main and customer instances.",
        )
        optimal_control_center_primary_sg.add_ingress_rule(
            peer=optimal_control_center_loadbalancer_sg,
            connection=ec2.Port.tcp(80),
            description="Allow HTTP",
        )
        optimal_control_center_primary_sg.add_ingress_rule(
            peer=optimal_control_center_loadbalancer_sg,
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS",
        )
        optimal_control_center_primary_sg.add_ingress_rule(
            peer=optimal_control_center_loadbalancer_sg,
            connection=ec2.Port.tcp(8043),
            description="Allow HTTPS",
        )
    #Customer Ignition General Security group
        self.Optimal_General_Customer_sg.add_ingress_rule(
            peer=optimal_control_center_primary_sg,
            connection=ec2.Port.tcp(8060),
            description="Allow communication between ignition server main and customer instances",
        )
    #Optimal Ignition Backup
        optimal_control_center_backup_sg.add_ingress_rule(
            peer=optimal_control_center_primary_sg,
            connection=ec2.Port.tcp(8060),
            description="Allow communication between ignition server main and failover instances",
        )
        optimal_control_center_backup_sg.add_ingress_rule(
            peer=optimal_control_center_loadbalancer_sg,
            connection=ec2.Port.tcp(80),
            description="Allow HTTP and HTTPS",
        )
        optimal_control_center_backup_sg.add_ingress_rule(
            peer=optimal_control_center_loadbalancer_sg,
            connection=ec2.Port.tcp(443),
            description="Allow HTTP and HTTPS",
        )
    #Optimal Database
        Optimal_database_sg.add_ingress_rule(
            peer=optimal_control_center_primary_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow MySQL access from Optimal primary server sg",
        )
        Optimal_database_sg.add_ingress_rule(
            peer=optimal_control_center_backup_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow MySQL access from Optimal backup server sg",
        )
        Optimal_database_sg.add_ingress_rule(
            peer=self.Optimal_General_Customer_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow MySQL access from Optimal backup server sg",
        )
        Optimal_database_sg.add_ingress_rule(
            peer=self.optimal_control_center_maintenance_host_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow MySQL access from Optimal maintenance host sg",
        )
        Optimal_database_sg.add_ingress_rule(
            peer=vpn_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow MySQL access from vpn sg",
        )
        Optimal_database_sg.add_ingress_rule(
            peer=alarm_query_lambda_sg,
            connection=ec2.Port.tcp(3306),
            description="Allow MySQL access from alarm query lambda sg",
        )
    #Optimal Maintenance Host SG
        self.optimal_control_center_maintenance_host_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("67.60.194.217/32"),
            connection=ec2.Port.tcp(22),
            description="Allow ssh from PK ip."
        )
        self.optimal_control_center_maintenance_host_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("67.60.194.217/32"),
            connection=ec2.Port.tcp(3389),
            description="Allow rdp from PK home ip."
        )
        self.optimal_control_center_maintenance_host_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("137.239.237.20/32"),
            connection=ec2.Port.tcp(22),
            description="Allow ssh from PK Atoka ip."
        )
        self.optimal_control_center_maintenance_host_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("137.239.237.20/32"),
            connection=ec2.Port.tcp(3389),
            description="Allow rdp from PK Atoka ip."
        )
        self.optimal_control_center_maintenance_host_sg.add_ingress_rule(
            peer=vpn_sg,
            connection=ec2.Port.tcp(22),
            description="Allow ssh from vpn sg."
        )
        self.optimal_control_center_maintenance_host_sg.add_ingress_rule(
            peer=vpn_sg,
            connection=ec2.Port.tcp(3389),
            description="Allow ssh from vpn sg."
        )
        vpn_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("67.60.194.217/32"),
            connection=ec2.Port.tcp(22),
            description="Allow ssh from vpn sg."
        )
        vpn_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4("137.239.237.20/32"),
            connection=ec2.Port.tcp(22),
            description="Allow ssh from vpn sg."
        )
        
# # ....................................................
# # Connectivity
# # ....................................................
        internet_gateway = ec2.CfnInternetGateway(self, "OptimalVPCInternetGateway")
        
        igw_attachment = ec2.CfnVPCGatewayAttachment(self, 'OptimalVPCIGWAttachment',
            vpc_id=self.vpc.vpc_id,
            internet_gateway_id=internet_gateway.ref
        )

        # #Nat gateway communication if private subnets end up needing internet connectivity
        eip_a = ec2.CfnEIP(self, "eip_a", domain="VPC")
        nat_gateway_a = ec2.CfnNatGateway(self, "nat_gateway_a", allocation_id=eip_a.attr_allocation_id, subnet_id=optimal_control_center_public_subnet_a.subnet_id)

        # #Routes:
        optimal_control_center_public_default_route_subnet_a = ec2.CfnRoute(self, "optimal_control_center_public_default_route_subnet_a", 
            route_table_id=optimal_control_center_public_subnet_a.route_table.route_table_id, 
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        optimal_control_center_public_default_route_subnet_b = ec2.CfnRoute(self, "optimal_control_center_public_default_route_subnet_b", 
            route_table_id=optimal_control_center_public_subnet_b.route_table.route_table_id, 
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        optimal_control_center_public_default_route_subnet_c = ec2.CfnRoute(self, "optimal_control_center_public_default_route_subnet_c", 
            route_table_id=optimal_control_center_public_subnet_c.route_table.route_table_id, 
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        customer_a_default_route = ec2.CfnRoute(self, "customer_a_default_route", 
            route_table_id=Customer_subnet_a.route_table.route_table_id, 
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        customer_b_default_route = ec2.CfnRoute(self, "customer_b_default_route", 
            route_table_id=Customer_subnet_b.route_table.route_table_id,  
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        customer_c_default_route = ec2.CfnRoute(self, "customer_c_default_route", 
            route_table_id=Customer_subnet_c.route_table.route_table_id,  
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        vpn_subnet_a = ec2.CfnRoute(self, "vpn_subnet_a_default_route", 
            route_table_id=vpn_subnet_a.route_table.route_table_id,  
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        vpn_subnet_b = ec2.CfnRoute(self, "vpn_subnet_b_default_route", 
            route_table_id=vpn_subnet_b.route_table.route_table_id,  
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        vpn_subnet_c = ec2.CfnRoute(self, "vpn_subnet_c_default_route", 
            route_table_id=vpn_subnet_c.route_table.route_table_id,  
            destination_cidr_block="0.0.0.0/0", 
            gateway_id=internet_gateway.attr_internet_gateway_id
        )
        # lambda_subnet_a = ec2.CfnRoute(self, "lambda_subnet_a_default_route", 
        #     route_table_id=lambda_subnet_a.route_table.route_table_id,  
        #     destination_cidr_block="0.0.0.0/0", 
        #     gateway_id=nat_gateway_a.attr_nat_gateway_id
        # )
        # lambda_subnet_b = ec2.CfnRoute(self, "lambda_subnet_b_default_route", 
        #     route_table_id=lambda_subnet_b.route_table.route_table_id,  
        #     destination_cidr_block="0.0.0.0/0", 
        #     gateway_id=nat_gateway_a.attr_nat_gateway_id
        # )

# # # ....................................................
# # # S3 VPC endpoint
# # # ....................................................
#         self.vpc.add_gateway_endpoint(
#             'S3Endpoint',
#             service=ec2.GatewayVpcEndpointAwsService.S3,
#         )

# ....................................................       
# RDS Aurora Serverless
# ....................................................
        optimal_aurora_private_subnet_group = rds.SubnetGroup(
            self,
            'optimal-aurora-private-subnet-group',
            vpc=self.vpc,
            description='The subnet for all Optimal aurora database.',
            subnet_group_name='optimal-aurora-private-subnet-group',
            vpc_subnets=ec2.SubnetSelection(
                subnets=[Optimal_database_private_subnet_a, Optimal_database_private_subnet_b, Optimal_database_private_subnet_c],
            ),
        )

        optimal_aurora_cluster = rds.ServerlessCluster(
            self,
            'optimal-aurora-cluster',
            cluster_identifier='Optimal-aurora',
            credentials=rds.Credentials.from_generated_secret(secret_name="aurora_credentials", username="clusteradmin"),  # Optional - will default to 'admin' username and generated password
            default_database_name='OptimalAurora',
            deletion_protection=False,
            backup_retention=aurora_backup_retention,
            #enable_data_api=True,
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_2_08_3),
            vpc=self.vpc,
            security_groups=[Optimal_database_sg],
            subnet_group=optimal_aurora_private_subnet_group,
            vpc_subnets=ec2.SubnetSelection(
                subnets=[Optimal_database_private_subnet_a, Optimal_database_private_subnet_b, Optimal_database_private_subnet_c],
            ),
            scaling=rds.ServerlessScalingOptions(
                auto_pause=auto_pause,
                min_capacity=min_serverless_capacity,
                max_capacity=max_serverless_capacity,
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        
        # Creating a service discovery and DNS entry in the private zone managed by aws cloud map
        aurora_db_service = self.private_dns_namespace.create_service('AuroraDatabaseService',
            description='Service Discovery for Aurora DB',
            dns_record_type=sd.DnsRecordType.CNAME,  # Use 'CNAME' record type for IP address
            dns_ttl=cdk.Duration.minutes(1),     # Time to live for the DNS records
            health_check=None,
            name=f'mysql' #This is the part of the CNAME record that hosts use to reach the optimal-aurora database.
        )
        
        sd.CnameInstance(self, 'AuroraInstanceDnsEndpoint',
            service=aurora_db_service,
            instance_id=optimal_aurora_cluster.cluster_identifier,
            instance_cname=optimal_aurora_cluster.cluster_endpoint.hostname
        )
        

   #### FUTURE STATE>> I THINK WE SHOULD PUT IN AN RDS PROXY 
        
        # # Create an RDS Proxy
        # #rds_proxy_name = "MyRDSProxy"
        # ords_proxy = rds_proxy.CfnDBProxy(
        #     self, "RDSProxy",
        #     debug_logging=False,
        #     debug_logging_log_level="DISABLED",
        #     engine_family="MYSQL",
        #     idle_client_timeout=1800,
        #     require_tls=True,
        #     #role_arn="YOUR_IAM_ROLE_ARN",  # Replace with your IAM role ARN
        #     vpc_security_group_ids=[Optimal_database_sg],  # Replace with your security group IDs
        #     vpc_subnet_ids=[optimal_aurora_private_subnet_group],  # Replace with your subnet IDs
        # )

        # # Allow the RDS Proxy to connect to the Aurora cluster
        # optimal_aurora_cluster.connections.allow_default_port_from(rds_proxy)
        
# ....................................................       
# Fargate Customer Cluster
# ....................................................
        if os.environ[ 'DEPLOYMENT_ENVIRONMENT' ] != 'demo':
            self.customer_control_center_fargate_cluster = ecs.Cluster(self, 
                'customer_control_center_fargate_cluster',
                cluster_name='customer_control_center_fargate_cluster',
                vpc=self.vpc
            )
# # ....................................................       
# # Fargate cluster Optimal Control Center
# # ....................................................
        self.optimal_control_center_fargate_cluster = ecs.Cluster(self, 
            'optimal_control_center_fargate_cluster',
            cluster_name='optimal_control_center_fargate_cluster',
            vpc=self.vpc
        )

# ....................................................       
# Fargate IAM
# ....................................................
        optimal_control_center_role = iam.Role(
            self,
            'optimal_control_center_role',
            role_name='optimal_control_center_role',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        )
        optimal_control_center_role.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        
        optimal_control_center_policy_document_json = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': [
                        'logs:CreateLogGroup'
                    ],
                    'Resource': [
                        f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:*'
                    ]
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'logs:CreateLogStream',
                        'logs:PutLogEvents'
                    ],
                    'Resource': [
                        f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:log-group:/optimal/:*'
                    ]
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'elasticfilesystem:*'
                    ],
                    'Resource': [
                        f'arn:aws:elasticfilesystem:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:*'
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecs:ExecuteCommand",
                        "ssm:StartSession"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        optimal_control_center_policy_document = iam.PolicyDocument.from_json(optimal_control_center_policy_document_json)
        iam.ManagedPolicy(
            self,
            'optimal_control_center_policy_doc',
            managed_policy_name='optimal_control_center_policy',
            document=optimal_control_center_policy_document,
            roles=[optimal_control_center_role],
        )

        optimal_control_center_init_role = iam.Role(
            self,
            'optimal_control_center_init_role',
            role_name='optimal_control_center_init_role',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        )
        optimal_control_center_init_role.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        
        optimal_control_center_init_policy_document_json = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': [
                        'logs:CreateLogGroup'
                    ],
                    'Resource': [
                        f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:*'
                    ]
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'logs:CreateLogStream',
                        'logs:PutLogEvents'
                    ],
                    'Resource': [
                        f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:log-group:/optimal/:*'
                    ]
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'elasticfilesystem:*'
                    ],
                    'Resource': [
                        f'arn:aws:elasticfilesystem:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:*'
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetRepositoryPolicy",
                        "ecr:DescribeRepositories",
                        "ecr:ListImages",
                        "ecr:DescribeImages",
                        "ecr:GetImage",
                        "ecr:GetObject"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject"
                    ],
                    
                    "Resource": [
                        f"arn:aws:s3:::{dep_env_prefix}control-center-restore-files-bucket/*",
                        f"arn:aws:s3:::{dep_env_prefix}control-center-init-file-bucket/*"
                    ]

                }
            ]
        }
        
        optimal_control_center_init_policy_document = iam.PolicyDocument.from_json(optimal_control_center_init_policy_document_json)
        iam.ManagedPolicy(
            self,
            'optimal_control_center_init_policy_doc',
            managed_policy_name='optimal_control_center_init_policy',
            document=optimal_control_center_init_policy_document,
            roles=[optimal_control_center_init_role],
        )
        
# # ....................................................       
# # Fargate Tasks Optimal Control Center PRIMARY
# # ....................................................
        # optimal_control_center_repository = ecr.Repository.from_repository_attributes(self, 'optimal_control_center_repository',
        #     repository_name='optimal-control-center',
        #     repository_arn=f'arn:aws:ecr:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:repository/optimal-control-center',
        # )
        
        # Create an EFS file system
        optimal_control_center_primary_efs_data_file_system = efs.FileSystem(self, "OptimalControlCenterEfsDataFolderFileSystem",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=[Optimal_database_private_subnet_a, Optimal_database_private_subnet_b, Optimal_database_private_subnet_c],
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY,
            security_group=optimal_control_center_efs_sg
        )
        # Define the EFS volume
        optimal_control_center_primary_efs_data_volume = ecs.Volume(name="optimal_control_center_primary_efs_data_volume", efs_volume_configuration=ecs.EfsVolumeConfiguration(
            file_system_id=optimal_control_center_primary_efs_data_file_system.file_system_id,
            root_directory="/",
            #transit_encryption='ENABLED'
            )
        )
        optimal_control_center_primary_efs_data_file_system.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        
        # Create a Fargate task definition
        optimal_control_center_task_definition = ecs.FargateTaskDefinition(self, 'optimal_control_center_task_definition',
            memory_limit_mib=control_center_memory_limit_mib,
            cpu=control_center_cpu,
            # memory_limit_mib=4096,
            # cpu=2048,
            family='optimal-control-center',
            task_role=optimal_control_center_role,
            volumes=[optimal_control_center_primary_efs_data_volume]
        )
        
        optimal_control_center_log_group = logs.LogGroup(self, 'optimal_control_center_log_group', log_group_name='/optimal/control-center/', removal_policy=cdk.RemovalPolicy.DESTROY, retention=logs.RetentionDays.ONE_YEAR)
        optimal_control_center_primary_service_container = optimal_control_center_task_definition.add_container('optimal_control_center_primary_service',
            container_name='control_center_primary',
            command=["/usr/local/share/ignition/data/.optimal_init_files/init.sh"],
            entry_point=["sh","-c"],
            image=ecs.ContainerImage.from_registry("inductiveautomation/ignition:8.1.36"),
            memory_limit_mib=control_center_memory_limit_mib,
            environment={
                "ACCEPT_IGNITION_EULA": ACCEPT_IGNITION_EULA,
                "DISABLE_QUICKSTART": DISABLE_QUICKSTART,
                "CONTROL_CENTER_RESTORE_FILE_NAME": CONTROL_CENTER_RESTORE_FILE_NAME,
                "GATEWAY_SYSTEM_NAME": GATEWAY_SYSTEM_NAME,
                #'GATEWAY_ADMIN_USERNAME': control_center_gateway_admin_username,
                #'GATEWAY_ADMIN_PASSWORD': control_center_gateway_admin_password,
                "GATEWAY_MODULES_ENABLED": GATEWAY_MODULES_ENABLED,
                "IGNITION_EDITION": IGNITION_EDITION,
                "IGNITION_ACTIVATION_TOKEN": IGNITION_ACTIVATION_TOKEN,
                "IGNITION_LICENSE_KEY": IGNITION_LICENSE_KEY,
                "TZ": TZ
            },
            #health_check=[https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_ecs/HealthCheck.html],
            logging=ecs.LogDriver.aws_logs(stream_prefix='/control-center-task', log_group=optimal_control_center_log_group),
            #port_mappings=[ecs.PortMapping(container_port=8088), ecs.PortMapping(container_port=8043)],
            port_mappings=[ecs.PortMapping(container_port=8043)],
            stop_timeout=Duration.seconds(10)
        )

        # Mount the EFS file system to the container
        optimal_control_center_primary_service_container.add_mount_points(
            ecs.MountPoint(
                container_path="/usr/local/share/ignition/",
                source_volume="optimal_control_center_primary_efs_data_volume",
                read_only=False
            )
        )
        
        optimal_control_center_primary_service = ecs.FargateService(self, 'optimal_control_center_primary_service', 
            cluster=self.optimal_control_center_fargate_cluster,
            enable_execute_command=True,
            assign_public_ip=True,
            task_definition=optimal_control_center_task_definition,
            desired_count=1, 
            security_groups=[optimal_control_center_primary_sg],
            service_name=f"controlcenter",  # This will be the name in the service discovery
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=self.private_dns_namespace,
                name=f"controlcenter"
            ),
            vpc_subnets=ec2.SubnetSelection(
                subnets=[optimal_control_center_public_subnet_a, optimal_control_center_public_subnet_b, optimal_control_center_public_subnet_c],
            ),
        )
        optimal_control_center_primary_service.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        optimal_control_center_primary_service.node.add_dependency(self.private_dns_namespace)
        
# # ....................................................       
# # Fargate Tasks Optimal Control Center data file init helper
# # ....................................................
        # Create a Fargate task definition
        optimal_control_center_init_task_definition = ecs.FargateTaskDefinition(self, 'optimal_control_center_init_task_definition',
            memory_limit_mib=512,
            cpu=256,
            family='optimal_control_center_init_task',
            task_role=optimal_control_center_init_role,
            #volumes=[optimal_control_center_primary_efs_data_volume]
            volumes=[optimal_control_center_primary_efs_data_volume]
        )
        
        optimal_control_center_init_log_group = logs.LogGroup(self, 'optimal_control_center_init_log_group', log_group_name='/optimal/control-center_init/', removal_policy=cdk.RemovalPolicy.DESTROY, retention=logs.RetentionDays.ONE_YEAR)

        optimal_control_center_init_repository = ecr.Repository.from_repository_attributes(self, f'{dep_env_prefix}optimal_control_center_init_repository',
            repository_name=f'{dep_env_prefix}optimal_control_center_init_data_helper',
            repository_arn=f'arn:aws:ecr:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:repository/{dep_env_prefix}optimal_control_center_init_data_helper',
        )
        optimal_control_center_init_service_container = optimal_control_center_init_task_definition.add_container('optimal_control_center_init_service',
            container_name='optimal_control_center_init',
            image=ecs.ContainerImage.from_ecr_repository(optimal_control_center_init_repository, tag='latest'),
            memory_limit_mib=512,
            #essential=False,
            environment={
                    "CONTROL_CENTER_RESTORE_FILE_NAME": f"controlcenter.gwbk",
                    "EFS_MOUNT_POINT": "/mnt/efs",
                    "S3_DATA_ZIP_BUCKET": f"{dep_env_prefix}control-center-init-file-bucket",
                    "S3_RESTORE_ZIP_BUCKET": f"{dep_env_prefix}control-center-restore-files-bucket"
                },
            logging=ecs.LogDriver.aws_logs(stream_prefix='/optimal_control_center_init', log_group=optimal_control_center_init_log_group),
            stop_timeout=Duration.seconds(10)
        )

        # Mount the EFS file system to the container
        optimal_control_center_init_service_container.add_mount_points(
            ecs.MountPoint(
                container_path="/mnt/efs", 
                source_volume="optimal_control_center_primary_efs_data_volume",
                read_only=False
            )
        )
        
        optimal_control_center_init_service = ecs.FargateService(self, 'optimal_control_center_init_service', 
            cluster=self.optimal_control_center_fargate_cluster,
            assign_public_ip=True,
            task_definition=optimal_control_center_init_task_definition,
            service_name='optimal_control_center_init',
            desired_count=1, 
            security_groups=[optimal_control_center_primary_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnets=[optimal_control_center_public_subnet_a, optimal_control_center_public_subnet_b, optimal_control_center_public_subnet_c],
            ),
        )
        optimal_control_center_init_service.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

# ....................................................       
# ALB Control Center
# ....................................................
        self.optimal_control_center_loadbalancer = elbv2.ApplicationLoadBalancer(
            self,
            'optimal_control_center_lb',
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=[optimal_control_center_public_subnet_a, optimal_control_center_public_subnet_b, optimal_control_center_public_subnet_c],
            ),
            load_balancer_name='optimal-control-center-lb',
            security_group=optimal_control_center_loadbalancer_sg,
            internet_facing=True
        )
        self.optimal_control_center_loadbalancer.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        optimal_control_center_loadbalancer_listener_80 = self.optimal_control_center_loadbalancer.add_listener('optimal_control_center_loadbalancer_80_Listener', port=80)
        optimal_control_center_loadbalancer_listener_80.add_action(
            'Port80Action',
            action=elbv2.ListenerAction.redirect(
                port='443', protocol='HTTPS',
                permanent=True,
            )
        )

        optimal_control_center_loadbalancer_listener_certificate = elbv2.ListenerCertificate.from_arn(
            optimal_control_center_certificate_arn)

        optimal_control_center_443_listener = self.optimal_control_center_loadbalancer.add_listener(
            'control_center_loadbalancer_443_Listener',
            port=443,
            certificates=[optimal_control_center_loadbalancer_listener_certificate],
            default_action=elbv2.ListenerAction.fixed_response(503)
        )
        optimal_control_center_service_health_check = elbv2.HealthCheck(path='/', healthy_http_codes='200,302', unhealthy_threshold_count=2)

        optimal_control_center_service_target_group = elbv2.ApplicationTargetGroup(self, 'optimal_control_center_tg',
            target_group_name='optimal-control-center-tg',
            target_type=elbv2.TargetType.IP,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            port=443,
            health_check=optimal_control_center_service_health_check,
            vpc=self.vpc
        )
        
        optimal_control_center_listener_rule_443 = elbv2.ApplicationListenerRule(self, 'optimal_control_center_listener_rule_443',
            listener=optimal_control_center_443_listener,
            priority=2,
            action=elbv2.ListenerAction.forward(target_groups=[optimal_control_center_service_target_group]),
            conditions=[elbv2.ListenerCondition.host_headers([f'{dep_env_prefix}controlcenter.optimalpipeline.io'])],
        )
        optimal_control_center_service_target_group.add_target(optimal_control_center_primary_service)
        
# # ....................................................       
# # ALB Customer
# # ....................................................
        if os.environ[ 'DEPLOYMENT_ENVIRONMENT' ] != 'demo':
            self.customer_control_center_loadbalancer = elbv2.ApplicationLoadBalancer(
                self,
                'customer_control_center_lb',
                vpc=self.vpc,
                vpc_subnets=ec2.SubnetSelection(
                    #subnets=[subnets[0], subnets[1], subnets[2]],
                    subnets=[Customer_subnet_a, Customer_subnet_b, Customer_subnet_c]
                ),
                load_balancer_name='customer-control-center-lb',
                security_group=self.customer_control_center_loadbalancer_sg,
                internet_facing=True
            )
            self.customer_control_center_loadbalancer.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
            customer_control_center_loadbalancer_listener_80 = self.customer_control_center_loadbalancer.add_listener('customer_control_center_loadbalancer_80_Listener', port=80)
            customer_control_center_loadbalancer_listener_80.add_action(
                'Port80Action',
                action=elbv2.ListenerAction.redirect(
                    port='443', protocol='HTTPS',
                    permanent=True,
                )
            )

            customer_control_center_loadbalancer_listener_certificate = elbv2.ListenerCertificate.from_arn(
                customer_control_center_certificate_arn)

            self.customer_control_center_443_listener = self.customer_control_center_loadbalancer.add_listener(
                'customer_control_center_loadbalancer_443_Listener',
                port=443,
                certificates=[customer_control_center_loadbalancer_listener_certificate],
                default_action=elbv2.ListenerAction.fixed_response(503)
            )
            
            self.optimal_control_center_service_health_check = elbv2.HealthCheck(path='/', healthy_http_codes='200,302', unhealthy_threshold_count=2)

            cdk.CfnOutput(self, "customer_control_center_loadbalancer_dns_output", value=self.customer_control_center_loadbalancer.load_balancer_dns_name)   
        
# ....................................................       
# EC2 Maintenance instances
# ....................................................   
#This host is used to mount the EFS to a volume and copy over the initial files. This may not be needed moving forward and also can be deleted after everything is working.
        maintenance_host = ec2.Instance(self, "maintenance_host",
                vpc=self.vpc,
                instance_name='maint_host_linux',
                instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
                machine_image=linux_maint_host_ami,
                private_ip_address='10.0.1.100',
                security_group=self.optimal_control_center_maintenance_host_sg,
                vpc_subnets=ec2.SubnetSelection(
                    subnets=[optimal_control_center_public_subnet_a, optimal_control_center_public_subnet_b, optimal_control_center_public_subnet_c],
                ),
                key_name=maintenance_host_ssh_key,
                
                )
        maintenance_host.connections.allow_to(optimal_control_center_primary_efs_data_file_system, ec2.Port.tcp(2049))
        maintenance_host.user_data.add_commands(
            "apt-get check-update -y", "apt-get upgrade -y", "apt-get install -y amazon-efs-utils", "apt-get install -y nfs-utils", "apt-get install nfs-common -y", "apt-get install -y mysql", "mkdir /mnt/optimal_control_center_init", "mkdir /mnt/optimal_control_center_data",
            #f"echo mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport {optimal_control_center_efs_file_system.file_system_id}.efs.{DEFAULT_REGION}.amazonaws.com:/ /mnt/optimal_control_center_init",
            f"mount -t nfs -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport {optimal_control_center_primary_efs_data_file_system.file_system_id}.efs.{DEFAULT_REGION}.amazonaws.com:/ /mnt/optimal_control_center_data",
# need to add apt install mysql-client-core-8.0 to install mysql client to ubuntu...
        )
       # IAM role for EC2 instances in the fleet
        maint_instance_role = iam.Role(
            self, "FleetInstanceRole",
            assumed_by=iam.ServicePrincipal('ec2.amazonaws.com')
        )

        # Attach managed policies (adjust this as needed)
        maint_instance_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonSSMManagedInstanceCore'))

        # maintenance_host_windows = ec2.Instance(self, "maintenance_host_windows",
        #         vpc=self.vpc,
        #         instance_name='maint-host-win',
        #         instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3_AMD, windows_maintenance_host_instance_size),
        #         machine_image=windows_host_ami,
        #         private_ip_address='10.0.1.101',
        #         security_group=self.optimal_control_center_maintenance_host_sg,
        #         vpc_subnets=ec2.SubnetSelection(
        #             subnets=[optimal_control_center_public_subnet_a, optimal_control_center_public_subnet_b, optimal_control_center_public_subnet_c],
        #         ),
        #         key_name=maintenance_host_ssh_key,
        #         role=maint_instance_role,
        #         user_data=ec2.UserData.custom(windows_maintenance_host_user_data)
        #         )
 
        #maintenance_host_windows.user_data.add_commands(
            # Set the new computer name and Change the computer name
            
        #)

# ....................................................       
# Create control_center_init_lambda
# ....................................................  
# had to move to private subnet and also create an s3 gateway endpoint for this to hit s3
# PROBABLY SHOULD ADD THE S3 GATEWAY ENDPOINT TO THE CDK 
        control_center_init_lambda_role = iam.Role(
            self,
            'control_center_init_lambda_role',
            role_name='control_center_init_lambda_role',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
        )
        control_center_init_lambda_role.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        control_center_init_lambda_policy_document_json = {
            'Version': '2012-10-17',
            'Statement': [
               {
                    'Effect': 'Allow',
                    'Action': [
                        '*'
                    ],
                    'Resource': [
                        f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:*'
                    ]
                },
                # {
                #     'Effect': 'Allow',
                #     'Action': [
                #         'logs:CreateLogGroup',
                #         "ec2:CreateNetworkInterface",
                #         "ec2:DescribeNetworkInterfaces",
                #         "ec2:DeleteNetworkInterface"
                #     ],
                #     'Resource': [
                #         f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:*'
                #     ]
                # },
                # {
                #     'Effect': 'Allow',
                #     'Action': [
                #         'logs:CreateLogStream',
                #         'logs:PutLogEvents'
                #     ],
                #     'Resource': [
                #         f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:log-group:/optimal/:*'
                #     ]
                # },
                # {
                #     'Effect': 'Allow',
                #     'Action': [
                #         'elasticfilesystem:*'
                #     ],
                #     'Resource': [
                #         f'arn:aws:elasticfilesystem:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:*'
                #     ]
                # }
            ]
        }
        
        control_center_init_lambda_policy_document = iam.PolicyDocument.from_json(control_center_init_lambda_policy_document_json)
        iam.ManagedPolicy(
            self,
            'control_center_init_lambda_policy_doc',
            managed_policy_name='control_center_init_lambda_policy',
            document=control_center_init_lambda_policy_document,
            roles=[control_center_init_lambda_role],
        )

        # Attach a policy to the role to allow Lambda to mount EFS
        control_center_init_lambda_efs_mount_policy = iam.Policy(
            self, "control_center_init_lambda_efs_mount_policy",
            statements=[
                iam.PolicyStatement(
                    actions=["elasticfilesystem:ClientMount"],
                    resources=[optimal_control_center_primary_efs_data_file_system.file_system_arn],
                ),
                iam.PolicyStatement(
                    actions=["*"],
                    resources=["*"],
                )
            ],
            roles=[control_center_init_lambda_role]
        )
        access_point = optimal_control_center_primary_efs_data_file_system.add_access_point(
            "LambdaAccessPoint",
            create_acl=efs.Acl(
                owner_uid="2003",
                owner_gid="2003",
                permissions="755"
            ),
            posix_user=efs.PosixUser(
                uid="2003",
                gid="2003"
            )
        )
        
        # Create the Lambda function
        control_panel_init_s3_copy_lambda = _lambda.Function(
            self, "control_panel_gwbk_s3_copy_lambda",
            description=f"Optimal Control Center lambda to copy new gwbk from s3 to efs when a new gwbk is copied to s3.",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            function_name="control_panel_gwbk_s3_copy_lambda",
            #log_retention=logs.RetentionDays.ONE_MONTH,
            code=_lambda.Code.from_asset("optimal_infrastructure/optimal_control_center/control_center_restore_file_lambda/"),  # Place your Lambda code in a 'control_center_init_lambda' directory
            environment={
                'CUSTOMER_NAME': customer_name,
                'CONTROL_CENTER_RESTORE_FILE_NAME': f'{customer_name}.gwbk',
                #'GWBK_RESTORE_BUCKET': f'{dep_env_prefix}{customer_name}-restore-files-bucket'
                'GWBK_RESTORE_BUCKET': f'{dep_env_prefix}control-center-restore-files-bucket'
            },
            role=control_center_init_lambda_role,
            timeout=Duration.seconds(30),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=[optimal_control_center_public_subnet_a, optimal_control_center_public_subnet_b, optimal_control_center_public_subnet_c],
            ),
            filesystem=_lambda.FileSystem.from_efs_access_point(
                ap=access_point,
                #efs_access_point_id=optimal_control_center_efs_file_system,  # Replace with your EFS access point ID
                mount_path="/mnt/efs"
            )
        )

        # # Grant Lambda the necessary permissions to the EFS
        optimal_control_center_primary_efs_data_file_system.grant(control_panel_init_s3_copy_lambda, "elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite")
        control_panel_init_s3_copy_lambda.add_event_source(lambda_event_sources.S3EventSource(
            control_center_restore_files_bucket,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[s3.NotificationKeyFilter(suffix="controlcenter.gwbk")]
        ))
        control_panel_init_s3_copy_lambda.add_event_source(lambda_event_sources.S3EventSource(
            control_center_restore_files_bucket,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[s3.NotificationKeyFilter(suffix="ssl.pfx")]
        ))
        
# ....................................................       
# Outputs Section
# ....................................................        
        #cdk.CfnOutput(self, "customer_control_center_loadbalancer_dns_output", value=self.customer_control_center_loadbalancer.load_balancer_dns_name)
        cdk.CfnOutput(self, "optimal_control_center_loadbalancer_dns_output", value=self.optimal_control_center_loadbalancer.load_balancer_dns_name)   
        #cdk.CfnOutput(self, "optimal_control_center_efs_file_system.file_system_id", value=optimal_control_center_efs_file_system.file_system_id)
        #cdk.CfnOutput(self, "optimal_control_center_efs_data_system.file_system_id", value=optimal_control_center_primary_efs_data_file_system.file_system_id)
        #cdk.CfnOutput(self, "optimal_control_center_backup_efs_file_system.file_system_id", value=optimal_control_center_backup_efs_file_system.file_system_id)
        cdk.CfnOutput(self, "VpcIdOutput", value=self.vpc.vpc_id)
        cdk.CfnOutput(self, "CustomerSubnetsOutput", value=",".join([subnet.subnet_id for subnet in self.customer_public_subnet_group]))
        
        
        
        #cdk.CfnOutput(self, "SecurityGroupsOutput", value=",".join([cdk.ec2.security_group.security_group_id for sg in vpc.security_groups]))
        
        # STORE THE VPC ID IN PARAMETER STORE FOR OTHER STACKS
        vpc_id_parameter = ssm.StringParameter(self, "vpc_id",
            parameter_name='optimal_vpc_id',
            string_value=self.vpc.vpc_id
        )
        # Store alarm lambda security group to be used by alarm lambda stack
        alarm_lambda_sg_parameter = ssm.StringParameter(self, "alarm_lambda_sg_parameter",
            parameter_name='alarm_lambda_sg_parameter',
            string_value=alarm_query_lambda_sg.security_group_id
        )
        #Storing database subnets ids for alarm_lambda_subnets     
        lambda_subnet_group_for_alarm_lambda_subnet_a = ssm.StringParameter(self, 'alarm_lambda_subnet_a',
            parameter_name='alarm_lambda_subnet_parameter_subnet_a',
            string_value=lambda_subnet_a.subnet_id,
        )
        lambda_subnet_group_for_alarm_lambda_subnet_b = ssm.StringParameter(self, 'alarm_lambda_subnet_b',
            parameter_name='alarm_lambda_subnet_parameter_subnet_b',
            string_value=lambda_subnet_b.subnet_id,
        )
            
        #I would like this to work but moving on...
        # secretsmanager.Secret(self, "optimal_control_center_admin_credentials",
        #     secret_object_value={
        #     "username": control_center_gateway_admin_username,
        #     #"database": SecretValue.unsafe_plain_text("foo"),
        #     "password": control_center_gateway_admin_password
        #     }
        # )
        
##################################
# Add the tags to the Fargate services and EFS file system
# This was working but created problems when testing and add/removing...
##################################
    # for key, value in tags.items():
        #cdk.Tags.of(optimal_control_center_init_service).add(key, value)
        #cdk.Tags.of(optimal_control_center_primary_service).add(key, value)
        #cdk.Tags.of(optimal_control_center_primary_efs_data_file_system).add(key, value)    
    
    
    
    
    
# # ....................................................       
# # Create a Client VPN endpoint
# # ....................................................  
# Currently using an Openvpn instance manually configured... This sec group does need to be in place. 
# The VPN instance needs to be in the maintenance security group to be able to communicate with Aurora
        # aws_client_vpn_log_group = logs.LogGroup(self, 'aws_client_vpn_log_group', log_group_name='/optimal/client_vpn/', removal_policy=cdk.RemovalPolicy.DESTROY, retention=logs.RetentionDays.ONE_MONTH)

#         client_vpn_endpoint = ec2.ClientVpnEndpoint(self, 'MyClientVpnEndpoint',
#             vpc=self.vpc,
#             client_cidr_block='10.100.0.0/24',
#             server_certificate_arn='arn:aws:acm:region:account-id:certificate/certificate-id',
#             #client_connection_handler=ec2.ClientVpnConnectionHandler.SELF,
#             transport_protocol=ec2.TransportProtocol.UDP,
#             authentication_options=[
#                 ec2.ClientVpnAuthenticationOptions(
#                     type=ec2.ClientVpnAuthenticationType.FEDERATED,
#                     federated=ec2.ClientVpnFederatedAuthentication(saml_provider_arn=saml_provider_arn)
#                 )
#             ],
#             #client_connection_handler=ec2.ClientVpnConnectionHandler.SELF,
#             #transport_protocol=ec2.ClientVpnEndpointTransportProtocol.UDP,
#             # authentication_options=[
#             #     ec2.ClientVpnAuthenticationOptions(
#             #         type=ec2.ClientVpnAuthenticationType.USER_PASSWORD,
#             #         active_directory=ec2.ClientVpnUserBasedAuthentication(
#             #             active_directory_id='d-1234567890'
#             #         )
#             #     )
#             # ],
#             dns_servers=['8.8.8.8'],
#             user_based_authentication=ec2.ClientVpnUserBasedAuthentication.federated(saml_provider='arn:aws:sso:::instance/ssoins-6684df608d7284d6')
#         )

#         # Grant the VPN endpoint access to the VPC
#         client_vpn_endpoint.add_vpc_subnets(subnets=[vpn_subnet_a, vpn_subnet_b, vpn_subnet_c])

#         # Create a security group and associate it with the VPN endpoint
#         security_group = ec2.SecurityGroup(self, 'MySecurityGroup',
#             vpc=self.vpc,
#             allow_all_outbound=True,
#         )

#         client_vpn_endpoint.add_security_groups(security_groups=[vpn_sg])
        
        # control_center_init_lambda_efs_mount = efs.FileSystem(
        #     self, "EfsFileSystem",
        #     vpc=self.vpc.vpc_id  
        # )
        