import streamlit as st
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def connect_to_aws(aws_access_key_id, aws_secret_access_key, region_name):
    try:
        # Initialize a session using the AWS credentials
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
        # Example: Creating an S3 client to verify connection
        s3 = session.client('s3')
        # Attempt to list S3 buckets (as a check)
        buckets = s3.list_buckets()
        return True, buckets['Buckets']
    except NoCredentialsError:
        return False, "No credentials provided."
    except PartialCredentialsError:
        return False, "Incomplete credentials provided."
    except Exception as e:
        return False, str(e)

# Streamlit app interface
st.title('AWS Account Connection')

st.write("Please enter your AWS credentials to connect your AWS account to the Streamlit project.")

# Collect AWS credentials from the user
aws_access_key_id = st.text_input("AWS Access Key ID", type="password")
aws_secret_access_key = st.text_input("AWS Secret Access Key", type="password")
region_name = st.text_input("AWS Region (optional)", "us-east-1")

# Submit button
if st.button("Connect to AWS"):
    if aws_access_key_id and aws_secret_access_key:
        connected, message = connect_to_aws(aws_access_key_id, aws_secret_access_key, region_name)
        if connected:
            st.success("Successfully connected to AWS!")
            st.write("S3 Buckets found:", message)
        else:
            st.error(f"Failed to connect to AWS: {message}")
    else:
        st.warning("Please provide both Access Key ID and Secret Access Key.")
