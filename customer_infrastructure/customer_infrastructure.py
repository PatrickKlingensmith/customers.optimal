import aws_cdk as cdk
from aws_cdk import (
    aws_ec2 as ec2,
    #aws_ssm as ssm,
    App, 
    Stack
)
import os
import boto3
# Create a session using AWS credentials and configuration
session = boto3.Session()
# Create an SSM client from the session
ssm = session.client('ssm')

#from optimal_infrastructure.optimal_control_center.optimal_control_center_stack import OptimalControlCenterStack
from customer_infrastructure.optimal_customers.customer_stack.customer_stack import CustomerStack

vpc_id_parameter_name = "/infrastructure/optimal_vpc_id"
response = ssm.get_parameter(Name=vpc_id_parameter_name, WithDecryption=True)
vpc_id = response['Parameter']['Value']
print(vpc_id)
      
customer_subnet_a_parameter_name = "/infrastructure/customer_subnet_a_id"
response = ssm.get_parameter(Name=customer_subnet_a_parameter_name, WithDecryption=True)
customer_subnet_a_id = response['Parameter']['Value']
print(customer_subnet_a_id)

customer_subnet_b_parameter_name = "/infrastructure/customer_subnet_b_id"
response = ssm.get_parameter(Name=customer_subnet_b_parameter_name, WithDecryption=True)
customer_subnet_b_id = response['Parameter']['Value']
print(customer_subnet_b_id)

customer_subnet_c_parameter_name = "/infrastructure/customer_subnet_c_id"
response = ssm.get_parameter(Name=customer_subnet_c_parameter_name, WithDecryption=True)
customer_subnet_c_id = response['Parameter']['Value']
print(customer_subnet_c_id)

lambda_subnet_a_parameter_name = "/infrastructure/lambda_subnet_a_id"
response = ssm.get_parameter(Name=lambda_subnet_a_parameter_name, WithDecryption=True)
lambda_subnet_a_id = response['Parameter']['Value']
print(lambda_subnet_a_id)

lambda_subnet_b_parameter_name = "/infrastructure/lambda_subnet_b_id"
response = ssm.get_parameter(Name=lambda_subnet_b_parameter_name, WithDecryption=True)
lambda_subnet_b_id = response['Parameter']['Value']
print(lambda_subnet_b_id)

customer_general_sg_parameter_name = "/infrastructure/Optimal_General_Customer_sg_id"
response = ssm.get_parameter(Name=customer_general_sg_parameter_name, WithDecryption=True)
customer_general_sg_id = response['Parameter']['Value']
print(customer_general_sg_id)

private_dns_namespace_id_parameter_name = "/infrastructure/private_dns_namespace_id"
response = ssm.get_parameter(Name=private_dns_namespace_id_parameter_name, WithDecryption=True)
private_dns_namespace_id = response['Parameter']['Value']
print(private_dns_namespace_id)

private_dns_namespace_arn_parameter_name = "/infrastructure/private_dns_namespace_arn"
response = ssm.get_parameter(Name=private_dns_namespace_arn_parameter_name, WithDecryption=True)
private_dns_namespace_arn = response['Parameter']['Value']
print(private_dns_namespace_arn)

optimal_control_center_maintenance_host_sg_id_parameter_name = "/infrastructure/optimal_control_center_maintenance_host_sg_id"
response = ssm.get_parameter(Name=optimal_control_center_maintenance_host_sg_id_parameter_name, WithDecryption=True)
optimal_control_center_maintenance_host_sg_id = response['Parameter']['Value']
print(optimal_control_center_maintenance_host_sg_id)

customer_control_center_443_listener_arn_parameter_name = "/infrastructure/customer_control_center_443_listener_arn"
response = ssm.get_parameter(Name=customer_control_center_443_listener_arn_parameter_name, WithDecryption=True)
customer_control_center_443_listener_arn = response['Parameter']['Value']
print(customer_control_center_443_listener_arn)

customer_control_center_fargate_cluster_name_parameter_name = "/infrastructure/customer_control_center_fargate_cluster_name"
response = ssm.get_parameter(Name=customer_control_center_fargate_cluster_name_parameter_name, WithDecryption=True)
customer_control_center_fargate_cluster_name = response['Parameter']['Value']
print(customer_control_center_fargate_cluster_name)

customer_control_center_fargate_cluster_arn_parameter_name = "/infrastructure/customer_control_center_fargate_cluster_arn"
response = ssm.get_parameter(Name=customer_control_center_fargate_cluster_arn_parameter_name, WithDecryption=True)
customer_control_center_fargate_cluster_arn = response['Parameter']['Value']
print(customer_control_center_fargate_cluster_arn)

customer_load_balancer_sg_id_name = "/infrastructure/customer_load_balancer_sg_id"
response = ssm.get_parameter(Name=customer_load_balancer_sg_id_name, WithDecryption=True)
customer_load_balancer_sg_id = response['Parameter']['Value']
print(customer_load_balancer_sg_id)




DEPLOYMENT_ENVIRONMENT = os.environ['DEPLOYMENT_ENVIRONMENT']

class OptimalStack(Stack):

    def __init__(self, scope: App, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        vpc = ec2.Vpc.from_lookup(self, "ExistingOptimalVPC", vpc_id=vpc_id)
        
        # vpc_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/optimal_vpc_id")
        # print(f'vpc_id: {vpc_id}')
        
        # customer_subnet_a_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/customer_subnet_a_id")
        # print(f'customer_subnet_a_id: {customer_subnet_a_id}')
        
        # customer_subnet_b_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/customer_subnet_b_id")
        # print(f'customer_subnet_b_id: {customer_subnet_b_id}')
        
        # customer_subnet_c_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/customer_subnet_c_id")
        # print(f'customer_subnet_c_id: {customer_subnet_c_id}')
        
        # lambda_subnet_a_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/lambda_subnet_a_id")
        # print(f'lambda_subnet_a_id: {lambda_subnet_a_id}')
          
        # lambda_subnet_b_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/lambda_subnet_b_id")
        # print(f'lambda_subnet_b_id: {lambda_subnet_b_id}')
                  
        # private_dns_namespace_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/private_dns_namespace_id")
        # print(f'private_dns_namespace_id: {private_dns_namespace_id}')
        
        # general_customer_sg_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/Optimal_General_Customer_sg_id")
        # print(f'general_customer_sg_id: {general_customer_sg_id}')
           
        # optimal_control_center_maintenance_host_sg_id = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/optimal_control_center_maintenance_host_sg_id")
        # print(f'optimal_control_center_maintenance_host_sg_id: {optimal_control_center_maintenance_host_sg_id}')
        
        # customer_control_center_443_listener_arn = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/customer_control_center_443_listener_arn")
        # print(f'customer_control_center_443_listener_arn: {customer_control_center_443_listener_arn}')
                   
        # customer_control_center_fargate_cluster_name = ssm.StringParameter.value_from_lookup(self,
        #     parameter_name="/infrastructure/customer_control_center_fargate_cluster_name")
        # print(f'customer_control_center_fargate_cluster_name: {customer_control_center_fargate_cluster_name}')              
              

        #optimal_stack = OptimalControlCenterStack(self, 'optimal-control-center-stack')
        #To deploy a new base customer control center add the customer name to the array
        #Create a folder with customer name in /optimal_customers/control_center_restore_files/
        #and include the 3 restore files required; uuid, metrokeystore and gwbk files.
        #To delete a customer run cdk destroy OptimalStack/customer4-stack (changing the customer name to match the desired customer to destroy)
        #Then remove the customer name from the name customerNameArray and delete the folder
        priority = 0
        if DEPLOYMENT_ENVIRONMENT == 'sandbox':
            customerNameArray = [ 'customer1', 'customer2' ]
        elif DEPLOYMENT_ENVIRONMENT == 'demo':
            #currently we do not want any customers to deploy to demo so the array is empty
            customerNameArray = [ ]
        elif DEPLOYMENT_ENVIRONMENT == 'production':
            customerNameArray = [ 'customer1', 'customer2' ]
        else:
            print(f'The deployment environment: {DEPLOYMENT_ENVIRONMENT} is invalid for deployment.')
        for customer_name in customerNameArray:
            priority = priority + 1
            CustomerStack(self, f'{customer_name}-stack',
                cluster_name=customer_control_center_fargate_cluster_name,
                cluster_arn=customer_control_center_fargate_cluster_arn,
                customer_name = f'{customer_name}',
                customer_load_balancer_sg_id = customer_load_balancer_sg_id,
                listener=customer_control_center_443_listener_arn,
                maint_host_sg=optimal_control_center_maintenance_host_sg_id,
                private_dns_namespace=private_dns_namespace_id,
                private_dns_namespace_arn=private_dns_namespace_arn,
                priority=priority,
                security_group=customer_general_sg_id, 
                customer_subnet_a_id=customer_subnet_a_id,
                customer_subnet_b_id=customer_subnet_b_id,
                customer_subnet_c_id=customer_subnet_c_id,
                lambda_subnet_a_id=lambda_subnet_a_id,
                lambda_subnet_b_id=lambda_subnet_b_id,
                vpc=vpc
            )
        
        # Tags.of(CustomerStack).add('environment', DEPLOYMENT_ENVIRONMENT)
        # Tags.of(optimal_infrastructure).add('cdkRepo', 'https://github.com/PatrickKlingensmith/infrastructure.optimal')
        # Tags.of(optimal_infrastructure).add('cost_center', 'Optimal_infrastructure')
        # Tags.of(optimal_infrastructure).add('environment', DEPLOYMENT_ENVIRONMENT)