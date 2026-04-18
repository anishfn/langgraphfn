# Streamlit + LangGraph Chatbot — Detailed Notes

## 1. Overview

This application is a **multi-threaded chatbot interface** built using:

* `streamlit` → UI framework
* `chatbot` (backend) → handles AI logic and state
* `session_state` → stores UI state per user session
* `uuid` → generates unique conversation IDs

### Core Idea

Each conversation is treated as a **thread**, identified by a unique `thread_id`.
The app allows:

* Multiple conversations
* Switching between them
* Persisting history via backend state

---

## 2. Imports

```python
import streamlit as st
from backend import chatbot
from langchain_core.messages import HumanMessage
import uuid
```

### Explanation

* `streamlit as st`
  Provides UI components like sidebar, chat messages, input box.

* `chatbot`
  Your LangGraph/LangChain backend. Handles:

  * message processing
  * state management
  * streaming responses

* `HumanMessage`
  Standard message format required by LangChain models.

* `uuid`
  Used to generate **globally unique thread IDs**.

---

## 3. Utility Functions

### 3.1 `generate_thread_id()`

```python
def generate_thread_id():
    return str(uuid.uuid4())
```

#### Purpose

* Creates a **unique identifier** for each chat thread.
* Converted to string because:

  * Easier to store
  * Avoids serialization issues

---

### 3.2 `reset_chat()`

```python
def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []
```

#### What it does

* Starts a **new conversation session**
* Generates new `thread_id`
* Adds it to thread list
* Clears current chat history

#### Key Concept

This function separates:

* **UI state reset** (message_history)
* **logical thread creation** (thread_id)

---

### 3.3 `add_thread(thread_id)`

```python
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
```

#### Purpose

* Maintains a list of all conversations
* Prevents duplicate entries

#### Data Structure

```python
chat_threads = [
  "uuid-1",
  "uuid-2",
  "uuid-3"
]
```

---

### 3.4 `load_conversation(thread_id)`

```python
def load_conversation(thread_id):
```

#### Purpose

* Loads stored messages from backend
* Converts them into UI-compatible format

---

#### Step 1: Fetch state

```python
state = chatbot.get_state(
    config={'configurable': {'thread_id': thread_id}}
)
```

* Retrieves backend state tied to this thread
* `thread_id` ensures isolation between conversations

---

#### Step 2: Extract messages

```python
messages = state.values.get('messages', [])
```

* Safely retrieves messages
* Defaults to empty list if none exist

---

#### Step 3: Convert message format

```python
for message in messages:
    if isinstance(message, HumanMessage):
        role = 'user'
    else:
        role = 'assistant'
```

* Backend uses LangChain message objects
* UI expects:

  ```python
  {'role': 'user' or 'assistant', 'content': "..."}
  ```

---

#### Step 4: Build UI-friendly structure

```python
temp_messages.append({
    'role': role,
    'content': message.content
})
```

---

#### Output Format

```python
[
  {'role': 'user', 'content': 'Hello'},
  {'role': 'assistant', 'content': 'Hi there'}
]
```

---

## 4. Session State Initialization

```python
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
```

### Purpose

* Stores messages for current session
* Prevents KeyError

---

```python
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
```

### Purpose

* Ensures every session has an active thread

---

```python
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []
```

### Purpose

* Stores all thread IDs

---

```python
add_thread(st.session_state['thread_id'])
```

### Purpose

* Adds initial thread on app load

---

## 5. Sidebar UI

### Title

```python
st.sidebar.title("langgraphfn")
```

---

### New Chat Button

```python
if st.sidebar.button("New Chat"):
    reset_chat()
```

#### Behavior

* Starts a fresh conversation
* Clears previous UI messages
* Creates new thread

---

### Conversation List

```python
for thread_id in st.session_state['chat_threads'][::-1]:
```

#### Key Concept: List Reversal

* `[::-1]` reverses the list
* Ensures:

  * latest chats appear first
  * better UX

---

```python
if st.sidebar.button(thread_id):
```

* Each thread becomes clickable

---

```python
st.session_state['thread_id'] = thread_id
st.session_state['message_history'] = load_conversation(thread_id)
```

#### Behavior

* Switch active conversation
* Load stored messages into UI

---

## 6. Displaying Messages

```python
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])
```

### Explanation

* Iterates over chat history
* Displays messages using Streamlit chat UI

### Roles

* `'user'` → right-aligned
* `'assistant'` → left-aligned

---

## 7. User Input

```python
user_input = st.chat_input("Type here...")
```

### Behavior

* Displays chat-style input box
* Returns input only when user sends message

---

## 8. Handling User Input

### Save User Message

```python
st.session_state['message_history'].append({
    'role': 'user',
    'content': user_input
})
```

---

### Display User Message

```python
with st.chat_message("user"):
    st.markdown(user_input)
```

---

## 9. Generating AI Response

### Configuration

```python
config = {
    'configurable': {
        'thread_id': st.session_state['thread_id']
    }
}
```

#### Purpose

* Links response to correct thread
* Ensures backend stores state properly

---

### Streaming Response

```python
stream = chatbot.stream(
    {'messages': [HumanMessage(content=user_input)]},
    config=config,
    stream_mode="messages"
)
```

#### Key Concepts

* Uses **streaming**
* Response arrives in chunks instead of full output

---

### Generator Function

```python
def generate():
    for message_chunk, _ in stream:
        if message_chunk.content:
            yield message_chunk.content
```

#### Purpose

* Converts stream into iterable text output
* Enables real-time rendering

---

### Display Streaming Output

```python
ai_message = st.write_stream(generate())
```

#### Behavior

* Displays text as it is generated
* Returns final combined message

---

## 10. Saving Assistant Response

```python
st.session_state['message_history'].append({
    'role': 'assistant',
    'content': ai_message
})
```

### Purpose

* Keeps conversation persistent in UI
* Ensures history survives reruns

---

## 11. Full Application Flow

1. App initializes session state
2. Sidebar shows threads
3. User selects or creates a thread
4. Messages are loaded and displayed
5. User inputs message
6. Message is saved and displayed
7. Backend processes input
8. Response is streamed
9. Response is saved
10. Cycle repeats

---

## 12. Key Concepts Summary

### Session State

Acts as temporary memory for:

* messages
* threads
* active conversation

---

### Threading System

* Each chat = unique `thread_id`
* Enables multiple independent conversations

---

### Streaming

* Improves responsiveness
* Mimics real-time typing

---

### Backend–Frontend Separation

* Frontend: Streamlit UI
* Backend: chatbot logic + state

---

### Message Transformation

* Backend format → LangChain objects
* UI format → dictionaries

---

## 13. Common Issues

### Missing session initialization

Leads to KeyError

---

### Not passing thread_id

Mixes conversation states

---

### Not saving assistant response

Chat appears incomplete on rerun

---

### Incorrect message conversion

Leads to wrong roles or crashes

---

## 14. Possible Enhancements

* Replace UUIDs with readable chat titles
* Add delete conversation feature
* Persist chats in database
* Add timestamps
* Add search across conversations
* Add multi-user authentication

