import os
import pandas as pd
import warnings
import sys
import streamlit as st
import unidecode
from sentry_sdk import capture_exception

warnings.filterwarnings("ignore")
# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path relative to the current file
# For example, if the directory to add is the parent directory of the current file
parent_dir = os.path.join(current_dir, "..")

# Add the parent directory to sys.path
sys.path.insert(0, parent_dir)

from llm import create_agent, dbchain_movies, generate_query
from gen_final_output import display_text_with_images
from utils import raw_query

st.set_page_config(page_title="PivotConsult Movie")

def reset_conversation():
    st.session_state.messages = []
    st.session_state.agent = create_agent()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = create_agent()

st.title("PivotConsult Data Extractor")
col1, col2 = st.columns([3, 1])
with col2:
    st.button("Reset Chat", on_click=reset_conversation)

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            if isinstance(message["content"], pd.DataFrame):
                st.table(message["content"])
            else:
                st.markdown(message["content"])
        else:
            st.markdown(message["content"])

# Accept user input
query_editable = st.session_state.get("query_editable", "")
if prompt := st.chat_input("Please ask your question"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    #### Changes
    result_query = dbchain_movies.invoke(prompt)
    query = generate_query(result_query)
    # Display the generated SQL query
    st.subheader("Generated SQL Query:")
    query_editable = st.text_area("Generated SQL Query:", value=query, height=200, max_chars=None)
    #####
    st.session_state["query_editable"] = query_editable
    print('Query ---- ', st.session_state.query_editable)

# Execute the SQL query when the "Run Query" button is clicked
if st.button("Run Query"):
    query_editable = st.session_state.get("query_editable", "")  # Define query_editable here
    if query_editable.strip():  # Check if query_editable is not empty
        print('button_clicked')
        with st.spinner("Running query..."):
            try:
                print('Calling raw_query()')
                result_data = raw_query(query_editable, as_df=True)  # Execute the query and return as DataFrame
                print(result_data.shape)
                with st.chat_message("assistant"):
                    if isinstance(result_data, pd.DataFrame):
                        st.table(result_data)  # Display the result as a table
                    else:
                        st.markdown(result_data)  # Display the result as markdown
                    st.session_state.messages.append({"role": "assistant", "content": result_data})  # Add assistant response to chat history
            except Exception as e:
                st.error(f"Error executing the query: {e}")
    else:
        st.error("Please enter a valid SQL query before running.")
