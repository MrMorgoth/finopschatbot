import streamlit as st
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings

openai_api_key = st.secrets["OPENAI_API_KEY"]

st.set_page_config(page_title="AWS FinOps Agent", page_icon="", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title("Chat with your AWS Cost Data 💬")


@st.cache_resource(show_spinner=False)
def load_data():
    reader = SimpleDirectoryReader(input_dir="pages/data", recursive=True)
    docs = reader.load_data()
    Settings.llm = OpenAI(
        model="gpt-3.5-turbo",
        temperature=0.2,
        system_prompt="""You are an expert on 
        FinOps and your 
        job is to answer technical questions. 
        Assume that all questions are related 
        to FinOps. Keep 
        your answers technical and based on 
        facts – do not hallucinate features. Write in British English. Use paragraphs and good sentence structure to make your output easy to read""",
    )
    index = VectorStoreIndex.from_documents(docs)
    return index


index = load_data()

def chat_interface():
    if "messages" not in st.session_state.keys():  # Initialise the chat messages history
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Ask me a question about your AWS Cost Data",
            }
        ]

    if "chat_engine" not in st.session_state.keys():  # Initialise the chat engine
        st.session_state.chat_engine = index.as_chat_engine(
            chat_mode="condense_question", verbose=True, streaming=True
        )

    if prompt := st.chat_input(
        "Ask a question"
    ):  # Prompt for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages:  # Write message history to UI
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # If last message is not from assistant, generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            response_stream = st.session_state.chat_engine.stream_chat(prompt)
            st.write_stream(response_stream.response_gen)
            message = {"role": "assistant", "content": response_stream.response}
            # Add response to message history
            st.session_state.messages.append(message)


def run():
    ready = False
    aws_access_key_id = st.session_state.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = st.session_state.get("AWS_SECRET_ACCESS_KEY")
    
    if not aws_access_key_id and aws_secret_access_key:
        # Collect AWS credentials from the user
        aws_access_key_id = st.text_input("AWS Access Key ID", type="password")
        aws_secret_access_key = st.text_input("AWS Secret Access Key", type="password")
        region_name = st.text_input("AWS Region (optional)", "eu-west-2")

        if aws_access_key_id and aws_secret_access_key:
            ready = True

    if ready:
        chat_interface()
run()