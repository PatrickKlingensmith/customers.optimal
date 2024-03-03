#!/usr/bin/env python3
# IMPORTANT NOTE... YOU MUST export AWS_DEFAULT_REGION for cdk to pick up desired region and keys to work!
import os

import aws_cdk as cdk
from aws_cdk import Tags

from customer_infrastructure.customer_infrastructure import OptimalStack
DEPLOYMENT_ENVIRONMENT = os.environ['DEPLOYMENT_ENVIRONMENT']

app = cdk.App()

optimal_infrastructure = OptimalStack(
      app,
      'OptimalStack',
      env=cdk.Environment(
          account=os.environ['CDK_DEFAULT_ACCOUNT'],
          region=os.environ['CDK_DEFAULT_REGION'],
      )
)

# Tags.of(optimal_infrastructure).add('cdkRepo', 'https://github.com/PatrickKlingensmith/infrastructure.optimal')
# Tags.of(optimal_infrastructure).add('cost_center', 'Optimal_infrastructure')
# Tags.of(optimal_infrastructure).add('environment', DEPLOYMENT_ENVIRONMENT)
app.synth()
