import boto3
import streamlit as st
from datetime import datetime, timedelta, timezone

# Collect AWS credentials from the user
aws_access_key_id = st.text_input("AWS Access Key ID", type="password")
aws_secret_access_key = st.text_input("AWS Secret Access Key", type="password")
region_name = st.text_input("AWS Region (optional)", "eu-west-2")

# Initialise boto3 clients
rds_client = boto3.client(
    'rds',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name)
cloudwatch_client = boto3.client(
    'cloudwatch',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name)

# Function to find inactive RDS instances
def find_inactive_rds_instances():
    # Get the current time and time from 30 days ago (timezone aware)
    current_time = datetime.now(timezone.utc)
    past_time = current_time - timedelta(days=30)
    
    # Get all RDS instances
    rds_instances = rds_client.describe_db_instances()
    inactive_instances = []
    
    for instance in rds_instances['DBInstances']:
        db_instance_id = instance['DBInstanceIdentifier']
        
        # Get CloudWatch metrics for the DB instance
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='DatabaseConnections',
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': db_instance_id
                },
            ],
            StartTime=past_time,
            EndTime=current_time,
            Period=86400,  # 1 day interval
            Statistics=['Sum']
        )
        
        # Sum of connections over the last 30 days
        total_connections = sum([datapoint['Sum'] for datapoint in response['Datapoints']])
        
        # If there are no connections, add to inactive instances list
        if total_connections == 0:
            inactive_instances.append(db_instance_id)
    
    return inactive_instances

# Streamlit UI
st.title('Inactive RDS Instances Finder')

# Button to find inactive RDS instances
if st.button('Find Inactive RDS Instances'):
    with st.spinner('Fetching inactive instances...'):
        inactive_instances = find_inactive_rds_instances()
    
    if inactive_instances:
        st.success(f'Found {len(inactive_instances)} inactive instances:')
        st.write(inactive_instances)
    else:
        st.info('No inactive instances found.')
