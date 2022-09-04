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
# function_name = "y3-shimizu-modify-instance"

print('--- Start ---')
while instance_status:
    now = datetime.datetime.now()
    print(now)
    
    try:
        response = client.describe_db_clusters(
            DBClusterIdentifier=db_cluster_name,
        )
        # pprint.pprint(response)
        cluster_props = response['DBClusters'][0]
        cluster_name = cluster_props['DBClusterIdentifier']
        cluster_status = cluster_props['Status']
        cluster_engine = cluster_props['EngineVersion']
        if 'ServerlessV2ScalingConfiguration' in cluster_props:
            cluster_capacity = response['DBClusters'][0]['ServerlessV2ScalingConfiguration']['MaxCapacity']
            pprint.pprint(cluster_name + ' : ' + cluster_status + ', ' + cluster_engine + ', max cap is ' + str(cluster_capacity))
        else:
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
    
    function_name_list = [
        'y3-shimizu_cluster_verup',
        'y3-shimizu_cluster_check_available',
        "y3-shimizu-modify-instance",
    ]
    
    for function_name in function_name_list:
        try:
            response = client_lambda.get_function(
                FunctionName=function_name,
            )
            pprint.pprint(response['Configuration']['FunctionName'] + " :  " + response['Configuration']['State'])
        except:
            print('no function')


    print('---')
    time.sleep(10)

print('--- End ---')
