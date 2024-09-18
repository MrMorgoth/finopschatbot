import boto3
import pandas as pd
from datetime import datetime, timedelta
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool

def get_top_rds_ec2_costs(aws_access_key_id, aws_secret_access_key, region_name):
    """Search AWS account for top RDS and EC2 instances by cost and returns dataframe of top 10 instances"""
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
        top_10 = df.sort_values(by='Cost', ascending=False).head(10)

        return top_10, None
    
    except NoCredentialsError:
        return None, "No credentials provided."
    except PartialCredentialsError:
        return None, "Incomplete credentials provided."
    except Exception as e:
        return None, str(e) 

aws_top_instances_tool = FunctionTool.from_defaults(fn=get_top_rds_ec2_costs)