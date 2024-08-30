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
percentage_discount_rate = st.text_input("Percentage Discount Rate - Don't include the percentage symbol")


def calculate_optimal_reservation(file):
    # Load the CSV file
    data = pd.read_csv(file)
    percentage_discount_rate = int(percentage_discount_rate)
    discount_rate = percentage_discount_rate // 100
    # Calculate the total hours by counting the entries (assuming each entry represents one hour)
    total_hours = len(data)
    
    # Calculate total costs for each purchase option
    total_reserved_cost = data['Reserved($)'].sum()
    total_ondemand_cost = data['On Demand($)'].sum()
    total_unused_reserved_cost = data['Unused Reserved($)'].sum()

     # Calculate average hourly usage
    average_ondemand_cost = total_ondemand_cost / total_hours
    optimal_hourly_reservation = average_ondemand_cost * (1 - int(discount_rate))
    
    return optimal_hourly_reservation


result = []
with st.form('myform', clear_on_submit=True):
    submitted = st.form_submit_button('Submit', disabled=not(uploaded_file))
    if submitted:
        response = calculate_optimal_reservation(uploaded_file)
        #response = generate_response(uploaded_file, query_text)
        result.append(response)

if len(result):
    st.info(response)