import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from agent_setup import run_agent
from rag import extract_text_from_excel,extract_text_from_pdf, extract_text_from_docx, extract_text_from_json, add_document_to_db, retrieve_context, generate_response, load_initial_knowledge
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Mock action suggestions (can be expanded dynamically)
actions = [
    {"name": "Restart Service"},
    {"name": "Get System Logs"},
    {"name": "Send Email"}
]

# MCP Tool Function
async def call_mcp_tool(tool_name: str, params: dict):
    """Call MCP server tool for transactional data"""
    try:
        async with AsyncExitStack() as exit_stack:
            server_params = StdioServerParameters(
                command="/Users/kalavathi/Downloads/agentic demo/.venv/bin/python",
                args=["/Users/kalavathi/Downloads/agentic demo/gen-ai-rag/code/src/main.py"]
            )
            
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()
            
            result = await session.call_tool(tool_name, params)
            return result.content[0].text
    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"

# Set the Streamlit page layout
st.set_page_config(page_title="Platform Engineer Chatbot", layout="wide")

st.title("🤖 Platform Engineer Assistant")

# File Upload
uploaded_file = st.file_uploader("Update Knowledge Base", type=["xlsx", "pdf", "docx", "txt", "json"])
if uploaded_file:
    st.write("Processing document...")
    file_type = uploaded_file.name.split(".")[-1].lower()
    
    if file_type == "xlsx":
        document_text = extract_text_from_excel(uploaded_file)
    elif file_type == "pdf":
        document_text = extract_text_from_pdf(uploaded_file)
    elif file_type == "docx":
        document_text = extract_text_from_docx(uploaded_file)
    elif file_type == "json":
        document_text = extract_text_from_json(uploaded_file)

    add_document_to_db(document_text, uploaded_file.name)
    st.success("Document added to ChromaDB!")

# Initialize chat history if not present
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Load initial knowledge only once
if "knowledge_loaded" not in st.session_state:
    with st.spinner("Loading knowledge base..."):
        load_initial_knowledge("data")
    st.session_state.knowledge_loaded = True

# Sidebar Info
with st.sidebar:
    st.markdown("### 👨‍💻 About Me")
    st.write(
        "I'm a **Platform Engineer Assistant**, here to help with:\n"
        "- Server restarts 🔄\n"
        "- Checking service health ✅\n"
        "- Debugging deployment issues 🛠️\n"
        "- Fetching logs 📜\n"
        "- Ask me anything!"
    )

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["💬 Chat with AI", "📊 Transactional Data", "🔧 Actions"])

# TAB 1: Chat with AI
with tab1:
    st.markdown("### 💬 Chat with the AI")

    # User Input Field
    user_input = st.chat_input("Ask me anything about platform engineering...")
    if user_input and isinstance(user_input, str):
        st.session_state.chat_history.append(HumanMessage(content=user_input))

    if user_input:
            context = retrieve_context(user_input)
            print("the context is : "+context)
            answer = generate_response(user_input, context)
            st.session_state.chat_history.append(AIMessage(content=answer))

    # Display chat history in a conversational format
    for message in st.session_state.chat_history:
        if isinstance(message, HumanMessage):
            st.markdown(f"🟢 **Platform Engineer:** {message.content}")
        else:
            st.markdown(f"🤖 **AI Bot:** {message.content}")

# TAB 2: Transactional Data
with tab2:
    st.markdown("### 📊 Transactional Data Query")
    
    # Customer lookup
    st.subheader("👤 Get Customer Information")
    col1, col2 = st.columns([3, 1])
    with col1:
        customer_id = st.text_input("Enter Customer ID (e.g., CUST123):", "CUST123", key="cust_info_id")
    with col2:
        if st.button("Get Info", key="btn_cust_info"):
            with st.spinner("Fetching customer information..."):
                result = asyncio.run(call_mcp_tool("get_customer_info", {"customer_id": customer_id}))
                st.write(result)

    # Customer name lookup
    st.subheader("🔍 Find Customer ID by Name")
    col1, col2 = st.columns([3, 1])
    with col1:
        customer_name = st.text_input("Enter Customer Name (e.g., Alice Johnson):", "Alice Johnson", key="cust_name")
    with col2:
        if st.button("Find ID", key="btn_find_cust"):
            with st.spinner("Searching for customer..."):
                result = asyncio.run(call_mcp_tool("get_customer_ids_by_name", {"customer_name": customer_name}))
                st.write(result)

    # Order lookup
    st.subheader("📦 Get Orders by Customer")
    col1, col2 = st.columns([3, 1])
    with col1:
        order_cust_id = st.text_input("Enter Customer ID for Orders:", "CUST123", key="order_cust_id")
    with col2:
        if st.button("Get Orders", key="btn_get_orders"):
            with st.spinner("Fetching orders..."):
                result = asyncio.run(call_mcp_tool("get_orders_by_customer_id", {"customer_id": order_cust_id}))
                st.write(result)

    # Order details
    st.subheader("📋 Get Order Details")
    col1, col2 = st.columns([3, 1])
    with col1:
        order_id = st.text_input("Enter Order ID (e.g., ORD1001):", "ORD1001", key="order_id")
    with col2:
        if st.button("Get Details", key="btn_order_details"):
            with st.spinner("Fetching order details..."):
                result = asyncio.run(call_mcp_tool("get_order_details", {"order_id": order_id}))
                st.write(result)

    # Inventory search
    st.subheader("🛒 Search Inventory")
    col1, col2 = st.columns([3, 1])
    with col1:
        product_name = st.text_input("Enter Product Name:", "Mouse", key="product_name")
    with col2:
        if st.button("Search", key="btn_search_inventory"):
            with st.spinner("Searching inventory..."):
                result = asyncio.run(call_mcp_tool("check_inventory", {"product_name": product_name}))
                st.write(result)

# TAB 3: Actions
with tab3:
    st.markdown("### 🔧 Agentic AI Actions")
    st.write("Execute predefined platform engineering actions:")
    
    if actions:
        cols = st.columns(2)
        for idx, action in enumerate(actions):
            with cols[idx % 2]:
                if st.button(f"▶️ {action['name']}", key=f"action_{idx}"):
                    st.session_state.chat_history.append(HumanMessage(content=action["name"]))
                    with st.spinner(f"Executing {action['name']}..."):
                        action_response = run_agent(action["name"])
                        st.session_state.chat_history.append(AIMessage(content=action_response.messages[1].content))
                        st.success(f"✅ {action['name']} completed!")
                        st.rerun()