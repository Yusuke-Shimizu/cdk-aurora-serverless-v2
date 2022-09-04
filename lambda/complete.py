import json
import boto3

client = boto3.client('rds')

def handler(event, context):
    print(event)
    physical_id = event["PhysicalResourceId"]
    request_type = event["RequestType"]

    props = event["ResourceProperties"]
    db_cluster_name = props['DBClusterIdentifier']
    response = client.describe_db_clusters(
        DBClusterIdentifier=db_cluster_name,
    )
    cluster_name = response['DBClusters'][0]['DBClusterIdentifier']
    cluster_status = response['DBClusters'][0]['Status']
    cluster_engine = response['DBClusters'][0]['EngineVersion']
    print('describe_db_clusters')
    print(response)
    print(cluster_name + ' : ' + cluster_status + ', ' + cluster_engine)
    is_ready = False
    if cluster_status == 'available' and cluster_engine == '8.0.mysql_aurora.3.02.0':
        is_ready = True
    
    # check if resource is stable based on request_type
    
    return { 'IsComplete': is_ready }
