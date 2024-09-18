import streamlit as st
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
import boto3
import pandas as pd
from datetime import datetime, timedelta
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

#aws_access_key_id = st.text_input("AWS Access Key ID", type="password")
#aws_secret_access_key = st.text_input("AWS Secret Access Key", type="password")
#region_name = st.text_input("AWS Region (optional)", "eu-west-2")

aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
region_name = st.secrets["REGION_NAME"]

def get_top_rds_ec2_costs():
    """Search AWS account for top RDS and EC2 instances by cost and returns dataframe of top 10 instances"""
    try:
        # Create a boto3 client for Cost Explorer
        client = boto3.client(
            'ce',
            aws_access_key_id = aws_access_key_id,
            aws_secret_access_key = aws_secret_access_key,
            region_name = region_name
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

openai_api_key = st.secrets["OPENAI_API_KEY"]
llm = OpenAI(model="gpt-3.5-turbo", temperature=0)
agent = ReActAgent.from_tools([aws_top_instances_tool], llm=llm, verbose=True)

st.set_page_config(page_title="AWS FinOps Agent", page_icon="", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title("Chat with your AWS Cost Data 💬")

def chat_interface():
    if "messages" not in st.session_state.keys():  # Initialise the chat messages history
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Ask me a question about your AWS Cost Data",
            }
        ]
    if prompt := st.chat_input(
        "Ask a question"
    ):  # Prompt for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:  # Write message history to UI
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is not from assistant, generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            response_stream = agent.chat(prompt)
            st.write(response_stream)
            message = {"role": "assistant", "content": response_stream}
            # Add response to message history
            st.session_state.messages.append(message)

chat_interface()

if st.button("Get top instances"):
    get_top_rds_ec2_costs()