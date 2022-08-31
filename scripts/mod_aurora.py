import boto3
import pprint
import datetime
import time

client = boto3.client('rds', region_name='ap-northeast-1')
instance_status = True
# db_cluster_name = 'y3-shimizu-senju-db'
db_cluster_name = 'y3-shimizu-cdk-aurora'
db_instance_name = db_cluster_name + 'instance1'

client_lambda = boto3.client('lambda', region_name='ap-northeast-1')
function_name = "y3-shimizu_cluster_verup"

waiter = client.get_waiter('db_cluster_available')
waiter.wait(
    DBClusterIdentifier='y3-shimizu-test',
)

print('--- Start ---')
while instance_status:
    now = datetime.datetime.now()
    print(now)
    
    try:
        response = client.describe_db_clusters(
            DBClusterIdentifier=db_cluster_name,
        )
        cluster_name = response['DBClusters'][0]['DBClusterIdentifier']
        cluster_status = response['DBClusters'][0]['Status']
        cluster_engine = response['DBClusters'][0]['EngineVersion']
        pprint.pprint(cluster_name + ' : ' + cluster_status + ', ' + cluster_engine)
    except:
        print('no cluster')
    
    try:
        response = client.describe_db_instances(
            DBInstanceIdentifier=db_instance_name,
        )
        db_name = response['DBInstances'][0]['DBInstanceIdentifier']
        db_status = response['DBInstances'][0]['DBInstanceStatus']
        db_class = response['DBInstances'][0]['DBInstanceClass']
        pprint.pprint(db_name + ' : ' + db_status + ', ' + db_class)
        # if db_status == 'available':
        #     instance_status = False
    except:
        print('no instance')
    

    try:
        response = client.get_function(
            FunctionName=function_name,
        )
        pprint.pprint(response)
    except:
        print('no function')


    print('---')
    time.sleep(10)

print('--- End ---')
