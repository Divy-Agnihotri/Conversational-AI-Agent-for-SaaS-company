import streamlit as st
from backend import chat_with_bot, initialize_state

st.set_page_config(page_title="AI Assistant", layout="centered")

st.title("💬 AI Assistant")

# Initialize state ONCE
if "state" not in st.session_state:
    st.session_state.state = initialize_state()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box (ChatGPT style)
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Call backend
    st.session_state.state, response = chat_with_bot(
        st.session_state.state, user_input
    )

    # Show assistant response
    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )
