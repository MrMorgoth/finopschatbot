import streamlit as st
import pandas as pd
import numpy as np

# Show title and description.
st.title("Rate Reduction Genie")
st.write(
    "Upload a file with 7-day hourly usage data for an instance type and the rate reduction genie will calculate the optimal amount of reservations to reduce total spend"
)