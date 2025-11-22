import re
import streamlit as st
from agent.agent_core import generate_agent_reply

st.set_page_config(page_title="Company Research Assistant", layout="wide")

# session
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "plan" not in st.session_state:
    st.session_state.plan = None

if "company" not in st.session_state:
    st.session_state.company = ""


def guess_company_name(message: str, current: str) -> str:
    if current:
        return current
    text = message.strip()
    lower = text.lower()
    if "about" in lower:
        try:
            after = text[lower.index("about") + len("about") :].strip(" :,-")
            return after if after else text
        except:
            return text
    return text


def format_section_text(text):
    if not text:
        return "_(empty)_"

    # FIX: convert list to bullets
    if isinstance(text, list):
        return "\n".join(f"- {item}" for item in text)

    t = text.strip()

    # add bullet formatting if needed
    t = re.sub(r"\s+(\d\.)", r"\n\1", t)

    return t


st.title("💼 Company Research Assistant")

with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Reset Conversation"):
        st.session_state.plan = None
        st.session_state.company = ""
        st.session_state.chat_history = []
        st.success("Restarted.")

# chat input
msg = st.chat_input("Ask about any company...")

if msg:
    st.session_state.company = guess_company_name(msg, st.session_state.company)

    with st.spinner("Working..."):
        reply, plan, history = generate_agent_reply(
            user_message=msg,
            company_name=st.session_state.company,
            current_plan=st.session_state.plan,
            chat_history=st.session_state.chat_history,
        )
        st.session_state.plan = plan
        st.session_state.chat_history = history

# chat messages
for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# always show structured plan (like before)
if st.session_state.plan:
    st.subheader("📄 Structured Summary")
    d = st.session_state.plan.to_dict()

    for sec, val in d.items():
        with st.container():
            st.markdown(
                f"""
                <div style="
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 12px;
                    border: 1px solid rgba(0,0,0,0.1);
                ">
                    <h4>{sec.replace('_',' ').title()}</h4>
                    <p>{format_section_text(val)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
