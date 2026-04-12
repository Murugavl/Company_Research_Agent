import re

def guess_company_name(message: str, current: str) -> str:
    """
    Phase 4.1 Improved Guessing: 
    Detects company names using expanded trigger words and strips filler words.
    """
    if current:
        return current
        
    text = message.strip().lower()
    
    triggers = [
        "about", "research", "analyze", "tell me", "look up", 
        "find", "what is", "who is", "info on", "details on"
    ]
    
    filler = {
        "the", "a", "an", "me", "us", "please", 
        "can", "you", "company", "corp", "inc"
    }
    
    target = ""
    for trigger in triggers:
        if trigger in text:
            try:
                # Find where trigger ends
                idx = text.index(trigger) + len(trigger)
                target = message[idx:].strip(" :,-.?!")
                break
            except:
                continue
    
    if not target:
        target = message.strip()
        
    # Strip filler words
    words = target.split()
    cleaned_words = [w for w in words if w.lower().strip(" ,.!") not in filler]
    
    return " ".join(cleaned_words) or target

def format_section_text(text: str, section_name: str = None) -> str:
    """Format structured text for Streamlit display, handling various data formats."""
    if not text:
        return "_(empty)_"

    raw = str(text).strip()

    def cap(s):
        return s[:1].upper() + s[1:] if s else s

    if section_name == "products_services":
        # Cleaning up string representation if it's leaked through
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
        # Fallback formatting for lists
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
