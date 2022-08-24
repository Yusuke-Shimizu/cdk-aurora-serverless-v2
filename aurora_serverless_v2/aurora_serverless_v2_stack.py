from aws_cdk import (
    Stack,
    CfnOutput,
    Environment,
    Tags,
    Duration,
    custom_resources as cr,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    aws_kms as kms,
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

        secret = rds.DatabaseSecret(self, "AuroraSecret", username=db_user)

        aurora_cluster_credentials = rds.Credentials.from_secret(secret, db_user)

        kms_key = kms.Key(
            self, "AuroraDatabaseKey", enable_key_rotation=True, alias=_id
        )

        # parameter_group = rds.ParameterGroup.from_parameter_group_name(
        #     self, "ParameterGroup", "default.aurora-postgresql14"
        # )

        instance_count = 1

        cluster = rds.DatabaseCluster(self, "AuroraCluster",
            engine=rds.DatabaseClusterEngine.aurora_mysql(version=rds.AuroraMysqlEngineVersion.VER_3_01_0),
            # cluster_identifier=_id,
            instances=instance_count,
            instance_props=rds.InstanceProps(
                vpc=vpc,
                # instance_type=ec2.InstanceType("serverless"),
                # auto_minor_version_upgrade=True,
                # allow_major_version_upgrade=False,
                # publicly_accessible=True,
            ),
            # engine=rds.DatabaseClusterEngine.AURORA_POSTGRESQL,
            # engine_version="14.3",
            # parameter_group=parameter_group,
            credentials=aurora_cluster_credentials,
            # default_database_name=db_name,
            # backup=rds.BackupProps(
            #     retention=Duration.days(14),
            # ),
        )

        # parameters = {
        #     "DBClusterIdentifier": cluster.cluster_identifier,
        #     "ServerlessV2ScalingConfiguration": {
        #         "MinCapacity": 0.5,
        #         "MaxCapacity": 8,
        #     },
        # }

        # scaling = cr.AwsCustomResource(
        #     self,
        #     "Scaling",
        #     on_create=cr.AwsSdkCall(
        #         service="RDS",
        #         action="modifyDBCluster",
        #         parameters=parameters,
        #         physical_resource_id=cr.PhysicalResourceId.of(
        #             cluster.cluster_identifier
        #         ),
        #     ),
        #     on_update=cr.AwsSdkCall(
        #         service="RDS",
        #         action="modifyDBCluster",
        #         parameters=parameters,
        #         physical_resource_id=cr.PhysicalResourceId.of(
        #             cluster.cluster_identifier
        #         ),
        #     ),
        #     policy=cr.AwsCustomResourcePolicy.from_sdk_calls(
        #         resources=cr.AwsCustomResourcePolicy.ANY_RESOURCE,
        #     ),
        # )

        # cfnCluster = cluster.node.default_child

        # target = scaling.node.find_child("Resource").node.default_child

        # cfnCluster.add_property_override("EngineMode", "provisioned")
        # scaling.node.add_dependency(cfnCluster)

        # for i in range(1, instance_count + 1):
        #     cluster.node.find_child(f"Instance{i}").add_depends_on(target)
