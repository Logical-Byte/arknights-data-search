import re

def clean_markup(text: str | None) -> str | None:
    if text is None:
        return None
    return re.sub(r'<[^>]*>', '', text)

def replace_description_placeholders(description: str, blackboard: dict) -> str:
    if not description:
        return ""
    
    def replace_match(match):
        full_key = match.group(1)
        format_spec = match.group(2)
        
        value = blackboard.get(full_key) # Direct lookup in the flat blackboard

        if value is None:
            # If key not found, return original placeholder
            return match.group(0)

        # Apply formatting
        if format_spec:
            try:
                if '%' in format_spec:
                    precision_match = re.search(r'\.(\d+)', format_spec)
                    precision = int(precision_match.group(1)) if precision_match else 0
                    
                    percent_val = value * 100
                    return f"{percent_val:.{precision}f}%"
                else:
                    return f"{value:{format_spec}}"
            except ValueError:
                return match.group(0) # Fallback if formatting fails
        else:
            # Default formatting: remove trailing .0 for floats
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)

    # Correct regex to match single braces like {key} or {key:fmt}
    processed_description = re.sub(r'\{([a-zA-Z0-9_\.@\[\]]+)(?::([^{}]+))?}', replace_match, description)
    return processed_description

def parse_handbook_info(story_text: str):
    gender_match = re.search(r"【性别】(.*?)\n", story_text)
    birth_place_match = re.search(r"【出身地】(.*?)\n", story_text)
    race_match = re.search(r"【种族】(.*?)\n", story_text)

    return {
        "gender": gender_match.group(1).strip() if gender_match else None,
        "birth_place": birth_place_match.group(1).strip() if birth_place_match else None,
        "race": race_match.group(1).strip() if race_match else None,
    }