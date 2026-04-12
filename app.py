import logging
import asyncio
import uuid
import streamlit as st
from agent.agent_core import generate_agent_reply
from agent.utils.formatters import guess_company_name, format_section_text
from config import settings

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Company Research Assistant", layout="wide")

# Phase 3.1: Multi-User Session Isolation
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "plan" not in st.session_state:
    st.session_state.plan = None
if "company" not in st.session_state:
    st.session_state.company = ""
if "diff_result" not in st.session_state:
    st.session_state.diff_result = {}

# Phase 4.2: Input Sanitization
INJECTION_PATTERNS = [
    "ignore previous", "ignore above",
    "disregard", "forget instructions",
    "you are now", "act as", "jailbreak"
]

st.title("💼 Company Research Assistant")

with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Reset Conversation"):
        st.session_state.chat_history = []
        st.session_state.plan = None
        st.session_state.company = ""
        st.session_state.diff_result = {}
        st.success("State cleared.")

    # Phase 2.4: Show What Changed
    if st.session_state.diff_result:
        with st.expander("🔄 What Changed Since Last Research", expanded=True):
            for section, values in st.session_state.diff_result.items():
                st.markdown(f"**{section.replace('_', ' ').title()}**")
                st.markdown(f"🔴 Before: {values['old']}")
                st.markdown(f"🟢 Now: {values['new']}")
                st.markdown("---")
    elif st.session_state.company and st.session_state.plan:
        st.info(f"🆕 First time researching {st.session_state.company}")

user_msg = st.chat_input("Ask about any company...")

if user_msg:
    user_msg = user_msg.strip()
    
    # Phase 4.2: Injection Check
    is_injection = any(pattern in user_msg.lower() for pattern in INJECTION_PATTERNS)
    
    if not user_msg:
        st.warning("Please enter a message")
    elif is_injection:
        st.warning("Invalid input detected. Please ask about a real company.")
    elif len(user_msg) > 500:
        st.warning("Message too long.")
    else:
        # Business logic: Identify company
        st.session_state.company = guess_company_name(user_msg, st.session_state.company)

        with st.spinner(f"Researching {st.session_state.company}..."):
            try:
                # Phase 2.3 & 3.3: Pass session_id and handle diff_result
                reply, plan, history, diff_result = asyncio.run(
                    generate_agent_reply(
                        user_message=user_msg,
                        company_name=st.session_state.company,
                        current_plan=st.session_state.plan,
                        chat_history=st.session_state.chat_history,
                        session_id=st.session_state.session_id
                    )
                )
                st.session_state.plan = plan
                st.session_state.chat_history = history
                st.session_state.diff_result = diff_result
            except Exception as e:
                logger.error(f"UI Error: {e}", exc_info=True)
                st.error("I encountered an error. Please check the logs.")

# Display Chat
for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Display Structured Plan
if st.session_state.plan:
    st.markdown("---")
    st.markdown(f"### 📄 Structured Summary: {st.session_state.company}")
    
    # Phase 1 Bug Fix: Replace to_dict() with model_dump()
    data = st.session_state.plan.model_dump()
    
    # Display in columns for better UI
    cols = st.columns(2)
    
    # Exclude technical fields
    keys = [k for k in data.keys() if k not in ["company_name"]]
    
    for i, key in enumerate(keys):
        with cols[i % 2]:
            st.markdown(f"**{key.replace('_', ' ').title()}**")
            st.markdown(format_section_text(data[key], key))
