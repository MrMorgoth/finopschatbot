import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from openai import OpenAI
import pandas as pd
from datetime import datetime, timedelta

# Initialize OpenAI API for LLM interaction
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

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


# LLM Interaction function (Updated for OpenAI API v1.0.0)
def ask_llm(question, aws_access_key_id, aws_secret_access_key, region_name):
    try:
        # If the user's question is related to AWS cost data (intercept)
        if "top instances by on-demand spend" in question.lower():
            service = "Amazon Elastic Compute Cloud - Compute"  # EC2 instance service
            top_instances, error_message = get_top_rds_ec2_costs(aws_access_key_id, aws_secret_access_key, region_name)
            if top_instances is not None:
                return f"Here are the top EC2 instances by On-Demand spend:\n{top_instances}"
            else:
                return f"Error fetching AWS data: {error_message}"
            
        # Use the new OpenAI API interface
        response = client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an AI assistant with the ability to query AWS cost data using the provided credentials."},
            {"role": "user", "content": question}
        ])
        answer = response.choices[0].message.content.strip()
        
    except Exception as e:
            return f"Error occurred while interacting with the LLM: {str(e)}"

# Streamlit UI for chat interface
st.title("Chat with LLM and Query AWS Cost Data")

# AWS credentials input
# Collect AWS credentials from the user
aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
region_name = st.secrets["AWS_REGION_NAME"]

# Chatbox for LLM interaction
st.write("Ask the LLM questions related to your AWS usage:")
user_question = st.text_input("Your question")

# Submit button
if st.button("Ask"):
    if aws_access_key_id and aws_secret_access_key and user_question:
        llm_response = ask_llm(user_question, aws_access_key_id, aws_secret_access_key, region_name)
        st.write(llm_response)
    else:
        st.warning("Please provide AWS credentials and ask a question.")
