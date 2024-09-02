import streamlit as st
import pandas as pd
import numpy as np

def calculate_optimal_reservation(data, discount_rate):
    # Load the CSV file
    #data = pd.read_csv(file)
    # Calculate the total hours by counting the entries (assuming each entry represents one hour)
    total_hours = len(data)
    
    # Calculate total costs for each purchase option
    total_reserved_cost = data['Reserved($)'].sum()
    total_ondemand_cost = data['On Demand($)'].sum()
    total_unused_reserved_cost = data['Unused Reserved($)'].sum()

     # Calculate average hourly usage
    average_ondemand_cost = total_ondemand_cost / total_hours
    optimal_hourly_reservation = avg_ondemand_cost * (1 - float(discount_rate))
    
    return optimal_hourly_reservation


# Show title and description.
st.title("Rate Reduction Genie")
st.write(
    "Upload a file with 7-day hourly usage data by purchase option for a given instance type and the rate reduction genie will calculate the optimal amount of reservations to reduce total spend."
)

# File upload
uploaded_file = st.file_uploader('Upload a file', type='csv')

if uploaded_file:
# Load the CSV file
    global data 
    data = pd.read_csv(uploaded_file)
    total_ondemand_cost = data['On Demand($)'].sum()
    total_hours = len(data)
    global avg_ondemand_cost
    avg_ondemand_cost = total_ondemand_cost / total_hours

# Discount Rate
percentage_discount_rate = st.text_input('Enter the percentage discount:', placeholder = "Don't include the percentage symbol")

result = []
with st.form('myform', clear_on_submit=True):
    submitted = st.form_submit_button('Submit', disabled=not(uploaded_file, percentage_discount_rate))
    if submitted:
        percentage_discount_rate = float(percentage_discount_rate)
        discount_rate = percentage_discount_rate / 100
        response = calculate_optimal_reservation(data, discount_rate)
        result.append(response)

if len(result):
    #st.bar_chart(data=data)
    with st.chat_message("user"):
        st.write("Hello 👋")
        st.write("The average On-Demand usage for this period is $", avg_ondemand_cost, "/hour")
        st.write("To replace this with a reservation, we make a reservation for an amount which is lower than the On-Demand amount by the discount rate")
        st.write("The optimal hourly reservation value is $", response, "/hour")