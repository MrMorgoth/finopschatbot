import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import openai
import pandas as pd
from datetime import datetime, timedelta

# Initialize OpenAI API for LLM interaction
openai.api_key = st.secrets["OPENAI_API_KEY"]

# AWS Cost Explorer query function
def get_cost_data(aws_access_key_id, aws_secret_access_key, region_name, service):
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

        # Query AWS Cost Explorer for a specific service (EC2, RDS)
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
                    'Values': [service]
                }
            }
        )

        # Parse the response
        cost_data = []
        for result in response['ResultsByTime'][0]['Groups']:
            instance_type = result['Keys'][1]
            amount = float(result['Metrics']['UnblendedCost']['Amount'])
            cost_data.append([instance_type, amount])

        # Return the data as a DataFrame
        df = pd.DataFrame(cost_data, columns=['Instance Type', 'Cost'])
        return df
    
    except NoCredentialsError:
        return None, "No credentials provided."
    except PartialCredentialsError:
        return None, "Incomplete credentials provided."
    except Exception as e:
        return None, str(e)

# LLM Interaction function (Updated for OpenAI API v1)
def ask_llm(question, aws_access_key_id, aws_secret_access_key, region_name):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an assistant that helps with AWS cost data queries."},
                {"role": "user", "content": question}
            ],
        )
        answer = response['choices'][0]['message']['content'].strip()

        # If the LLM detects a question related to AWS usage, it fetches the data
        if "top instances by on-demand spend" in question.lower():
            service = "Amazon Elastic Compute Cloud - Compute"  # Example for EC2
            top_instances, error_message = get_cost_data(aws_access_key_id, aws_secret_access_key, region_name, service)
            if top_instances is not None:
                return f"LLM: {answer}\n\nHere are the top EC2 instances by On-Demand spend:\n{top_instances}"
            else:
                return f"LLM: {answer}\n\nError fetching AWS data: {error_message}"
        else:
            return f"LLM: {answer}"
    except Exception as e:
        return f"Error occurred while interacting with the LLM: {str(e)}"

# Streamlit UI for chat interface
st.title("Chat with LLM and Query AWS Cost Data")

# AWS credentials input
st.write("Please enter your AWS credentials:")
aws_access_key_id = st.text_input("AWS Access Key ID", type="password")
aws_secret_access_key = st.text_input("AWS Secret Access Key", type="password")
region_name = st.text_input("AWS Region", "us-east-1")

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

