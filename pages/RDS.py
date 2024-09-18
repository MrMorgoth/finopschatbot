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
ses_client = boto3.client(
    'ses',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
    )  # Or ses_client if using SES


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
        master_username = instance['MasterUsername']
        
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
            inactive_instances.append((db_instance_id, master_username))
    
    return inactive_instances

# Function to tag the instance for deletion
def tag_instance_for_deletion(db_instance_id):
    # Tag the instance as "for_deletion"
    rds_client.add_tags_to_resource(
        ResourceName=f'arn:aws:rds:region:account-id:db:{db_instance_id}',  # Replace with actual region/account
        Tags=[
            {
                'Key': 'for_deletion',
                'Value': 'true'
            }
        ]
    )
    print(f"Instance {db_instance_id} tagged for deletion.")
    
# Function to notify the DB creator
def notify_db_creator(db_instance_id, master_username, notification_email):
    # Message to notify the user of the impending deletion
    subject = f"RDS Instance {db_instance_id} Scheduled for Deletion"
    message = f"""
    Dear {master_username},

    Your RDS instance '{db_instance_id}' has not had any connections in the past 30 days.
    It is has been tagged and scheduled for deletion in 7 days unless you remove the tag.

    If you wish to keep this instance, please ensure the tag is removed before the deletion date.
    """

    # Alternatively, if using SES:
    ses_client.send_email(
        Source='your-email@example.com',  # Replace with an SES verified email.
        Destination={'ToAddresses': [notification_email]},
        Message={
        'Subject': {'Data': subject},
        'Body': {'Text': {'Data': message}}
        }
    )

# Streamlit UI
st.title('Inactive RDS Instances Finder')

# Button to find inactive RDS instances
if st.button('Find Inactive RDS Instances'):
    with st.spinner('Fetching inactive instances...'):
        inactive_instances = find_inactive_rds_instances()
    
    if inactive_instances:
        st.success(f'Found {len(inactive_instances)} inactive instances:')
        for db_instance_id, master_username in inactive_instances:
            st.write(f"DB Instance: {db_instance_id}, Master Username: {master_username}")
            
            # Fetch the notification email from tags or provide manually
            # For demo purposes, assume email is stored in tags (replace with real logic)
            db_tags = rds_client.list_tags_for_resource(ResourceName=f'arn:aws:rds:region:account-id:db:{db_instance_id}')
            notification_email = None
            for tag in db_tags['TagList']:
                if tag['Key'] == 'CreatorEmail':
                    notification_email = tag['Value']
            
            if notification_email:
                notify_db_creator(db_instance_id, master_username, notification_email)
                st.write(f'Notification sent to {notification_email}')
            else:
                st.write(f'No notification email found for {db_instance_id}')
    else:
        st.info('No inactive instances found.')
