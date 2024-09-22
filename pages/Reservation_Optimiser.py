import boto3
import streamlit as st
from datetime import datetime, timedelta, timezone
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import pandas as pd

# Collect AWS credentials from the user
aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
region_name = st.secrets["REGION_NAME"]

pricing_client = boto3.client('pricing', region_name='eu-west-2')

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
            reserved_cost = get_reserved_instance_pricing(instance_type, 'eu-west-2')
            percentage_saving = 0
            if reserved_cost:
                saving_perc=(amount-reserved_cost)/amount
                percentage_saving = saving_perc
            cost_data.append([service, instance_type, amount, reserved_cost, percentage_saving])

        # Create a DataFrame and sort by cost
        df = pd.DataFrame(cost_data, columns=['Service', 'Instance Type', 'Cost', 'Reserved Cost', 'Percentage Saving'])
        top_5 = df.sort_values(by='Cost', ascending=False).head(10)

        return top_5, None
    
    except NoCredentialsError:
        return None, "No credentials provided."
    except PartialCredentialsError:
        return None, "Incomplete credentials provided."
    except Exception as e:
        return None, str(e)
    
def get_reserved_instance_pricing(instance_type, region):
    try:
        response = pricing_client.get_products(
            ServiceCode='AmazonRDS',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region},
                {'Type': 'TERM_MATCH', 'Field': 'termType', 'Value': 'Reserved'},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
            ],
            MaxResults=1
        )

        # Extract the reserved instance price from the response
        product = response['PriceList'][0]
        product_data = eval(product)  # Convert JSON string to dictionary
        price_dimensions = product_data['terms']['Reserved'].values()
        for dimension in price_dimensions:
            price_per_hour = dimension['priceDimensions'].values()[0]['pricePerUnit']['USD']
            return float(price_per_hour)

    except Exception as e:
        print(f"Error fetching reserved pricing for {instance_type}: {e}")
        return None

# Streamlit app interface
st.set_page_config(page_title="Rate Reduction Genie", page_icon="🧞‍♂️", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title('Top Instances by On-Demand Expenditure')
st.write(
    "Below are the top instances by On-Demand spend along with possible savings to be realised."
)
top_instances = get_top_rds_ec2_costs(aws_access_key_id, aws_secret_access_key, region_name)
c= st.container()
c.table(top_instances)