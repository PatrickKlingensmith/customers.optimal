# customers.optimal
Customer infrastructure written in python for AWS CDK

You must set env var AWS_DEFAULT_REGION to the desired region or cdk will ignore all other env vars and reset it to us-east-1.

## Deployment
Deploy infrastructure.optimal to desired environment
Run github actions to copy the control center init files to s3
Run github actions to copy control panel restore files to s3
After infrastructure.optimal has completed
Deploy customers.optimal
Run github actions to copy customerN restore files to s3
* Note to ensure the S3 bucket has been created before running the github actions copy restore files workflow
### Final Step
* Copy the control_panel_loadbalancer DNS and update the dns entry in cloudflare
* Copy the customer_controlpanel_loadbalancer DNS and update the DNS entry in cloudflare

## FILES

* /customer_infrastructure/optimal_customers/control_center_restore_files/customerN
The files here are base files needed to start and operate the customer control centers.
The customerN.gwbk files need to be prepended with dep_env_prefix in order to work per environment.


