import streamlit as st
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# Connect to AWS Cost Explorer
def get_aws_cost_data(aws_access_key_id, aws_secret_access_key, region_name):
    try:
        # Create a boto3 client for Cost Explorer
        client = boto3.client(
            'ce',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )

        # Define the time period for the past 30 days
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        # Query AWS Cost Explorer
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
            Metrics=['BlendedCost'],
        )

        # Extract the data
        cost_data = []
        for result in response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            amount = float(result['Total']['BlendedCost']['Amount'])
            cost_data.append([date, amount])

        # Create a DataFrame and convert the 'Date' column to datetime
        df = pd.DataFrame(cost_data, columns=['Date', 'Cost'])
        df['Date'] = pd.to_datetime(df['Date'])

        return df
    
    except NoCredentialsError:
        return None, "No credentials provided."
    except PartialCredentialsError:
        return None, "Incomplete credentials provided."
    except Exception as e:
        return None, str(e)

# Streamlit app interface
st.title('AWS Cost Trends')

# Collect AWS credentials from the user
aws_access_key_id = st.text_input("AWS Access Key ID", type="password")
aws_secret_access_key = st.text_input("AWS Secret Access Key", type="password")
region_name = st.text_input("AWS Region (optional)", "us-east-1")

# Submit button
if st.button("Get AWS Cost Data"):
    if aws_access_key_id and aws_secret_access_key:
        # Fetch AWS cost data
        cost_data, message = get_aws_cost_data(aws_access_key_id, aws_secret_access_key, region_name)
        if cost_data is not None:
            st.success("AWS Cost Data Retrieved!")
            
            # Visualize the cost data
            st.write(cost_data)
            
            # Ensure the Date column is used as the index
            st.line_chart(cost_data.set_index('Date')['Cost'])
            
            # Plot cost trends with Matplotlib
            plt.figure(figsize=(10, 6))
            plt.plot(cost_data['Date'], cost_data['Cost'], marker='o')
            plt.title('AWS Daily Cost Trends (Last 30 Days)')
            plt.xlabel('Date')
            plt.ylabel('Cost ($)')
            plt.xticks(rotation=45)
            st.pyplot(plt)
        else:
            st.error(f"Failed to retrieve cost data: {message}")
    else:
        st.warning("Please provide both Access Key ID and Secret Access Key.")
