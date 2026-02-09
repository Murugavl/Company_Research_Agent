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


def guess_company_name(message, current):
    if current:
        return current
    text = message.strip().lower()
    if "about" in text:
        try:
            i = text.index("about") + len("about")
            return message[i:].strip(" :,-") or message
        except:
            return message
    return message


def format_section_text(text, section_name=None):
    if not text:
        return "_(empty)_"

    raw = str(text).strip()

    def cap(s):
        return s[:1].upper() + s[1:] if s else s

    if section_name == "products_services":
        t = raw.replace("[", "").replace("]", "").replace("{", "").replace("}", "")
        t = t.replace("'", "").strip()
        parts = re.split(r"\s{2,}|\n", t)
        out = []
        for p in parts:
            p = p.strip().strip(",")
            if not p:
                continue
            if ":" in p and "→" not in p:
                left, right = p.split(":", 1)
                out.append(f"{left.strip()} → {right.strip()}")
            else:
                out.append(p)
        return "\n".join(out)

    if section_name in {"competitors", "opportunities", "risks", "recommended_actions"}:

        if raw.startswith("[") and raw.endswith("]"):
            try:
                import ast
                items = ast.literal_eval(raw)
                cleaned_items = []
                for i in items:
                    line = str(i).strip()
                    line = line.replace("e g", "e.g.").replace("(e g", "(e.g.")
                    cleaned_items.append(f"- {line}")
                return "\n".join(cleaned_items)
            except:
                pass

        lines = []
        for line in raw.split("\n"):
            cleaned = line.strip().strip("-• ").strip()
            if cleaned:
                cleaned = cleaned.replace("e g", "e.g.").replace("(e g", "(e.g.")
                cleaned = re.sub(r"\s+", " ", cleaned)
                lines.append(f"- {cleaned}")

        return "\n".join(lines)



    if section_name in {
        "overview",
        "market_position",
        "financial_snapshot",
        "key_contacts"
    }:
        return cap(raw.replace("\n", " ").strip())

    return cap(raw)


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
    # Input validation
    user_msg = user_msg.strip()

    if not user_msg:
        st.warning("Please enter a message")
    elif len(user_msg) > 500:
        st.warning("Message is too long. Please keep it under 500 characters.")
    else:
        st.session_state.company = guess_company_name(user_msg, st.session_state.company)

        with st.spinner("Working..."):
            try:
                reply, plan, history = generate_agent_reply(
                    user_message=user_msg,
                    company_name=st.session_state.company,
                    current_plan=st.session_state.plan,
                    chat_history=st.session_state.chat_history,
                )
                st.session_state.plan = plan
                st.session_state.chat_history = history
                logger.info(f"Successfully processed message for company: {st.session_state.company}")
            except Exception as e:
                logger.error(f"Error processing user message: {e}", exc_info=True)
                error_message = "I apologize, but I encountered an error while processing your request. Please try again."
                st.session_state.chat_history.append({"role": "user", "content": user_msg})
                st.session_state.chat_history.append({"role": "assistant", "content": error_message})
                st.error(error_message)


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
        st.markdown(f"**{key.replace('_', ' ').title()}**")
        st.markdown(format_section_text(value, key))
        st.markdown("")
