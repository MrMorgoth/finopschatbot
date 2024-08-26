import streamlit as st
from openai import OpenAI
import os
import time
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain import hub
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

# Initiate OpenAI client
openai_api_key = st.secrets["OPENAI_API_KEY"]


prompt = hub.pull("langchain-ai/retrieval-qa-chat")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def generate_response(uploaded_file, query_text):
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
        # LLM
        llm = ChatOpenAI(api_key=openai_api_key)
        # Create QA chain
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(vectorstore.as_retriever(), combine_docs_chain)
        output = rag_chain.invoke({"input": query_text})
        return output["answer"]
    
# Show title and description.
st.title("💬 FinOps Chatbot")
st.write(
    "This is a simple chatbot that uses Generative AI combined with FinOps specific content to generate more accurate responses. "
)

# File upload
uploaded_file = "personas.txt"
#st.file_uploader('Upload a file', type='txt')
# Query text
query_text = st.text_input('Enter your question:', placeholder = 'Please provide a short summary.', disabled=not uploaded_file)

# Form input and query
result = []
with st.form('myform', clear_on_submit=True):
    submitted = st.form_submit_button('Submit', disabled=not(uploaded_file and query_text))
    if submitted:  
        response = generate_response(uploaded_file, query_text)
        result.append(response)

if len(result):
    st.info(response)