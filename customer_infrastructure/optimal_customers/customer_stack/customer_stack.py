import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_efs as efs,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
    aws_logs as logs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_s3 as s3,
    aws_servicediscovery as sd,
    Duration,
    Tags
)
import os


DEFAULT_ACCOUNT = (os.environ['CDK_DEFAULT_ACCOUNT'])
DEFAULT_REGION = (os.environ['CDK_DEFAULT_REGION'])
DEPLOYMENT_ENVIRONMENT = os.environ['DEPLOYMENT_ENVIRONMENT']

class CustomerStack(cdk.Stack):

    def __init__(self, scope: cdk.App, construct_id: str, customer_name, cluster_name, customer_load_balancer_sg_id, maint_host_sg, security_group, customer_subnet_a_id, customer_subnet_b_id, customer_subnet_c_id, lambda_subnet_a_id, lambda_subnet_b_id, listener, priority, private_dns_namespace, private_dns_namespace_arn, vpc, **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)
        
        print(f'Customer {customer_name} stack deployment to: {DEPLOYMENT_ENVIRONMENT}')
        print(f'DEPLOYMENT_ENVIRONMENT: {DEPLOYMENT_ENVIRONMENT}')
        print(f'Region: {DEFAULT_REGION}')

        customer_name = customer_name
        print(f'customer_name: {customer_name}')
        tags = {
            'Environment': f'{DEPLOYMENT_ENVIRONMENT}',
            'cost_center': f'{customer_name}',
        }
        if os.environ['DEPLOYMENT_ENVIRONMENT'] == 'sandbox':
            memory_limit_mib = 8192
            cpu = 2048
            dep_env_prefix = 'dev-'
        elif os.environ['DEPLOYMENT_ENVIRONMENT'] == 'production':
            memory_limit_mib = 8192
            cpu = 2048
            dep_env_prefix = ''
            
        # Enumerate usable array of customer subnets (creating a usable customer_subnets array from imported IDs)
        customer_subnet_ids = [customer_subnet_a_id, customer_subnet_b_id, customer_subnet_c_id]

        # Import subnets using their IDs
        customer_subnets = []
        for i, subnet_id in enumerate(customer_subnet_ids, start=1):
            subnet = ec2.Subnet.from_subnet_attributes(
                self, f"CustomerImportedSubnet{i}",
                subnet_id=subnet_id,
                # You must provide at least one of availability_zone or availability_zone_id
                # If not known, you can specify a dummy value, but be aware this may have implications
                availability_zone=f"dummy-{i}"
            )
            customer_subnets.append(subnet)
            
        # Enumerate usable array of lambda subnets (creating a usable lambda_subnets array from imported IDs)
        lambda_subnet_ids = [lambda_subnet_a_id, lambda_subnet_b_id]

        # Import subnets using their IDs
        lambda_subnets = []
        for i, subnet_id in enumerate(lambda_subnet_ids, start=1):
            subnet = ec2.Subnet.from_subnet_attributes(
                self, f"LambdaImportedSubnet{i}",
                subnet_id=subnet_id,
                # You must provide at least one of availability_zone or availability_zone_id
                # If not known, you can specify a dummy value, but be aware this may have implications
                availability_zone=f"dummy-{i}"
            )
            lambda_subnets.append(subnet)
# ....................................................
# S3 Bucket for customer control center restore (gwbk, uuid, keystore) files
# ....................................................
        control_center_restore_files_bucket = s3.Bucket(self, f'{dep_env_prefix}{customer_name}-control-center-restore-files-bucket', bucket_name=f'{dep_env_prefix}{customer_name}-control-center-restore-files-bucket', versioned=True, removal_policy=cdk.RemovalPolicy.DESTROY)
# ....................................................       
# Security Group and ingress rules
# ....................................................
        customer_sg = ec2.SecurityGroup(self, f"{customer_name}SG",
            vpc=vpc,
            security_group_name=f'{customer_name} Security Group',
            description=f'{customer_name} Security Group.',
            allow_all_outbound=True,
        )
        customer_control_center_init_helper_sg = ec2.SecurityGroup(self, f"{customer_name}CustomerControlCenterInitHelperSG",
            vpc=vpc,
            security_group_name=f'{customer_name} Customer Control Center Init Helper SG',
            description=f'{customer_name} Customer Control Center Init Helper Security Group.',
            allow_all_outbound=True,
        )
        customer_control_center_efs_sg = ec2.SecurityGroup(self, f"{customer_name}OptimalControlCenterEFSSG",
            vpc=vpc,
            security_group_name=f'{customer_name} Control Center EFS SG',
            description=f'{customer_name} Control Center EFS Security Group.',
            allow_all_outbound=True,
        )

    #ingress rule creation
        customer_control_center_efs_sg.add_ingress_rule(
            peer=customer_sg,
            connection=ec2.Port.tcp(2049),
            description=f"Allow NFS from {customer_name} control center sg",
        )
        customer_control_center_efs_sg.add_ingress_rule(
            peer=customer_control_center_init_helper_sg,
            connection=ec2.Port.tcp(2049),
            description=f"Allow NFS from {customer_name} init helper sg",
        )
        customer_control_center_efs_sg.add_ingress_rule(
            peer=ec2.SecurityGroup.from_security_group_id(
            self, "ExistingSG",
            security_group_id=maint_host_sg
            ),
            connection=ec2.Port.tcp(2049),
            description=f"Allow NFS from maintenance host sg",
        )
        customer_sg.add_ingress_rule(
            peer=ec2.SecurityGroup.from_security_group_id(
            self, "customer_load_balancer_sg_id",
            security_group_id=customer_load_balancer_sg_id
            ),
            connection=ec2.Port.tcp(8043),
            description=f"Allow HTTPS from customer_control_center_load_balancer sg",
        )
# ....................................................       
# Fargate IAM
# ....................................................

        customer_control_center_role = iam.Role(
            self,
            f'{customer_name}_control_center_role',
            role_name=f'{customer_name}_control_center_role',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        )
        customer_control_center_role.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        
        customer_control_center_policy_document_json = {
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
                        f'arn:aws:logs:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:log-group:/optimal/customer_control_center:*'
                    ]
                },
            ]
        }
        
        customer_control_center_policy_document = iam.PolicyDocument.from_json(customer_control_center_policy_document_json)
        iam.ManagedPolicy(
            self,
            f'{customer_name}_control_center_policy_doc',
            managed_policy_name=f'{customer_name}_control_center_policy',
            document=customer_control_center_policy_document,
            roles=[customer_control_center_role],
        )
       #### Need to create a side car container that will monitor, build and ship a new ignition container when a new gwbk file is stored in the efs location 
# ....................................................       
# Customer ECS FARGATAE Service
# ....................................................
        # Create an EFS file system
        customer_control_center_efs_data_file_system = efs.FileSystem(self, f"{customer_name}ControlCenterEfsDataFileSystem",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=customer_subnets,
            ),
            security_group=customer_control_center_efs_sg
        )
# Define the EFS volume
        customer_control_center_efs_data_volume = ecs.Volume(name=f"{customer_name}_control_center_efs_data_volume", efs_volume_configuration=ecs.EfsVolumeConfiguration(
            file_system_id=customer_control_center_efs_data_file_system.file_system_id,
            root_directory="/",
            )
        )
        customer_control_center_efs_data_file_system.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        # Create a Fargate task definition
        customer_control_center_task_definition = ecs.FargateTaskDefinition(self, f'{customer_name}_control_center_task_definition',
            memory_limit_mib=memory_limit_mib,
            cpu=cpu,
            family=f'{customer_name}-control-center',
            task_role=customer_control_center_role,
            volumes=[customer_control_center_efs_data_volume]
        )
        
        optimal_control_center_log_group = logs.LogGroup(self, f'{customer_name}_control_center_log_group', log_group_name=f'/optimal/customer_control_center/{customer_name}', removal_policy=cdk.RemovalPolicy.DESTROY, retention=logs.RetentionDays.ONE_YEAR)

        customer_control_center_service_container = customer_control_center_task_definition.add_container(f'{customer_name}_control_center_service',
            container_name=f'{customer_name}_control_center',
            command=[f"docker-entrypoint.sh -r /usr/local/bin/ignition/data/{dep_env_prefix}{customer_name}.gwbk"],
            entry_point=["sh","-c"],
            image=ecs.ContainerImage.from_registry("inductiveautomation/ignition:8.1.36"),
            memory_limit_mib=memory_limit_mib,
            environment={
                "ACCEPT_IGNITION_EULA": "Y",
                "DISABLE_QUICKSTART": "true",
                #"CONTROL_CENTER_RESTORE_FILE_NAME": f"{customer_name}.gwbk",
                "GATEWAY_NETWORK_#_HOST": f"{dep_env_prefix}controlcenter.optimal.local",
                "GATEWAY_NETWORK_#_PORT": "8060",
                "GATEWAY_SYSTEM_NAME": f"{customer_name}",
                "GATEWAY_MODULES_ENABLED": "perspective,tag-historian,opc-ua,modbus-driver-v2,vision,sql-bridge,opc-ua,symbol-factory",
                "IGNITION_EDITION": "standard",
                "TZ": "America/Chicago"
            },
            logging=ecs.LogDriver.aws_logs(stream_prefix=f'/{customer_name}-control-center-task', log_group=optimal_control_center_log_group),
            #port_mappings=[ecs.PortMapping(container_port=8043), ecs.PortMapping(container_port=8088)],
            port_mappings=[ecs.PortMapping(container_port=8043)],
            stop_timeout=Duration.seconds(10)
        )
        # I am not convinced this logic was needed but at one point i had one ecs task mapping all efs paritions... 
        if customer_name == customer_name and customer_name in customer_control_center_efs_data_volume.name:
            customer_control_center_service_container.add_mount_points(
                ecs.MountPoint(
                    container_path="/usr/local/bin/ignition/data",
                    source_volume=f"{customer_name}_control_center_efs_data_volume",
                    read_only=False
                )
            )
            
        # create usable security group for cluster
        security_group_usable = ec2.SecurityGroup.from_security_group_id(
            self, "ImportedSG",
            security_group_id=security_group
        )
            
        cluster_imported = ecs.Cluster.from_cluster_attributes(
            self, "ImportedCluster",
            cluster_name=cluster_name,
            vpc=vpc,
            security_groups=[security_group_usable, customer_sg]
        )

        namespace = sd.PrivateDnsNamespace.from_private_dns_namespace_attributes(
            self, "ImportedNamespace",
            namespace_name='optimal.local',
            namespace_id=private_dns_namespace,  # The Cloud Map namespace ID
            namespace_arn=private_dns_namespace_arn  # Optional
        ) 

        customer_control_center_service = ecs.FargateService(self, f'{customer_name}_control_center_service', 
            assign_public_ip=True,
            desired_count=1, 
            cloud_map_options=ecs.CloudMapOptions(
                cloud_map_namespace=namespace,
                name=f"{customer_name}"
            ),
            cluster=cluster_imported,
            security_groups=[security_group_usable, customer_sg],
            service_name=f"{customer_name}",  # This will be the name in the service discovery
            task_definition=customer_control_center_task_definition,
            vpc_subnets=ec2.SubnetSelection(
                subnets=customer_subnets,
            ),
        )
        customer_control_center_service.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        # Add tags to the ECS service
        # cdk.Tags.of(customer_control_center_service).add("Environment", DEPLOYMENT_ENVIRONMENT)
        # cdk.Tags.of(customer_control_center_service).add("cost_center", customer_name)
        
        customer_control_center_service_health_check = elbv2.HealthCheck(path='/', healthy_http_codes='200,302', unhealthy_threshold_count=2)

        customer_control_center_service_target_group = elbv2.ApplicationTargetGroup(self, f'{customer_name}_control_center_tg',
            target_group_name=f'{customer_name}-control-center-tg',
            target_type=elbv2.TargetType.IP,
            protocol=elbv2.ApplicationProtocol.HTTPS,
            port=443,
            health_check=customer_control_center_service_health_check,
            vpc=vpc
        )

        rule = elbv2.CfnListenerRule(self, "MyListenerRule",
            actions=[{
                "type": "forward",
                "targetGroupArn": customer_control_center_service_target_group.target_group_arn  # Ensure you have a target group ARN
            }],
            conditions=[{
                "field": "host-header",
                "values": [f'{dep_env_prefix}{customer_name}.optimalpipeline.io']
            }],
            listener_arn=listener,
            priority=priority
        )
        
        customer_control_center_service_target_group.add_target(customer_control_center_service)
        
##################################
# Control Center Init Container
##################################
        customer_control_center_init_role = iam.Role(
            self,
            f'{customer_name}_control_center_init_role',
            role_name=f'{customer_name}_control_center_init_role',
            assumed_by=iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
        )
        customer_control_center_init_role.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        
        customer_control_center_init_policy_document_json = {
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
                            f"arn:aws:s3:::{dep_env_prefix}{customer_name}-control-center-restore-files-bucket/*",
                            f"arn:aws:s3:::{dep_env_prefix}control-center-init-file-bucket/*"
                    ]
                }
            ]
        }
        
        customer_control_center_init_policy_document = iam.PolicyDocument.from_json(customer_control_center_init_policy_document_json)
        iam.ManagedPolicy(
            self,
            f'{customer_name}_control_center_init_policy_doc',
            managed_policy_name=f'{customer_name}_optimal_control_center_init_policy',
            document=customer_control_center_init_policy_document,
            roles=[customer_control_center_init_role],
        )
   # Create a Fargate task definition
        customer_control_center_init_task_definition = ecs.FargateTaskDefinition(self, f'{customer_name}_control_center_init_task_definition',
            memory_limit_mib=512,
            cpu=256,
            family=f'{customer_name}_control_center_init_task',
            task_role=customer_control_center_init_role,
            volumes=[customer_control_center_efs_data_volume]
        )
        
        customer_control_center_init_log_group = logs.LogGroup(self, f'{customer_name}_control_center_init_log_group', log_group_name=f'/optimal/{customer_name}_control-center_init/', removal_policy=cdk.RemovalPolicy.DESTROY, retention=logs.RetentionDays.ONE_YEAR)

        customer_control_center_init_repository = ecr.Repository.from_repository_attributes(self, f'{dep_env_prefix}optimal_control_center_init_repository',
            repository_name=f'{dep_env_prefix}optimal_control_center_init_data_helper',
            repository_arn=f'arn:aws:ecr:{DEFAULT_REGION}:{DEFAULT_ACCOUNT}:repository/{dep_env_prefix}optimal_control_center_init_data_helper',
        )
        customer_control_center_init_service_container = customer_control_center_init_task_definition.add_container(f'{customer_name}_control_center_init_service',
            container_name=f'{customer_name}_control_center_init',
            image=ecs.ContainerImage.from_ecr_repository(customer_control_center_init_repository, tag='latest'),
            memory_limit_mib=512,
            #essential=False,
            environment={
                    "CONTROL_CENTER_RESTORE_FILE_NAME": f"{dep_env_prefix}{customer_name}.gwbk",
                    "S3_INIT_BUCKET": f"{dep_env_prefix}control-center-init-file-bucket",
                    "S3_RESTORE_BUCKET": f"{dep_env_prefix}{customer_name}-control-center-restore-files-bucket",
                    "EFS_MOUNT_POINT": "/mnt/efs",
                },
            logging=ecs.LogDriver.aws_logs(stream_prefix=f'/{customer_name}_control_center_init', log_group=customer_control_center_init_log_group),
            stop_timeout=Duration.seconds(10)
        )

        # Mount the EFS file system to the container
        print (f"{customer_name}")
        print (f"{customer_name}{customer_control_center_efs_data_volume.name}")
        if customer_name in customer_control_center_efs_data_volume.name:
            customer_control_center_init_service_container.add_mount_points(
                ecs.MountPoint(
                    container_path="/mnt/efs",
                    source_volume=f"{customer_name}_control_center_efs_data_volume",
                    read_only=False
                )
            )
        
        customer_control_center_init_service = ecs.FargateService(self, f'{customer_name}_control_center_init_service', 
            cluster=cluster_imported,
            assign_public_ip=True,
            task_definition=customer_control_center_init_task_definition,
            service_name=f'{customer_name}_control_center_init',
            desired_count=1, 
            security_groups=[customer_control_center_init_helper_sg],
            vpc_subnets=ec2.SubnetSelection(
                subnets=customer_subnets,
            ),
        )
        customer_control_center_init_service.apply_removal_policy(cdk.RemovalPolicy.DESTROY)
        

# ....................................................       
# Create customer_control_center_init_lambda
# ....................................................  
# had to move to private subnet and also create an s3 gateway endpoint for this to hit s3
        customer_control_center_gwbk_lambda_role = iam.Role(
            self,
            f'{customer_name}_control_center_gwbk_lambda_role',
            role_name=f'{customer_name}_control_center_gwbk_lambda_role',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
        )
        customer_control_center_gwbk_lambda_role.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        customer_control_center_gwbk_lambda_policy_document_json = {
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
        
        customer_control_center_gwbk_lambda_policy_document = iam.PolicyDocument.from_json(customer_control_center_gwbk_lambda_policy_document_json)
        iam.ManagedPolicy(
            self,
            f'{customer_name}_control_center_init_lambda_policy_doc',
            managed_policy_name=f'{customer_name}_control_center_gwbk_lambda_policy',
            document=customer_control_center_gwbk_lambda_policy_document,
            roles=[customer_control_center_gwbk_lambda_role],
        )

        # Attach a policy to the role to allow Lambda to mount EFS
        customer_control_center_gwbk_lambda_efs_mount_policy = iam.Policy(
            self, f"{customer_name}_control_center_gwbk_lambda_efs_mount_policy",
            statements=[
                iam.PolicyStatement(
                    actions=["elasticfilesystem:ClientMount"],
                    resources=[customer_control_center_efs_data_file_system.file_system_arn],
                ),
                iam.PolicyStatement(
                    actions=["*"],
                    resources=["*"],
                )
            ],
            roles=[customer_control_center_gwbk_lambda_role]
        )
        access_point = customer_control_center_efs_data_file_system.add_access_point(
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
        customer_control_panel_gwbk_s3_copy_lambda = _lambda.Function(
            self, f"{customer_name}_control_panel_gwbk_s3_copy_lambda",
            description=f"{customer_name} lambda to copy new gwbk from s3 to efs when a new gwbk is copied to s3.",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            function_name=f"{customer_name}_control_panel_gwbk_s3_copy_lambda",
            log_retention=logs.RetentionDays.ONE_MONTH,
            code=_lambda.Code.from_asset("customer_infrastructure/optimal_customers/restore_file_lambda/"),  # Place your Lambda code in a 'control_center_init_lambda' directory
            environment={
                'CUSTOMER_NAME': customer_name,
                'CONTROL_CENTER_RESTORE_FILE_NAME': f'{dep_env_prefix}{customer_name}.gwbk',
                'GWBK_RESTORE_BUCKET': f'{dep_env_prefix}{customer_name}-control-center-restore-files-bucket'
            },
            role=customer_control_center_gwbk_lambda_role,
            timeout=Duration.seconds(30),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=lambda_subnets,
            ),
            filesystem=_lambda.FileSystem.from_efs_access_point(
                ap=access_point,
                mount_path="/mnt/efs"
            )
        )

        # # Grant Lambda the necessary permissions to the EFS
        customer_control_center_efs_data_file_system.grant(customer_control_panel_gwbk_s3_copy_lambda, "elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite")
        customer_control_panel_gwbk_s3_copy_lambda.add_event_source(lambda_event_sources.S3EventSource(
            control_center_restore_files_bucket,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[s3.NotificationKeyFilter(suffix=f"{customer_name}.gwbk")]
        ))
        customer_control_panel_gwbk_s3_copy_lambda.add_event_source(lambda_event_sources.S3EventSource(
            control_center_restore_files_bucket,
            events=[s3.EventType.OBJECT_CREATED],
            filters=[s3.NotificationKeyFilter(suffix=f"ssl.pfx")]
        ))
        
##################################
# Add the tags to the Fargate services and EFS file system
##################################
        for key, value in tags.items():
            cdk.Tags.of(customer_control_center_init_service).add(key, value)
            cdk.Tags.of(customer_control_center_service).add(key, value)
            cdk.Tags.of(customer_control_center_efs_data_file_system).add(key, value)
            cdk.Tags.of(customer_control_center_init_service_container).add(key, value)