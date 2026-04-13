from typing import Dict

def diff_plans(old: Dict[str, str], new: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    Compares two research plans and returns a dictionary of changed sections.
    """
    sections = [
        "overview", "products_services", "market_position", 
        "competitors", "financial_snapshot", "key_contacts", 
        "opportunities", "risks", "recommended_actions"
    ]
    
    diff = {}
    
    for section in sections:
        old_val = str(old.get(section, "")).strip()
        new_val = str(new.get(section, "")).strip()
        
        if old_val != new_val:
            diff[section] = {
                "old": old_val,
                "new": new_val
            }
            
    return diff
