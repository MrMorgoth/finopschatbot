import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.drawing.image import Image
import io

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
    st.bar_chart(
        data,
        x = "Purchase option",
        y = ["Reserved($)", "On Demand($)", "Unused Reserved($)"],
        )
    rounded_avg = round(avg_ondemand_cost, 2)
    rounded_response = round(response, 2)
    with st.chat_message("user"):
        st.write("Hello 👋")
        st.write("The average On-Demand usage for this period is $", rounded_avg, "/hour")
        st.write("To replace this with a reservation, we make a reservation for an amount which is lower than the On-Demand amount by the discount rate")
        st.write("The optimal hourly reservation value is $", rounded_response, "/hour")
    

# Create a function to add a DataFrame to an Excel sheet
def add_dataframe_to_sheet(ws, df, title):
    # Write DataFrame to Excel sheet
    ws.title = title
    for r in dataframe_to_rows(df, index=False, header=True):
        ws.append(r)

# Create a function to generate a graph and add it to the Excel sheet
def add_graph_to_sheet(ws, df, chart_title, img_cell):
    # Generate a plot
    plt.figure(figsize=(10, 6))
    df.plot(kind='bar', stacked=True)
    plt.title(chart_title)
    plt.xlabel('Hour')
    plt.ylabel('Cost ($)')
    plt.tight_layout()

    # Save the plot to an in-memory buffer
    img_data = io.BytesIO()
    plt.savefig(img_data, format='png')
    img_data.seek(0)
    plt.close()

    # Add the image to the worksheet
    img = Image(img_data)
    ws.add_image(img, img_cell)

# Create an Excel workbook and add data and graphs
wb = Workbook()

# Adding the first sheet with data and a graph
with st.form('form', clear_on_submit=True):
    submitted = st.form_submit_button('Generate Excel Spreadsheet', disabled=not(uploaded_file, percentage_discount_rate))
    if submitted:
        ws1 = wb.active
        add_dataframe_to_sheet(ws1, data, "Instance analysis")
        add_graph_to_sheet(ws1, data[['Reserved($)', 'On Demand($)', 'Unused Reserved($)']], "Cost Analysis", "G2")
        with open('reservationanalysis.xlsx', 'rb') as f:
            st.download_button('Download Excel Spreadsheet', f, file_name='reservationanalysis.xlsx')  # Defaults to 'application/octet-stream'

# Save the workbook to a file
excel_file_path = 'reservationanalysis.xlsx'
wb.save(excel_file_path)



# Grab the return value of the button

#if st.download_button(...):
   #st.write('Thanks for downloading!')

