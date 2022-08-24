#!/usr/bin/env python3

import aws_cdk as cdk

from aurora_serverless_v2.aurora_serverless_v2_stack import AuroraServerlessV2Stack


app = cdk.App()
AuroraServerlessV2Stack(app, "aurora-serverless-v2", stage_name = "hoge")

app.synth()
