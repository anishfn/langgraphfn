from langgraph.graph import StateGraph, START
from dotenv import load_dotenv
from langchain_mistralai import ChatMistralAI
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
# from langchain_core.tools import tool
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()

# llm
llm = ChatMistralAI(model="mistral-small-2506")

# mcp client
client = MultiServerMCPClient({
    "expensefn": {
        "transport": "streamable_http",
        "url": "https://expensefn.fastmcp.app/mcp"
    }
})



# state
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# build graph
async def build_graph():
    
    tools = await client.get_tools()
    llm_with_tools = llm.bind_tools(tools)
    # node functions
    async def chat_node(state: ChatState):
        messages = state['messages']
        response = await llm_with_tools.ainvoke(messages)
        return {'messages': [response]}

    tool_node = ToolNode(tools)

    # defining graph and nodes
    graph = StateGraph(ChatState)

    # nodes
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", tool_node)

    # edges (graph connections)
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)
    graph.add_edge("tools", "chat_node")

    chatbot = graph.compile()

    return chatbot

# main function
async def main():
    chatbot = await build_graph()

    # running the graph
    result = await chatbot.ainvoke({"messages": [HumanMessage(content="add 123 and 347")]})
    print(result['messages'][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
