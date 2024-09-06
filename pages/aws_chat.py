import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
import pandas as pd
from datetime import datetime, timedelta

# Initialize OpenAI API for LLM interaction

# AWS Cost Explorer query function for detailed EC2 cost data
def get_detailed_ec2_costs(aws_access_key_id, aws_secret_access_key, region_name):
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

        # Query AWS Cost Explorer for detailed EC2 cost data
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',  # Daily breakdown for detailed cost view
            Metrics=['UnblendedCost'],
            GroupBy=[
                {'Type': 'DIMENSION', 'Key': 'INSTANCE_TYPE'},
                {'Type': 'DIMENSION', 'Key': 'REGION'}
            ],
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': ['Amazon Elastic Compute Cloud - Compute']
                }
            }
        )

        # Parse the response
        cost_data = []
        for result in response['ResultsByTime'][0]['Groups']:
            for group in result['Groups']:
                instance_type = group['Keys'][1]
                region = group['Keys'][2]
                usage_type = group['Keys'][3]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                date = result['TimePeriod']['Start']
                cost_data.append([date, instance_type, region, usage_type, amount])
        

        # Return the data as a DataFrame
        df = pd.DataFrame(cost_data, columns=['Date', 'Instance Type', 'Region', 'Usage Type', 'Cost'])
        return df

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
            top_instances, error_message = get_detailed_ec2_costs(aws_access_key_id, aws_secret_access_key, region_name)
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
