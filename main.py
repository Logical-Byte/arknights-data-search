import json
import re
import time
import logging
import subprocess
import threading
import os
from typing import List, Optional

from fastapi import FastAPI, Query
from pydantic import BaseModel

# --- Configuration Loading ---
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    logging.error("config.json not found! Please create it.")
    # Default config for fallback
    config = {
        "active_source": "Logical-Byte",
        "sources": {
            "Logical-Byte": {
                "url": "https://github.com/Logical-Byte/arknights-game-data.git",
                "path": "arknights-game-data-logical-byte"
            }
        },
        "update_interval_seconds": 3600
    }

# --- Global Variables ---
operators_data = []
app = FastAPI(
    title="Arknights Game Data API",
    description="An API to query Arknights operator data from various community-maintained data sources."
)

# --- Pydantic Models ---
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

def load_data(data_path: str):
    logging.info(f"Loading data from path: {data_path}")
    global operators_data
    
    char_table_path = os.path.join(data_path, "zh_CN", "gamedata", "excel", "character_table.json")
    handbook_path = os.path.join(data_path, "zh_CN", "gamedata", "excel", "handbook_info_table.json")

    if not os.path.exists(char_table_path) or not os.path.exists(handbook_path):
        logging.error(f"Data files not found in {data_path}. Please ensure the data source is cloned and valid.")
        operators_data = []
        return

    temp_operators_data = []
    with open(char_table_path, "r", encoding="utf-8") as f:
        character_data = json.load(f)

    with open(handbook_path, "r", encoding="utf-8") as f:
        handbook_data = json.load(f).get("handbookDict", {})

    for char_id, char_info in character_data.items():
        char_info["charId"] = char_id
        handbook_info = handbook_data.get(char_id)
        if handbook_info and handbook_info.get("storyTextAudio"):
            story_text = handbook_info["storyTextAudio"][0]["stories"][0]["storyText"]
            parsed_info = parse_handbook_info(story_text)
            char_info.update(parsed_info)

        temp_operators_data.append(char_info)
    
    operators_data.clear()
    operators_data.extend(temp_operators_data)
    logging.info(f"Data loaded successfully. {len(operators_data)} operators.")

# --- Background Update Task ---
def get_active_source_info():
    active_key = config.get("active_source", "Kengou")
    return config["sources"].get(active_key)

def manage_data_repository():
    source_info = get_active_source_info()
    if not source_info:
        logging.error(f"Active source '{config.get('active_source')}' not found in config.json.")
        return False, None

    data_path = source_info["path"]
    data_url = source_info["url"]

    if os.path.exists(data_path):
        logging.info(f"Data directory '{data_path}' exists. Pulling latest changes...")
        command = ["git", "pull"]
        cwd = data_path
    else:
        logging.info(f"Data directory '{data_path}' not found. Cloning from {data_url}...")
        command = ["git", "clone", data_url, data_path]
        cwd = "."
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        # Check if there were changes
        if "Already up to date." in result.stdout or "Cloning into" in result.stdout:
            logging.info("Data is up to date or has been successfully cloned.")
            return True, data_path, False # (success, path, has_changes)
        else:
            logging.info("Data has been updated.")
            return True, data_path, True # (success, path, has_changes)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to {'pull' if os.path.exists(data_path) else 'clone'} repository: {e.stderr}")
        return False, data_path, False

def update_data_periodically():
    while True:
        logging.info("Background task: Checking for new game data updates...")
        success, data_path, has_changes = manage_data_repository()
        if success and has_changes:
            logging.info("Background task: Reloading data due to updates.")
            load_data(data_path)
        
        interval = config.get("update_interval_seconds", 3600)
        time.sleep(interval)

# --- FastAPI Events and Endpoints ---
@app.on_event("startup")
def startup_event():
    logging.info("API starting up. Performing initial data setup...")
    success, data_path, has_changes = manage_data_repository()
    if success:
        load_data(data_path)
    
    update_thread = threading.Thread(target=update_data_periodically, daemon=True)
    update_thread.start()
    logging.info("Started background thread for periodic data updates.")

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
