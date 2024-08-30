import streamlit as st
import pandas as pd
import numpy as np

# Show title and description.
st.title("Rate Reduction Genie")
st.write(
    "Upload a file with 7-day hourly usage data for an instance type and the rate reduction genie will calculate the optimal amount of reservations to reduce total spend."
)

# File upload
uploaded_file = st.file_uploader('Upload a file', type='csv')
discount_rate = st.text_input


def calculate_optimal_reservation(file_path):
    # Load the CSV file
    data = pd.read_csv(file_path)
    
    # Calculate the total hours by counting the entries (assuming each entry represents one hour)
    total_hours = len(data)
    
    # Calculate total costs for each purchase option
    total_reserved_cost = data['Reserved($)'].sum()
    total_ondemand_cost = data['On Demand($)'].sum()
    total_unused_reserved_cost = data['Unused Reserved($)'].sum()

     # Calculate average hourly usage
    average_ondemand_cost = total_ondemand_cost / total_hours
    optimal_hourly_reservation = average_ondemand_cost * (1-discount_rate)
    
    return optimal_hourly_reservation
