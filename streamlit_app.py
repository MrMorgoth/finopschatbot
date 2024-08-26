import streamlit as st
from openai import OpenAI
import os
import time
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS

# Initiate OpenAI client


def generate_response(uploaded_file, openai_api_key, query_text):
    # Load document if file is uploaded
    
    if uploaded_file is not None:
        documents = [uploaded_file.read().decode()]
        # Split documents into chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.create_documents(documents)
        # Select embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])
        # Create a vectorstore from documents
        vectorstore = FAISS.from_documents(documents=texts,
                                   embedding=OpenAIEmbeddings())
        # Create retriever interface
        retriever = vectorstore.as_retriever()
        # Create QA chain
        qa = RetrievalQA.from_chain_type(llm=OpenAI(openai_api_key=openai_api_key), chain_type='stuff', retriever=retriever)
        return qa.run(query_text)
    



# Show title and description.
st.title("💬 FinOps Chatbot")
st.write(
    "This is a simple chatbot that uses Generative AI combined with FinOps specific content to generate more accurate responses. "
)

# File upload
uploaded_file = st.file_uploader('Upload a file', type='txt')
# Query text
query_text = st.text_input('Enter your question:', placeholder = 'Please provide a short summary.', disabled=not uploaded_file)

# Form input and query
result = []
with st.form('myform', clear_on_submit=True):
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    print(openai_api_key)
    submitted = st.form_submit_button('Submit', disabled=not(uploaded_file and query_text))
    if submitted:
        with st.spinner('Calculating...'):
            response = generate_response(uploaded_file, openai_api_key, query_text)
            result.append(response)

if len(result):
    st.info(response)