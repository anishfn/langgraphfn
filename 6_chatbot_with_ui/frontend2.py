import streamlit as st
from backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage
import uuid

# -------------------------------
# Utility Functions
# -------------------------------

def generate_thread_id():
    return str(uuid.uuid4())  # safer as string


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []


def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    state = chatbot.get_state(
        config={'configurable': {'thread_id': thread_id}}
    )
    messages = state.values.get('messages', [])

    temp_messages = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = 'user'
        else:
            role = 'assistant'

        temp_messages.append({
            'role': role,
            'content': message.content
        })

    return temp_messages


# -------------------------------
# Initialize session state
# -------------------------------

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])


# -------------------------------
# Sidebar UI
# -------------------------------

st.sidebar.title("langgraphfn")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread_id):
        st.session_state['thread_id'] = thread_id
        st.session_state['message_history'] = load_conversation(thread_id)


# -------------------------------
# Display chat messages
# -------------------------------

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])


# -------------------------------
# User input
# -------------------------------

user_input = st.chat_input("Type here...")


# -------------------------------
# Handle input
# -------------------------------

if user_input:

    # Save user message
    st.session_state['message_history'].append({
        'role': 'user',
        'content': user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # -------------------------------
    # Generate response
    # -------------------------------
    with st.chat_message("assistant"):
        config = {
            'configurable': {
                'thread_id': st.session_state['thread_id']
            }
        }

        stream = chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config=config,
            stream_mode="messages"
        )

        def generate():
            for message_chunk, _ in stream:
                if message_chunk.content:
                    yield message_chunk.content

        ai_message = st.write_stream(generate())

    # -------------------------------
    # Save assistant response
    # -------------------------------
    st.session_state['message_history'].append({
        'role': 'assistant',
        'content': ai_message
    })