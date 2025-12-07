from langgraph.graph import StateGraph ,START ,END
from typing import TypedDict,Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.prebuilt import ToolNode , tools_condition
from langchain_core.tools import tool   
from dotenv import load_dotenv
import sqlite3
import requests

load_dotenv()

llm=ChatOpenAI()

search_tool=DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_num: float , second_num: float,operation:str)-> dict:
    """ 
    Perform basic arthmatic operation on two numbers.
    Supported Operation: add,sub,mul,div
    """
    try:
        if operation =="add":
            result=first_num + second_num
        elif operation=="sub":
            result=first_num - second_num
        elif operation=="mul":
            result=first_num * second_num
        elif operation=="div":
            if second_num==0:
                return {"error":"division by zero isn't allowed"}
        else:
            return {"error":f"Unsupported operation'{operation}'"}
        
        return {"first_num":first_num , "second_num":second_num , "operation":operation,"result":result}
    except Exception as e:
        return {"error":str(e)}
    
@ tool
def get_weather(city:str)->str:
  """
  Get real weather data of given city
  """
  fake_data={
      "Pune": "28°C, Sunny",
        "Mumbai": "31°C, Humid",
        "Delhi": "26°C, Cloudy"

  }
  return fake_data.get(city,"weather not available")

tools=[search_tool,calculator,get_weather]
llm_with_tools=llm.bind_tools(tools)

class ChatState(TypedDict):
    messages:Annotated[list[BaseMessage],add_messages]

def chat_node(state:ChatState):
    messages=state['messages']
    response=llm_with_tools.invoke(messages)
    return {"messages":[response]}
tool_node=ToolNode(tools)

conn=sqlite3.connect(database="Chatbot.db" , check_same_thread=False)
checkpointer=SqliteSaver(conn=conn)

graph=StateGraph(ChatState)
graph.add_node("chat_node",chat_node)
graph.add_node("tools",tool_node)

graph.add_edge(START , "chat_node")

graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools','chat_node')

chatbot=graph.compile(checkpointer=checkpointer)


def retrive_all_threads():
    all_threads=set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)


