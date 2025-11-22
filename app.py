import streamlit as st
from agent.agent_core import generate_agent_reply

st.set_page_config(page_title="Company Research Assistant")

st.title("Company Research Assistant")

# session placeholders
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "plan" not in st.session_state:
    st.session_state.plan = None

if "company" not in st.session_state:
    st.session_state.company = ""

# user enters company name once
company = st.text_input("Company Name", value=st.session_state.company)

# chat box
msg = st.chat_input("Ask anything about the company...")

if msg:
    if not company.strip():
        st.error("Enter a company name first.")
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

# show plan at bottom
if st.session_state.plan:
    st.subheader("Account Plan")
    d = st.session_state.plan.to_dict()
    for sec, val in d.items():
        st.markdown(f"**{sec.replace('_', ' ').title()}**")
        st.markdown(val if val else "_(empty)_")
        st.markdown("---")
