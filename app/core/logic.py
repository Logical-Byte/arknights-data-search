from typing import List, Dict, Optional
from app.models import CharacterAttributes
from app.config import PROFESSION_MAP, POSITION_MAP

def validate_calculation_params(char_info: dict, elite: int = None, level: int = None, potential: int = None):
    """
    Validates if the provided calculation parameters are within valid ranges for the specific operator.
    Raises ValueError with a detailed message if invalid.
    """
    phases = char_info.get("phases", [])
    operator_name = char_info.get("name", "Unknown")

    # 1. Elite Phase Validation
    max_elite = len(phases) - 1
    if elite is not None:
        if elite < 0:
             raise ValueError(f"Elite phase cannot be negative.")
        if elite > max_elite:
            raise ValueError(f"Operator '{operator_name}' cannot reach Elite {elite}. Max Elite phase is {max_elite}.")
    
    # Determine target elite for level validation
    target_elite = elite if elite is not None else max_elite
    # Clamp target_elite to safe bounds just for looking up max_level (in case elite was None but logic above ensures safety)
    safe_elite_idx = max(0, min(target_elite, max_elite))
    
    current_phase = phases[safe_elite_idx]
    max_level_in_phase = current_phase.get("maxLevel", 1)

    # 2. Level Validation
    if level is not None:
        if level <= 0:
             raise ValueError(f"Level must be greater than 0.")
        if level > max_level_in_phase:
            raise ValueError(f"Operator '{operator_name}' at Elite {target_elite} cannot reach Level {level}. Max Level is {max_level_in_phase}.")

    # 3. Potential Validation
    if potential is not None:
        potential_ranks = char_info.get("potentialRanks", [])
        if potential < 0:
             raise ValueError(f"Potential cannot be negative.")
        if potential > len(potential_ranks):
             raise ValueError(f"Operator '{operator_name}' does not have {potential} potential levels. Max potential upgrade count is {len(potential_ranks)}.")

def calculate_attributes(char_info: dict, elite: int = None, level: int = None, trust: int = 100, potential: int = 5) -> CharacterAttributes:
    phases = char_info.get("phases", [])
    if not phases:
        return None

    if elite is None:
        elite = len(phases) - 1
    
    elite = max(0, min(elite, len(phases) - 1))
    current_phase = phases[elite]
    max_level_in_phase = current_phase.get("maxLevel", 1)

    if level is None:
        level = max_level_in_phase
    
    level = max(1, min(level, max_level_in_phase))

    # 1. Base Attributes (Interpolation)
    key_frames = current_phase.get("attributesKeyFrames", [])
    base_stats = {}
    
    if not key_frames:
        pass 
    elif len(key_frames) == 1:
        base_stats = key_frames[0]["data"]
    else:
        lower_frame = key_frames[0]
        upper_frame = key_frames[-1]
        
        for frame in key_frames:
            if frame["level"] <= level:
                lower_frame = frame
            if frame["level"] >= level:
                upper_frame = frame
                break 
        
        if lower_frame["level"] == upper_frame["level"]:
            base_stats = lower_frame["data"]
        else:
            ratio = (level - lower_frame["level"]) / (upper_frame["level"] - lower_frame["level"])
            for key in lower_frame["data"]:
                val_lower = lower_frame["data"].get(key, 0)
                val_upper = upper_frame["data"].get(key, 0)
                if isinstance(val_lower, (int, float)) and isinstance(val_upper, (int, float)):
                     val = val_lower + (val_upper - val_lower) * ratio
                     base_stats[key] = val
                else:
                    base_stats[key] = val_lower

    # 2. Trust Bonus (Interpolation 0-100)
    trust_stats = {"maxHp": 0, "atk": 0, "def": 0, "magicResistance": 0}
    favor_frames = char_info.get("favorKeyFrames", [])
    if favor_frames:
        calc_trust = max(0, min(trust, 100))
        lower_f = favor_frames[0]
        upper_f = favor_frames[-1]
        
        for f in favor_frames:
            if f["level"] <= calc_trust:
                lower_f = f
            if f["level"] >= calc_trust:
                upper_f = f
                break
        
        if lower_f["level"] == upper_f["level"]:
             trust_stats = lower_f["data"]
        else:
            ratio = (calc_trust - lower_f["level"]) / (upper_f["level"] - lower_f["level"])
            for key in ["maxHp", "atk", "def", "magicResistance"]:
                val_l = lower_f["data"].get(key, 0)
                val_u = upper_f["data"].get(key, 0)
                trust_stats[key] = val_l + (val_u - val_l) * ratio

    # 3. Potential Bonus
    pot_stats = {"maxHp": 0, "atk": 0, "def": 0, "magicResistance": 0, "cost": 0, "blockCnt": 0, "respawnTime": 0, "attackSpeed": 0}
    potential_ranks = char_info.get("potentialRanks", [])
    valid_potential_idx = max(0, min(potential, len(potential_ranks)))
    
    for i in range(valid_potential_idx):
        pot = potential_ranks[i]
        if pot["buff"]:
            for mod in pot["buff"]["attributes"]["attributeModifiers"]:
                attr_type = mod["attributeType"]
                value = mod["value"]
                if attr_type == 0: pot_stats["maxHp"] += value
                elif attr_type == 1: pot_stats["atk"] += value
                elif attr_type == 2: pot_stats["def"] += value
                elif attr_type == 3: pot_stats["magicResistance"] += value
                elif attr_type == 21: pot_stats["cost"] += value
                elif attr_type == 22: pot_stats["blockCnt"] += value
                elif attr_type == 23: pot_stats["respawnTime"] += value
                elif attr_type == 7: pot_stats["attackSpeed"] += value

    final_stats = {
        "maxHp": int(base_stats.get("maxHp", 0) + trust_stats.get("maxHp", 0) + pot_stats["maxHp"]),
        "atk": int(base_stats.get("atk", 0) + trust_stats.get("atk", 0) + pot_stats["atk"]),
        "def": int(base_stats.get("def", 0) + trust_stats.get("def", 0) + pot_stats["def"]),
        "magicResistance": base_stats.get("magicResistance", 0.0) + trust_stats.get("magicResistance", 0.0) + pot_stats["magicResistance"],
        "cost": int(base_stats.get("cost", 0) + pot_stats["cost"]),
        "blockCnt": int(base_stats.get("blockCnt", 0) + pot_stats["blockCnt"]),
        "moveSpeed": base_stats.get("moveSpeed", 1.0),
        "attackSpeed": base_stats.get("attackSpeed", 100.0) + pot_stats["attackSpeed"],
        "baseAttackTime": base_stats.get("baseAttackTime", 1.0),
        "respawnTime": int(base_stats.get("respawnTime", 0) + pot_stats["respawnTime"])
    }
    
    return CharacterAttributes(**final_stats)


