import streamlit as st
from agent.agent_core import generate_agent_reply
from agent.tools import research_company

st.set_page_config(page_title="Company Research Assistant", layout="wide")

st.title("💼 Company Research Assistant")

# session data
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "plan" not in st.session_state:
    st.session_state.plan = None

if "company" not in st.session_state:
    st.session_state.company = ""

# sidebar actions
with st.sidebar:
    st.header("Actions")

    if st.button("🔄 Regenerate Plan"):
        st.session_state.plan = None
        st.session_state.chat_history = []
        st.success("Plan cleared. Type a message to regenerate.")

    if st.button("🌐 Refresh Research"):
        if st.session_state.company.strip():
            data = research_company(st.session_state.company)
            st.info("New research fetched. Type something to update the plan.")
        else:
            st.error("Enter a company name first.")

    st.markdown("---")
    st.markdown("Made for interview use.")

# company name input
company = st.text_input("Company Name", value=st.session_state.company)
msg = st.chat_input("Ask about the company...")

if msg:
    if not company.strip():
        st.error("Enter company name first.")
    else:
        st.session_state.company = company

        with st.spinner("Working..."):
            reply, plan, history = generate_agent_reply(
                user_message=msg,
                company_name=company,
                current_plan=st.session_state.plan,
                chat_history=st.session_state.chat_history
            )
            st.session_state.plan = plan
            st.session_state.chat_history = history

# show chat
for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# show plan
if st.session_state.plan:
    st.subheader("📄 Account Plan")

    d = st.session_state.plan.to_dict()

    for sec, val in d.items():
        with st.container():
            st.markdown(
                f"""
                <div style="padding: 15px; margin-bottom: 15px;
                border-radius: 12px; border: 1px solid rgba(0,0,0,0.1);
                background-color: rgba(255,255,255,0.02);">
                    <h4>{sec.replace('_',' ').title()}</h4>
                    <p>{val if val else '_(empty)_'}<p>
                </div>
                """,
                unsafe_allow_html=True
            )
