import streamlit as st
import boto3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedeltafrom 
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from streamlit_extras.metric_cards import style_metric_cards

st.write("New Page!")