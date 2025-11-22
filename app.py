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


def format_section_text(text, section_name=None):
    if not text:
        return "_(empty)_"

    raw = str(text).strip()

    # Special formatting for Products & Services (Category → Items)
    if section_name == "products_services":
        items = []

        # If model returned a Python list
        if isinstance(text, list):
            for entry in text:
                entry = str(entry).strip().replace("\n", ", ")
                if "→" in entry:
                    items.append(entry)
                else:
                    parts = entry.split(":", 1)
                    if len(parts) == 2:
                        cat = parts[0].strip()
                        vals = parts[1].strip()
                        items.append(f"{cat} → {vals}")
        else:
            # If it's a dict-like string: "{'A':'x','B':'y'}"
            if raw.startswith("{") and raw.endswith("}"):
                cleaned = raw.strip("{}")
                for pair in cleaned.split("' '"):
                    pair = pair.replace("{", "").replace("}", "").replace("'", "")
                    if ":" in pair:
                        cat, vals = pair.split(":", 1)
                        items.append(f"{cat.strip()} → {vals.strip().replace(',', ', ')}")
            else:
                # fallback: each line "Category: values"
                lines = raw.split("\n")
                for line in lines:
                    if ":" in line:
                        cat, vals = line.split(":", 1)
                        vals = vals.replace("\n", ", ").strip()
                        items.append(f"{cat.strip()} → {vals}")
        
        return "\n".join(items)

    # The rest of your current function remains unchanged
    # (bullet rules, paragraph rules, etc.)

    bullet_sections = {
        "competitors",
        "opportunities",
        "risks",
        "recommended_actions"
    }

    def cap(s):
        return s[0].upper() + s[1:] if s else s

    if section_name not in bullet_sections:
        cleaned = cap(raw.replace("\n", " ").strip())
        return cleaned

    items = []
    if isinstance(text, list):
        for i in text:
            s = str(i).strip().lstrip("-• ").strip()
            if s:
                items.append(f"- {cap(s)}")
        return "\n".join(items)

    if "," in raw and "\n" not in raw:
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if len(parts) > 1:
            return "\n".join(f"- {cap(p)}" for p in parts)

    if "\n" in raw:
        lines = [l.strip().lstrip("-• ").strip() for l in raw.split("\n") if l.strip()]
        if len(lines) > 1:
            return "\n".join(f"- {cap(l)}" for l in lines)

    return f"- {cap(raw)}"


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
        st.markdown(format_section_text(value, key))
        st.markdown("")
