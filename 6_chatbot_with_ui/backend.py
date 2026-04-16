from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langchain_mistralai import ChatMistralAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

load_dotenv()

# model
llm = ChatMistralAI()

# state
class ChatState(TypedDict):
  messages: Annotated[list[BaseMessage], add_messages]

# node functions
def chat_node(state: ChatState) -> ChatState:
  messages = state['messages']
  response = llm.invoke(messages)
  return {'messages': [response]}

# checkpointer
checkpointer = InMemorySaver()

# graph
graph = StateGraph(ChatState)

# nodes
graph.add_node("chat_node", chat_node)

# edges
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

# compile graph
chatbot = graph.compile(checkpointer=checkpointer)