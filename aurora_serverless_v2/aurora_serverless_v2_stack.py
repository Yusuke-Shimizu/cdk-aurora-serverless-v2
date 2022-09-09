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

        instance_count = 1

        cluster = rds.DatabaseCluster(self, "AuroraCluster",
            cluster_identifier='y3-shimizu-cdk-aurora',
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0),
            instances=instance_count,
            instance_props=rds.InstanceProps(
                vpc=vpc,
            ),
            credentials=aurora_cluster_credentials,
        )
        
        # クラスタバージョンアップ
        on_event = lambda_.Function(self, "VerUpFunction",
            function_name='y3-shimizu_cluster_verup',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="verup.handler",
            code=lambda_.Code.from_asset('lambda'),
        )
        lambda_policy = iam.PolicyStatement(
            resources=["*"],
            actions=[
                "rds:*",
            ]
        )
        on_event.add_to_role_policy(lambda_policy)
        is_complete = lambda_.Function(self, "CheckComplete",
            function_name='y3-shimizu_cluster_check_available',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="complete.handler",
            code=lambda_.Code.from_asset('lambda'),
        )
        is_complete.add_to_role_policy(lambda_policy)
        
        my_provider = cr.Provider(self, "MyProvider",
            on_event_handler=on_event,
            is_complete_handler=is_complete,  # optional async "waiter"
            provider_function_name="y3-shimizu_cluster_verup_provider",
        )
        version_up=CustomResource(self, "VerUpCustomResource", 
            service_token=my_provider.service_token,
            properties={
                "DBClusterIdentifier": cluster.cluster_identifier,
                "DBEngineVersion": "8.0.mysql_aurora.3.02.0"
            },
        )
        for i in range(1, instance_count + 1):
            version_up.node.add_dependency(cluster.node.find_child(f"Instance{i}"))

        # サーバレス用の設定を追加
        mod_cap_cluster_serverless = cr.AwsSdkCall(
            service="RDS",
            action="modifyDBCluster",
            parameters={
                "DBClusterIdentifier": cluster.cluster_identifier,
                "ApplyImmediately": True,
                "ServerlessV2ScalingConfiguration": {
                    "MinCapacity": 0.5,
                    "MaxCapacity": 1,
                },
            },
            physical_resource_id=cr.PhysicalResourceId.of(
                cluster.cluster_identifier
            ),
        )
        add_cap = cr.AwsCustomResource(self, "VersionUp",
            on_create=mod_cap_cluster_serverless,
            on_update=mod_cap_cluster_serverless,
            policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,
            ),
        )
        add_cap.node.add_dependency(version_up)
        
        # インスタンスタイプをServerlessに変更
        for i in range(instance_count):
            instance_name = cluster.instance_identifiers[i]
            
            mod_type_serverless = cr.AwsSdkCall(
                service="RDS",
                action="modifyDBInstance",
                parameters={
                    "DBInstanceIdentifier": instance_name,
                    "DBInstanceClass": "db.serverless",
                    "ApplyImmediately": True
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    instance_name
                ),
            )
            mod_type_provisioned = cr.AwsSdkCall(
                service="RDS",
                action="modifyDBInstance",
                parameters={
                    "DBInstanceIdentifier": instance_name,
                    "DBInstanceClass": "db.t3.medium",
                    "ApplyImmediately": True
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    instance_name
                ),
            )
            modify_instance_type = cr.AwsCustomResource(self, "ModType",
                function_name='y3-shimizu-modify-instance',
                on_create=mod_type_serverless,
                on_update=mod_type_serverless,
                on_delete=mod_type_provisioned,
                policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
                    resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,
                ),
            )
            modify_instance_type.node.add_dependency(add_cap)
