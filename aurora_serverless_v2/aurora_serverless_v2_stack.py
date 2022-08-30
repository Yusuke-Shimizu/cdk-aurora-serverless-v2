from aws_cdk import (
    Stack,
    CfnOutput,
    Environment,
    Tags,
    Duration,
    CustomResource,
    custom_resources as cr,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
    aws_iam as iam,
    aws_lambda as lambda_,
)
from constructs import Construct


class AuroraServerlessV2Stack(Stack):
    def __init__(
        self,
        scope: Construct,
        _id: str,
        # vpc: ec2.IVpc,
        stage_name: str,
        db_user: str="admin",
        db_name: str="mydb",
        **kwargs,
    ) -> None:
        super().__init__(scope, _id, **kwargs)
        
        vpc = ec2.Vpc(self, "VPC")
        
        db_user = "admin"
        secret = rds.DatabaseSecret(self, "AuroraSecret", username=db_user)
        aurora_cluster_credentials = rds.Credentials.from_secret(secret, db_user)

        kms_key = kms.Key(self, "AuroraDatabaseKey", 
            # self, "AuroraDatabaseKey", enable_key_rotation=True, alias=_id
            enable_key_rotation=True
        )

        instance_count = 1

        cluster = rds.DatabaseCluster(self, "AuroraCluster",
            cluster_identifier='y3-shimizu-cdk-aurora',
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0),
            instances=instance_count,
            instance_props=rds.InstanceProps(
                vpc=vpc,
                # instance_type=ec2.InstanceType("serverless"),
            ),
            credentials=aurora_cluster_credentials,
        )
        
        on_event = lambda_.Function(self, "MyFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="verup.handler",
            code=lambda_.Code.from_asset('lambda'),
        )
        my_role = iam.Role(self, "Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="This is a custom role..."
        )
        my_role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=[
                "lambda:*",
                "logs:*",
                "rds:*",
            ]
        ))
        my_provider = cr.Provider(self, "MyProvider",
            on_event_handler=on_event,
            # is_complete_handler=is_complete,  # optional async "waiter"
            # log_retention=logs.RetentionDays.ONE_DAY,  # default is INFINITE
            role=my_role,
            provider_function_name="y3-shimizu_cluster_verup",
        )
        CustomResource(self, "Resource1", 
            service_token=my_provider.service_token,
            properties={
                "DBClusterIdentifier": cluster.cluster_identifier,
            },
        )


        mod_cluster_serverless = cr.AwsSdkCall(
            service="RDS",
            action="modifyDBCluster",
            parameters={
                "DBClusterIdentifier": cluster.cluster_identifier,
                "ApplyImmediately": True,
                "EngineVersion": "8.0.mysql_aurora.3.02.0",
                # "ServerlessV2ScalingConfiguration": {
                #     "MinCapacity": 0.5,
                #     "MaxCapacity": 1,
                # },
            },
            physical_resource_id=cr.PhysicalResourceId.of(
                cluster.cluster_identifier
            ),
        )
        mod_cluster_provisioned = cr.AwsSdkCall(
            service="RDS",
            action="modifyDBCluster",
            parameters={
                "DBClusterIdentifier": cluster.cluster_identifier,
                "ApplyImmediately": True,
                "EngineVersion": "8.0.mysql_aurora.3.01.0",
            },
            physical_resource_id=cr.PhysicalResourceId.of(
                cluster.cluster_identifier
            ),
        )
        version_up = cr.AwsCustomResource(self, "VersionUp",
            on_create=mod_cluster_serverless,
            on_update=mod_cluster_serverless,
            # on_delete=mod_cluster_provisioned,
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,
            ),
        )

        mod_type_serverless = cr.AwsSdkCall(
            service="RDS",
            action="modifyDBInstance",
            parameters={
                "DBInstanceIdentifier": cluster.instance_identifiers[0],
                "DBInstanceClass": "db.serverless",
                "ApplyImmediately": True
            },
            physical_resource_id=cr.PhysicalResourceId.of(
                cluster.instance_identifiers[0]
            ),
        )
        mod_type_provisioned = cr.AwsSdkCall(
            service="RDS",
            action="modifyDBInstance",
            parameters={
                "DBInstanceIdentifier": cluster.instance_identifiers[0],
                "DBInstanceClass": "db.t3.medium",
                "ApplyImmediately": True
            },
            physical_resource_id=cr.PhysicalResourceId.of(
                cluster.instance_identifiers[0]
            ),
        )
        modify_instance_type = cr.AwsCustomResource(self, "ModType",
            on_create=mod_type_serverless,
            on_update=mod_type_serverless,
            on_delete=mod_type_provisioned,
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,
            ),
        )

        cfnCluster = cluster.node.default_child

        target = version_up.node.find_child("Resource").node.default_child
        target_mod_type = modify_instance_type.node.default_child

        # cfnCluster.add_property_override("EngineMode", "provisioned")
        version_up.node.add_dependency(cfnCluster)
        # version_up.node.add_dependency(cluster)
        modify_instance_type.node.add_dependency(target)

        for i in range(1, instance_count + 1):
            # cluster.node.find_child(f"Instance{i}").add_depends_on(target)
            modify_instance_type.node.add_dependency(cluster.node.find_child(f"Instance{i}"))
