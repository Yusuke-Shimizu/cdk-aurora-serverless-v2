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
    print("create new resource with props %s" % props)
    db_cluster_name = props['DBClusterIdentifier']
    
    # add your create code here...
    physical_id = 'id'
    response = client.modify_db_cluster(
        DBClusterIdentifier=db_cluster_name,
        ApplyImmediately=True,
        EngineVersion="8.0.mysql_aurora.3.02.0",
    )
    print('modify_db_cluster')
    print(response)
    
    waiter = client.get_waiter('db_cluster_available')
    waiter.wait(
        DBClusterIdentifier=db_cluster_name,
    )
    
    return { 'PhysicalResourceId': physical_id }

def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("update resource %s with props %s" % (physical_id, props))
    # ...

def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    print("delete resource %s" % physical_id)
