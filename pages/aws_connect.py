import streamlit as st
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Connect to AWS Cost Explorer
def get_top_rds_ec2_costs(aws_access_key_id, aws_secret_access_key, region_name):
    try:
        # Create a boto3 client for Cost Explorer
        client = boto3.client(
            'ce',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

        # Define the time period for the past month
        end_date = datetime.now().date()
        start_date = (end_date.replace(day=1) - timedelta(days=1)).replace(day=1)

        # Query AWS Cost Explorer for RDS and EC2 On-Demand costs
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'}
            ],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Relational Database Service', 'Amazon Elastic Compute Cloud - Compute']
                }
            }
        )

        # Check if there are any results
        if not response['ResultsByTime'][0]['Groups']:
            return None, "No costs or instances found for the specified time period."

        # Parse the response to find top 5 RDS and EC2 instances by cost
        cost_data = []
        for result in response['ResultsByTime'][0]['Groups']:
            service = result['Keys'][0]
            instance_type = result['Keys'][1]
            amount = float(result['Metrics']['UnblendedCost']['Amount'])
            cost_data.append([service, instance_type, amount])

        # Create a DataFrame and sort by cost
        df = pd.DataFrame(cost_data, columns=['Service', 'Instance Type', 'Cost'])
        top_5 = df.sort_values(by='Cost', ascending=False).head(5)

        return top_5, None
    
    except NoCredentialsError:
        return None, "No credentials provided."
    except PartialCredentialsError:
        return None, "Incomplete credentials provided."
    except Exception as e:
        return None, str(e)

# Streamlit app interface
st.title('Top 5 RDS and EC2 Instances by On-Demand Expenditure')

# Collect AWS credentials from the user
aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
region_name = st.secrets["AWS_REGION_NAME"]

#st.text_input("AWS Access Key ID", type="password")
#aws_secret_access_key = st.text_input("AWS Secret Access Key", type="password")
#region_name = st.text_input("AWS Region (optional)", "us-east-1")

# Submit button
if st.button("Get Top 5 RDS and EC2 Instances"):
    if aws_access_key_id and aws_secret_access_key:
        # Fetch AWS cost data
        top_5_instances, message = get_top_rds_ec2_costs(aws_access_key_id, aws_secret_access_key, region_name)
        if top_5_instances is not None:
            st.success("Top 5 Instances Retrieved!")
            
            # Display the top 5 instances
            st.write(top_5_instances)
            
            # Plot the top 5 instances with Matplotlib
            plt.figure(figsize=(10, 6))
            plt.bar(top_5_instances['Instance Type'], top_5_instances['Cost'], color='skyblue')
            plt.title('Top 5 RDS and EC2 Instances by On-Demand Cost')
            plt.xlabel('Instance Type')
            plt.ylabel('Cost ($)')
            plt.xticks(rotation=45)
            st.pyplot(plt)
        else:
            st.warning(message)
    else:
        st.warning("Please provide both Access Key ID and Secret Access Key.")