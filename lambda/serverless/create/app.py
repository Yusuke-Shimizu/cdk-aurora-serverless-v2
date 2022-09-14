import json
import boto3
import time

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

    return update_instance(props, 'db.serverless')
    
def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("update resource %s with props %s" % (physical_id, props))

    return update_instance(props, 'db.serverless')

def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("delete resource %s" % physical_id)
    print("update resource %s with props %s" % (physical_id, props))

    return update_instance(props, 'db.t3.medium')

def update_instance(props, instance_class):
    db_instance_name = props['DBInstanceIdentifier']
    print(db_instance_name + ' : ' + instance_class)

    response = client.modify_db_instance(
        DBInstanceIdentifier=db_instance_name,
        DBInstanceClass=instance_class,
        ApplyImmediately=True,
    )
    print('modify_db_instance')
    print(response)

    return { 'PhysicalResourceId': response['DBInstance']['DBInstanceIdentifier'] }
