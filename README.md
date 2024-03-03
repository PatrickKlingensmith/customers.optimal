# infrastructure.optimal
Infrastructure needed for basic operation written in python for AWS CDK

you must set env var AWS_DEFAULT_REGION to the desired region or cdk will ignore all other env vars and reset it to us-east-1.

## FILES

* /optimal_infrastructure/optimal_control_center_init_files/data.zip
This file contains the basic files needed to populate the data folder in the container. The init task prepopulates the EFS mount data folder with the contents of this file if it has not been executed before.


**NOTE** I had to manually add the default route to the NAT Gateway in the lambda subnets because CDK would hang after successfully deploying and wait for about an hour and then abort and roll back.

