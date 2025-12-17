import json
import re
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

# --- Global Variables & Constants ---
LOCAL_DATA_PATH = Path("arknights-game-data/zh_CN/gamedata/excel")
operators_data = []
app = FastAPI(
    title="Arknights Game Data API",
    description="An API to query Arknights operator data from the local game data files."
)

# --- Pydantic Models ---
class CharacterAttributes(BaseModel):
    maxHp: int
    atk: int
    def_: int
    magicResistance: float
    cost: int
    blockCnt: int
    moveSpeed: float
    attackSpeed: float
    baseAttackTime: float
    respawnTime: int

class SkillLevel(BaseModel):
    level: str
    name: Optional[str] = None
    description: Optional[str] = None
    spCost: int
    initialSp: int
    duration: float

class Skill(BaseModel):
    skillId: str
    levels: List[SkillLevel]

class PotentialInfo(BaseModel):
    rank: str
    description: str

class Operator(BaseModel):
    charId: str
    name: str
    description: Optional[str] = None
    canUseGeneralPotentialItem: bool
    potentialItemId: Optional[str] = None
    nationId: Optional[str] = None
    groupId: Optional[str] = None
    teamId: Optional[str] = None
    displayNumber: Optional[str] = None
    appellation: str
    position: str
    tagList: Optional[List[str]] = None
    itemUsage: Optional[str] = None
    itemDesc: Optional[str] = None
    itemObtainApproach: Optional[str] = None
    isNotObtainable: bool
    isSpChar: bool
    maxPotentialLevel: int
    rarity: str
    profession: str
    subProfessionId: str
    gender: Optional[str] = None
    birth_place: Optional[str] = None
    race: Optional[str] = None
    attributes: Optional[CharacterAttributes] = None
    skills: Optional[List[Skill]] = None
    potentials: Optional[List[PotentialInfo]] = None

# --- Data Loading and Parsing ---
def clean_markup(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    return re.sub(r'<[^>]*>', '', text)

def replace_skill_description_placeholders(description: str, blackboard: dict) -> str:
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
                    precision_match = re.search(r'\\.(\\d+)', format_spec)
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

    processed_description = re.sub(r'{([a-zA-Z0-9_\.@\[\]]+)(?::([^{}]+))?}', replace_match, description)
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

def load_data():
    print(f"Loading data from local path: {LOCAL_DATA_PATH}")
    global operators_data

    char_table_path = LOCAL_DATA_PATH / "character_table.json"
    handbook_path = LOCAL_DATA_PATH / "handbook_info_table.json"
    skill_table_path = LOCAL_DATA_PATH / "skill_table.json"
    favor_table_path = LOCAL_DATA_PATH / "favor_table.json"

    try:
        with open(char_table_path, 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        with open(handbook_path, 'r', encoding='utf-8') as f:
            handbook_data = json.load(f).get("handbookDict", {})
        with open(skill_table_path, 'r', encoding='utf-8') as f:
            skill_data = json.load(f)
        with open(favor_table_path, 'r', encoding='utf-8') as f:
            favor_data = json.load(f).get("favorFrames", {})
    except Exception as e:
        print(f"Failed to load or parse local data files: {e}")
        operators_data = []
        return

    temp_operators_data = []
    for char_id, char_info in character_data.items():
        if not isinstance(char_info, dict) or char_info.get("subProfessionId") == "notchar": continue
        char_info["charId"] = char_id
        char_info["description"] = clean_markup(char_info.get("description"))
        
        # --- Calculate Max Stats ---
        final_phase = char_info["phases"][-1]
        max_level_stats = final_phase["attributesKeyFrames"][-1]["data"]
        
        trust_stats = {"maxHp": 0, "atk": 0, "def": 0, "magicResistance": 0}
        if char_info.get("favorKeyFrames"):
            favor_frame = char_info["favorKeyFrames"][-1]["data"]
            trust_stats.update(favor_frame)

        # Base stats at max level
        final_stats = {
            "maxHp": max_level_stats["maxHp"] + trust_stats["maxHp"],
            "atk": max_level_stats["atk"] + trust_stats["atk"],
            "def": max_level_stats["def"] + trust_stats["def"],
            "magicResistance": max_level_stats["magicResistance"] + trust_stats["magicResistance"],
            "cost": max_level_stats["cost"],
            "blockCnt": max_level_stats["blockCnt"],
            "moveSpeed": max_level_stats["moveSpeed"],
            "attackSpeed": max_level_stats["attackSpeed"],
            "baseAttackTime": max_level_stats["baseAttackTime"],
            "respawnTime": max_level_stats["respawnTime"]
        }

        # Add potential bonuses
        for pot in char_info.get("potentialRanks", []):
            if pot["buff"]:
                attr_type = pot["buff"]["attributes"]["attributeModifiers"][0]["attributeType"]
                value = pot["buff"]["attributes"]["attributeModifiers"][0]["value"]
                if attr_type == 0: final_stats["maxHp"] += value
                elif attr_type == 1: final_stats["atk"] += value
                elif attr_type == 2: final_stats["def"] += value
                elif attr_type == 3: final_stats["magicResistance"] += value
                elif attr_type == 21: final_stats["cost"] -= value
                elif attr_type == 22: final_stats["blockCnt"] += value
                elif attr_type == 23: final_stats["respawnTime"] -= value

        char_info["attributes"] = CharacterAttributes(def_=final_stats.pop("def"), **final_stats)

        # --- Add Handbook Info ---
        handbook_info = handbook_data.get(char_id)
        if handbook_info and handbook_info.get("storyTextAudio"):
            story_text = handbook_info["storyTextAudio"][0]["stories"][0]["storyText"]
            parsed_info = parse_handbook_info(story_text)
            char_info.update(parsed_info)

        # --- Add Skill Info ---
        operator_skills = []
        if char_info.get("skills"):
            for skill_ref in char_info["skills"]:
                skill_id = skill_ref.get("skillId")
                if skill_id and skill_id in skill_data:
                    full_skill_info = skill_data[skill_id]
                    skill_levels = []
                    for i, level_data in enumerate(full_skill_info.get("levels", [])):
                        blackboard = {item["key"]: item["value"] for item in level_data.get("blackboard", [])}
                        
                        level_str = f"专{i - 6}" if i > 6 else str(i + 1)
                        skill_description = clean_markup(level_data.get("description"))
                        # Pass blackboard directly, no complex preprocessing needed for @ keys
                        filled_description = replace_skill_description_placeholders(skill_description, blackboard)

                        skill_levels.append(
                            SkillLevel(
                                level=level_str,
                                name=clean_markup(level_data.get("name")),
                                description=filled_description,
                                spCost=level_data.get("spData", {}).get("spCost", 0),
                                initialSp=level_data.get("spData", {}).get("initSp", 0),
                                duration=blackboard.get("duration", 0.0)
                            )
                        )
                    operator_skills.append(Skill(skillId=skill_id, levels=skill_levels))
        char_info["skills"] = operator_skills

        # --- Add Potential Info ---
        operator_potentials = []
        if char_info.get("potentialRanks"):
            for i, potential_rank in enumerate(char_info["potentialRanks"]):
                if potential_rank and potential_rank.get("description"):
                    rank_str = f"潜能{i + 2}"
                    operator_potentials.append(PotentialInfo(rank=rank_str, description=clean_markup(potential_rank["description"])))
        char_info["potentials"] = operator_potentials

        temp_operators_data.append(char_info)
    
    operators_data.clear()
    operators_data.extend(temp_operators_data)
    print(f"Data loaded successfully. {len(operators_data)} operators.")

# --- FastAPI Events and Endpoints ---
@app.on_event("startup")
def startup_event():
    print("API starting up. Performing initial data load...")
    load_data()
    print("Startup data load complete.")

@app.get("/")
def read_root():
    return {"message": "欢迎使用明日方舟干员数据查询 API"}

def calculate_attributes(char_info: dict, elite: int = None, level: int = None, trust: int = 100, potential: int = 5) -> CharacterAttributes:
    phases = char_info.get("phases", [])
    if not phases:
        return None

    # Default to max elite and max level if not provided
    if elite is None:
        elite = len(phases) - 1
    
    # Validate elite
    elite = max(0, min(elite, len(phases) - 1))
    current_phase = phases[elite]
    max_level_in_phase = current_phase.get("maxLevel", 1)

    if level is None:
        level = max_level_in_phase
    
    # Validate level
    level = max(1, min(level, max_level_in_phase))

    # 1. Base Attributes (Interpolation)
    key_frames = current_phase.get("attributesKeyFrames", [])
    base_stats = {}
    
    if not key_frames:
        pass # Should not happen for valid data
    elif len(key_frames) == 1:
        base_stats = key_frames[0]["data"]
    else:
        # Find two frames to interpolate between
        lower_frame = key_frames[0]
        upper_frame = key_frames[-1]
        
        for frame in key_frames:
            if frame["level"] <= level:
                lower_frame = frame
            if frame["level"] >= level:
                upper_frame = frame
                break # Found the immediate upper bound
        
        if lower_frame["level"] == upper_frame["level"]:
            base_stats = lower_frame["data"]
        else:
            # Linear Interpolation
            ratio = (level - lower_frame["level"]) / (upper_frame["level"] - lower_frame["level"])
            for key in lower_frame["data"]:
                val_lower = lower_frame["data"].get(key, 0)
                val_upper = upper_frame["data"].get(key, 0)
                # Some stats like cost/blockCnt don't interpolate, but usually they are const across frames in a phase or handle differently.
                # However, numeric stats do interpolate.
                if isinstance(val_lower, (int, float)) and isinstance(val_upper, (int, float)):
                     val = val_lower + (val_upper - val_lower) * ratio
                     base_stats[key] = val
                else:
                    base_stats[key] = val_lower # Fallback for non-numerics

    # 2. Trust Bonus (Interpolation 0-100)
    trust_stats = {"maxHp": 0, "atk": 0, "def": 0, "magicResistance": 0}
    favor_frames = char_info.get("favorKeyFrames", [])
    if favor_frames:
        # Trust caps at 100 for stats
        calc_trust = max(0, min(trust, 100))
        # Usually frames are at 0 and 100
        lower_f = favor_frames[0]
        upper_f = favor_frames[-1] # Assuming sorted
        
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
    # potential is 0-5 (representing Potential 1-6)
    pot_stats = {"maxHp": 0, "atk": 0, "def": 0, "magicResistance": 0, "cost": 0, "blockCnt": 0, "respawnTime": 0, "attackSpeed": 0}
    potential_ranks = char_info.get("potentialRanks", [])
    # Validate potential index
    valid_potential_idx = max(0, min(potential, len(potential_ranks))) # Allow 0 to max available
    
    for i in range(valid_potential_idx):
        pot = potential_ranks[i]
        if pot["buff"]:
            for mod in pot["buff"]["attributes"]["attributeModifiers"]:
                attr_type = mod["attributeType"]
                value = mod["value"]
                # Mapping attributeType to keys
                if attr_type == 0: pot_stats["maxHp"] += value
                elif attr_type == 1: pot_stats["atk"] += value
                elif attr_type == 2: pot_stats["def"] += value
                elif attr_type == 3: pot_stats["magicResistance"] += value
                elif attr_type == 21: pot_stats["cost"] += value # Usually negative
                elif attr_type == 22: pot_stats["blockCnt"] += value
                elif attr_type == 23: pot_stats["respawnTime"] += value # Usually negative
                elif attr_type == 7: pot_stats["attackSpeed"] += value

    # Aggregate Final Stats
    final_stats = {
        "maxHp": int(base_stats.get("maxHp", 0) + trust_stats.get("maxHp", 0) + pot_stats["maxHp"]),
        "atk": int(base_stats.get("atk", 0) + trust_stats.get("atk", 0) + pot_stats["atk"]),
        "def_": int(base_stats.get("def", 0) + trust_stats.get("def", 0) + pot_stats["def"]),
        "magicResistance": base_stats.get("magicResistance", 0.0) + trust_stats.get("magicResistance", 0.0) + pot_stats["magicResistance"],
        "cost": int(base_stats.get("cost", 0) + pot_stats["cost"]),
        "blockCnt": int(base_stats.get("blockCnt", 0) + pot_stats["blockCnt"]),
        "moveSpeed": base_stats.get("moveSpeed", 1.0),
        "attackSpeed": base_stats.get("attackSpeed", 100.0) + pot_stats["attackSpeed"],
        "baseAttackTime": base_stats.get("baseAttackTime", 1.0),
        "respawnTime": int(base_stats.get("respawnTime", 0) + pot_stats["respawnTime"])
    }
    
    return CharacterAttributes(**final_stats)

@app.get("/api/operators", response_model=List[Operator])
def search_operators(
    name: Optional[str] = Query(None, title="名称", description="干员的名称 (支持模糊搜索)"),
    profession: Optional[str] = Query(None, title="职业", description="干员的职业"),
    sub_profession: Optional[str] = Query(None, title="分支", description="干员的子职业"),
    rarity: Optional[int] = Query(None, title="稀有度", ge=1, le=6, description="干员的稀有度 (1-6)"),
    position: Optional[str] = Query(None, title="位置", description="干员的位置 (MELEE or RANGED)"),
    tag: Optional[str] = Query(None, title="词缀", description="干员的标签"),
    nation: Optional[str] = Query(None, title="势力", description="干员所属的势力"),
    gender: Optional[str] = Query(None, title="性别", description="干员的性别"),
    birth_place: Optional[str] = Query(None, title="出身地", description="干员的出身地"),
    race: Optional[str] = Query(None, title="种族", description="干员的种族"),
    max_level: Optional[int] = Query(None, title="精英等级过滤", ge=0, le=2, description="筛选能够达到该精英等级的干员 (旧参数)"),
    obtain_approach: Optional[str] = Query(None, title="获取途径", description="干员的获取途径"),
    # New calculation parameters
    elite: Optional[int] = Query(None, title="目标精英阶段", ge=0, le=2, description="计算属性时的精英阶段 (0-2)"),
    level: Optional[int] = Query(None, title="目标等级", ge=1, le=90, description="计算属性时的等级"),
    potential: Optional[int] = Query(5, title="目标潜能", ge=0, le=5, description="计算属性时的潜能等级 (0-5, 0为潜能1, 5为满潜)"),
    trust: Optional[int] = Query(100, title="目标信赖", ge=0, le=200, description="计算属性时的信赖值 (0-200, 属性加成100封顶)")
):
    results = operators_data

    if name:
        results = [op for op in results if op.get("name") and name.lower() in op.get("name").lower()]

    if profession:
        results = [op for op in results if op.get("profession") and op.get("profession").lower() == profession.lower()]
    
    if sub_profession:
        results = [op for op in results if op.get("subProfessionId") and op.get("subProfessionId").lower() == sub_profession.lower()]

    if rarity:
        rarity_str = f"TIER_{rarity}"
        results = [op for op in results if op.get("rarity") == rarity_str]

    if position:
        results = [op for op in results if op.get("position") and op.get("position").lower() == position.lower()]

    if tag:
        results = [op for op in results if op.get("tagList") and tag.lower() in [t.lower() for t in op["tagList"]]]
    
    if nation:
        results = [op for op in results if op.get("nationId") and op.get("nationId").lower() == nation.lower()]

    if gender:
        results = [op for op in results if op.get("gender") and op.get("gender").lower() == gender.lower()]

    if birth_place:
        results = [op for op in results if op.get("birth_place") and op.get("birth_place").lower() == birth_place.lower()]
    
    if race:
        results = [op for op in results if op.get("race") and op.get("race").lower() == race.lower()]
    
    if max_level is not None:
        results = [op for op in results if len(op.get("phases", [])) > max_level]

    if obtain_approach:
        results = [op for op in results if op.get("itemObtainApproach") and op.get("itemObtainApproach").lower() == obtain_approach.lower()]

    # Dynamic Attribute Calculation
    # We create a new list of Operator objects (or dicts) to avoid modifying the global cache
    final_results = []
    for op in results:
        # Shallow copy to avoid side effects on the global operators_data
        op_copy = op.copy()
        
        # Calculate attributes based on parameters or default to max
        # If parameters are not provided, calculate_attributes handles defaults (Max/Max)
        # Note: If elite/level are None, it calculates max stats for that operator.
        # This overwrites the statically loaded 'attributes' with a dynamically calculated one.
        op_copy["attributes"] = calculate_attributes(op, elite, level, trust, potential)
        final_results.append(op_copy)

    return final_results
