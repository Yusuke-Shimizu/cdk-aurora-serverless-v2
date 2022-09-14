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
    db_instance_name = props['DBInstanceIdentifier']
    # db_engine_version = props['DBEngineVersion']
    print(db_instance_name)

    response = client.describe_db_instances(
        DBInstanceIdentifier=db_instance_name,
    )

    db_instance = response['DBInstances'][0]
    instance_name = db_instance['DBInstanceIdentifier']
    instance_status = db_instance['DBInstanceStatus']
    instance_class = db_instance['DBInstanceClass']
    print('describe_db_clusters')
    print(response)
    print(instance_name + ' : ' + instance_status + ', ' + instance_class)
    
    is_ready = False
    if instance_status == 'available' and instance_class == 'db.serverless':
        is_ready = True

    return { 'IsComplete': is_ready }
