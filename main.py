import json
import re
import urllib.request
from typing import List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

# --- Global Variables & Constants ---
BASE_URL = "https://torappu.prts.wiki/gamedata/latest/excel/"
operators_data = []
app = FastAPI(
    title="Arknights Game Data API",
    description="An API to query Arknights operator data from various community-maintained data sources."
)

# --- Pydantic Models ---
class SkillLevel(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    spCost: int
    initialSp: int
    duration: float

class Skill(BaseModel):
    skillId: str
    levels: List[SkillLevel]

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
    skills: Optional[List[Skill]] = None

# --- Data Loading and Parsing ---
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
    print(f"Loading data from base URL: {BASE_URL}")
    global operators_data

    char_table_url = BASE_URL + "character_table.json"
    handbook_url = BASE_URL + "handbook_info_table.json"
    skill_table_url = BASE_URL + "skill_table.json"

    try:
        with urllib.request.urlopen(char_table_url) as response:
            character_data = json.load(response)
        with urllib.request.urlopen(handbook_url) as response:
            handbook_data = json.load(response).get("handbookDict", {})
        with urllib.request.urlopen(skill_table_url) as response:
            skill_data = json.load(response)
    except Exception as e:
        print(f"Failed to fetch or parse data from URL: {e}")
        operators_data = []
        return

    temp_operators_data = []
    for char_id, char_info in character_data.items():
        if not isinstance(char_info, dict): continue # Skip non-dict items like "version"
        char_info["charId"] = char_id
        
        # Add handbook info
        handbook_info = handbook_data.get(char_id)
        if handbook_info and handbook_info.get("storyTextAudio"):
            story_text = handbook_info["storyTextAudio"][0]["stories"][0]["storyText"]
            parsed_info = parse_handbook_info(story_text)
            char_info.update(parsed_info)

        # Add skill info
        operator_skills = []
        if char_info.get("skills"):
            for skill_ref in char_info["skills"]:
                skill_id = skill_ref.get("skillId")
                if skill_id and skill_id in skill_data:
                    full_skill_info = skill_data[skill_id]
                    skill_levels = []
                    for level_data in full_skill_info.get("levels", []):
                        blackboard = {item["key"]: item["value"] for item in level_data.get("blackboard", [])}
                        skill_levels.append(
                            SkillLevel(
                                name=level_data.get("name"),
                                description=level_data.get("description"),
                                spCost=level_data.get("spData", {}).get("spCost", 0),
                                initialSp=level_data.get("spData", {}).get("initSp", 0),
                                duration=blackboard.get("duration", 0.0)
                            )
                        )
                    operator_skills.append(Skill(skillId=skill_id, levels=skill_levels))
        char_info["skills"] = operator_skills

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
    obtain_approach: Optional[str] = Query(None, title="获取途径", description="干员的获取途径")
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
    
    if obtain_approach:
        results = [op for op in results if op.get("itemObtainApproach") and op.get("itemObtainApproach").lower() == obtain_approach.lower()]

    return results
