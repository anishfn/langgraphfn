from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import sqlite3

load_dotenv()

# model
llm = ChatMistralAI()

# state
class ChatState(TypedDict):
  messages: Annotated[list[BaseMessage], add_messages]

# sqlite3 db
conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)

# node functions
def chat_node(state: ChatState) -> ChatState:
  messages = state['messages']
  response = llm.invoke(messages)
  return {'messages': [response]}

# checkpointer
checkpointer = SqliteSaver(conn=conn)

# graph
graph = StateGraph(ChatState)

# nodes
graph.add_node("chat_node", chat_node)

# edges
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# compile graph
chatbot = graph.compile(checkpointer=checkpointer)

# retrieve all threads function
def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    return list(all_threads)

