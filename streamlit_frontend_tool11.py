import streamlit as st
from langgraph_tool_backend import chatbot,retrive_all_threads
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import uuid

st.markdown(
    """
    <style>
    .stApp {
        background-color: Black;
        border-color=white;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px;
    }
    .user {
        background-color: Blue;
        font-color:Blue:p
        text-align: right;
    }
    .assistant {
        background-color: White;
        text-align: left;
    }
    [data-testid="stSidebar"] {
        background-color: White;
        padding: 20px;
        
    }
    [data-testid="stSidebar"] button {
        background-color: #00B4D8;
        color: Black;
        border-radius: 8px;
        font-weight: bold;
    }
    [data-testid="stSidebar"] h1 {
        color: #00B4D8;
        text-shadow: 0px 0px 5px #00B4D8;
    }
    [data-testid="stSidebar"] h2 {
        color: Blue;
        text-align: center;
        border-bottom: 2px solid #00B4D8;
        padding-bottom: 8px;
        margin-bottom: 15px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.3);
    }
    
   
    </style>
   """ ,
    unsafe_allow_html=True,
)


#********************utility function*******************
def generate_thread_id():
    thread_id=uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id=generate_thread_id()
    st.session_state['thread_id']=thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history']=[]

def add_thread(thread_id):
    if thread_id  not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_converstion(thread_id):
    state=chatbot.get_state(config={'configurable':{'thread_id':thread_id}})
    return state.values.get('messages',[])

#**************************Session setup*********************

if 'message_history' not in st.session_state:
    st.session_state.message_history = {}

if 'thread_id' not in st.session_state:
    st.session_state.thread_id={}

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])


#******************** Main UI***********************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversations')


for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages=load_converstion(thread_id)

        temp_messages=[]

        for msg in messages:
            if isinstance(msg,HumanMessage):
                role='user'
            else:
                role='assistant'
            temp_messages.append({'role': role , 'content': msg.content})
        st.session_state['message_history'] = temp_messages
st.sidebar.info("Created by Pratik Salunke")       

    #****************************** Main UI*********************

# Render conversation history (single chat input below, not inside the sidebar loop)
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {
            "thread_id": st.session_state['thread_id']
        },
        "run_name": "chat_turn",
    }

    # Stream assistant response, collect chunks for history
    with st.chat_message('assistant'):
        #status_container generator can set/modify
        status_holder ={"box":None}
        def ai_only_stream():
            for message_chunk,metadata in chatbot.stream(
                {'messages':[HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode='messages',
            ):
                if isinstance(message_chunk,ToolMessage):
                    tool_name=getattr(message_chunk,"name","tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )
                # stream only assistant token
                if isinstance(message_chunk,AIMessage):
                    yield message_chunk.content
        ai_message=st.write_stream(ai_only_stream())

        #finalize only if a tool was actually used
        if status_holder['box'] is not None:
            status_holder['box'].update(
                label="✅ Tool finished", state="complete", expanded=False

            )
        #save assistant message
        st.session_state["message_history"].append(
            {"role":"assistant" ,"content":ai_message}
        )
            
       