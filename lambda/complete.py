import json
import boto3

client = boto3.client('rds')

def handler(event, context):
    print(event)
    request_type = event['RequestType']
    if request_type == 'Create': return on_create(event)
    if request_type == 'Update': return on_update(event)
    if request_type == 'Delete': return on_delete(event)
    raise Exception("Invalid request type: %s" % request_type)


def on_create(event):
    props = event["ResourceProperties"]
    return check_cluster_status(props)
    
def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("update resource %s with props %s" % (physical_id, props))

    return check_cluster_status(props)

def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    print("delete resource %s" % physical_id)
    return { 'IsComplete': True }

def check_cluster_status(props):
    db_cluster_name = props['DBClusterIdentifier']
    db_engine_version = props['DBEngineVersion']
    print(db_cluster_name + " : " + db_engine_version)

    response = client.describe_db_clusters(
        DBClusterIdentifier=db_cluster_name,
    )
    db_cluster = response['DBClusters'][0]
    cluster_name = db_cluster['DBClusterIdentifier']
    cluster_status = db_cluster['Status']
    cluster_engine = db_cluster['EngineVersion']
    print('describe_db_clusters')
    print(response)
    print(cluster_name + ' : ' + cluster_status + ', ' + cluster_engine)
    
    is_ready = False
    if cluster_status == 'available' and cluster_engine == db_engine_version:
        is_ready = True

    return { 'IsComplete': is_ready }
