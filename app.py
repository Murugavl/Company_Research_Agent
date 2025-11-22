import re
import streamlit as st
from agent.agent_core import generate_agent_reply

st.set_page_config(page_title="Company Research Assistant", layout="wide")

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
            idx = lower.index("about") + len("about")
            after = text[idx:].strip(" :,-")
            return after if after else text
        except Exception:
            return text

    return text


def format_section_text(text):
    if text is None or text == "":
        return "_(empty)_"

    # if the model or tools gave a real list
    if isinstance(text, list):
        cleaned_items = []
        for item in text:
            s = str(item).strip()
            s = s.lstrip("-• ").strip()
            if s:
                cleaned_items.append(f"- {s}")
        return "\n".join(cleaned_items) if cleaned_items else "_(empty)_"

    t = str(text).strip()

    # handle python-style list as string: "['A', 'B', 'C']"
    if t.startswith("[") and t.endswith("]"):
        try:
            import ast

            arr = ast.literal_eval(t)
            if isinstance(arr, list):
                cleaned_items = []
                for item in arr:
                    s = str(item).strip()
                    s = s.lstrip("-• ").strip()
                    if s:
                        cleaned_items.append(f"- {s}")
                if cleaned_items:
                    return "\n".join(cleaned_items)
        except Exception:
            pass

    # inline " - " separators -> bullets
    if " - " in t and "\n" not in t:
        parts = [p.strip() for p in t.split(" - ") if p.strip()]
        if len(parts) > 1:
            return "\n".join(f"- {p}" for p in parts)

    # put numbered items on new lines if needed
    t = re.sub(r"\s+(\d\.)", r"\n\1", t)

    return t


st.title("💼 Company Research Assistant")

with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Reset Conversation"):
        st.session_state.chat_history = []
        st.session_state.plan = None
        st.session_state.company = ""
        st.success("Conversation and structured summary cleared.")

user_msg = st.chat_input("Ask about any company...")

if user_msg:
    st.session_state.company = guess_company_name(user_msg, st.session_state.company)

    with st.spinner("Working..."):
        reply, plan, history = generate_agent_reply(
            user_message=user_msg,
            company_name=st.session_state.company,
            current_plan=st.session_state.plan,
            chat_history=st.session_state.chat_history,
        )
        st.session_state.plan = plan
        st.session_state.chat_history = history

for m in st.session_state.chat_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if st.session_state.plan:
    st.markdown("---")
    st.markdown("### 📄 Structured Summary")

    data = st.session_state.plan.to_dict()

    for key, value in data.items():
        if key.lower() == "company_name":
            continue

        title = key.replace("_", " ").title()
        st.markdown(f"**{title}**")
        st.markdown(format_section_text(value))
        st.markdown("")  # small spacing
