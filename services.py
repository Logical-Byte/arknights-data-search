import json
import time
import os
import urllib.request
from pathlib import Path
from typing import List, Dict

from models import Operator, CharacterAttributes, SkillLevel, Skill, PotentialInfo, ModuleLevel, Module
from utils import clean_markup, replace_description_placeholders, parse_handbook_info

# Configuration
CACHE_DIR = Path("data_cache")
REMOTE_BASE_URL = "https://torappu.prts.wiki/gamedata/latest/excel/"
CACHE_DURATION = 86400  # 24 hours in seconds

REQUIRED_FILES = [
    "character_table.json",
    "handbook_info_table.json",
    "skill_table.json",
    "favor_table.json",
    "uniequip_table.json",
    "battle_equip_table.json"
]

operators_data: List[dict] = []

def update_cache_if_needed():
    """
    Checks if cache is missing or outdated (older than 24h).
    Downloads files from REMOTE_BASE_URL if needed.
    """
    if not CACHE_DIR.exists():
        print(f"Creating cache directory: {CACHE_DIR}")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    needs_update = False
    
    # Check if any required file is missing
    for filename in REQUIRED_FILES:
        file_path = CACHE_DIR / filename
        if not file_path.exists():
            print(f"File missing in cache: {filename}")
            needs_update = True
            break
    
    # Check if cache is expired (using character_table.json as reference)
    if not needs_update:
        ref_file = CACHE_DIR / "character_table.json"
        if ref_file.exists():
            last_modified = ref_file.stat().st_mtime
            if time.time() - last_modified > CACHE_DURATION:
                print("Cache is older than 24 hours.")
                needs_update = True
    
    if needs_update:
        print("Starting data download from remote source...")
        success = True
        for filename in REQUIRED_FILES:
            url = REMOTE_BASE_URL + filename
            target_path = CACHE_DIR / filename
            try:
                print(f"Downloading {filename}...")
                # Download with a timeout to prevent hanging
                with urllib.request.urlopen(url, timeout=30) as response, open(target_path, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
                success = False
                # If download fails and we don't have a local file, we are in trouble.
                # If we have an old file, we'll just log the error and use the old one.
                if not target_path.exists():
                    print(f"Critical: {filename} missing and download failed.")
        
        if success:
            print("Data cache updated successfully.")
        else:
            print("Cache update finished with errors. Using existing files if available.")
    else:
        print("Cache is up to date.")

def load_data():
    # 1. Update cache before loading
    update_cache_if_needed()

    print(f"Loading data from cache: {CACHE_DIR}")
    global operators_data

    # Paths now point to the CACHE_DIR
    char_table_path = CACHE_DIR / "character_table.json"
    handbook_path = CACHE_DIR / "handbook_info_table.json"
    skill_table_path = CACHE_DIR / "skill_table.json"
    favor_table_path = CACHE_DIR / "favor_table.json"
    uniequip_table_path = CACHE_DIR / "uniequip_table.json"
    battle_equip_table_path = CACHE_DIR / "battle_equip_table.json"

    try:
        with open(char_table_path, 'r', encoding='utf-8') as f:
            character_data = json.load(f)
        with open(handbook_path, 'r', encoding='utf-8') as f:
            handbook_data = json.load(f).get("handbookDict", {})
        with open(skill_table_path, 'r', encoding='utf-8') as f:
            skill_data = json.load(f)
        with open(favor_table_path, 'r', encoding='utf-8') as f:
            favor_data = json.load(f).get("favorFrames", {})
        with open(uniequip_table_path, 'r', encoding='utf-8') as f:
            uniequip_data = json.load(f).get("equipDict", {})
        with open(battle_equip_table_path, 'r', encoding='utf-8') as f:
            battle_equip_data = json.load(f)
    except Exception as e:
        print(f"Failed to load or parse data files: {e}")
        operators_data = []
        return

    # Organize modules by charId
    char_modules_map = {}
    for equip_id, equip_info in uniequip_data.items():
        if not isinstance(equip_info, dict): continue
        char_id = equip_info.get("charId")
        if char_id:
            if char_id not in char_modules_map:
                char_modules_map[char_id] = []
            char_modules_map[char_id].append(equip_info)

    temp_operators_data = []
    for char_id, char_info in character_data.items():
        if not isinstance(char_info, dict) or char_info.get("subProfessionId") == "notchar": continue
        char_info["charId"] = char_id
        char_info["description"] = clean_markup(char_info.get("description"))
        
        # --- Calculate Max Stats ---
        # Note: We still calculate a default 'attributes' set here, but the API can overwrite it dynamically.
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
                        # Pass the original blackboard directly
                        filled_description = replace_description_placeholders(skill_description, blackboard)

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

        # --- Add Module Info ---
        operator_modules = []
        if char_id in char_modules_map:
            for equip_info in char_modules_map[char_id]:
                equip_id = equip_info["uniEquipId"]
                battle_equip = battle_equip_data.get(equip_id)
                
                module_levels = []
                if battle_equip and "phases" in battle_equip:
                    for phase in battle_equip["phases"]:
                        lvl = phase["equipLevel"]
                        
                        # Attributes
                        attrs = {}
                        # Create a base blackboard from attributes for description replacement
                        # This allows descriptions to reference global stat buffs like {attack_speed}
                        base_blackboard = {}
                        for attr in phase.get("attributeBlackboard", []):
                            attrs[attr["key"]] = attr["value"]
                            base_blackboard[attr["key"]] = attr["value"]
                        
                        # Trait/Talent Upgrades
                        trait_up = None
                        talent_up = None
                        
                        for part in phase.get("parts", []):
                            # Trait
                            if part.get("target") == "TRAIT" and part.get("overrideTraitDataBundle"):
                                candidates = part["overrideTraitDataBundle"].get("candidates", [])
                                if candidates:
                                    cand = candidates[-1]
                                    desc_template = cand.get("overrideDescripton") or cand.get("additionalDescription")
                                    if desc_template:
                                        # Merge attribute blackboard with candidate blackboard
                                        cand_blackboard = {item["key"]: item["value"] for item in cand.get("blackboard", [])}
                                        combined_blackboard = {**base_blackboard, **cand_blackboard}
                                        trait_up = replace_description_placeholders(clean_markup(desc_template), combined_blackboard)
                            
                            # Talent
                            if part.get("target") in ["TALENT", "TALENT_DATA_ONLY"] and part.get("addOrOverrideTalentDataBundle"):
                                candidates = part["addOrOverrideTalentDataBundle"].get("candidates", [])
                                if candidates:
                                    cand = candidates[-1]
                                    desc_template = cand.get("upgradeDescription")
                                    if desc_template:
                                        # Merge attribute blackboard with candidate blackboard (though talent parts often lack local blackboard)
                                        # Some talents might reference attributes or have their own params in a different structure?
                                        # Usually talent text is static or uses params. If params are missing in candidate['blackboard'], check if they exist elsewhere.
                                        # For now, we try to use the combined blackboard if candidate has one.
                                        cand_blackboard = {item["key"]: item["value"] for item in cand.get("blackboard", [])} if cand.get("blackboard") else {}
                                        combined_blackboard = {**base_blackboard, **cand_blackboard}
                                        talent_up = replace_description_placeholders(clean_markup(desc_template), combined_blackboard)

                        module_levels.append(ModuleLevel(
                            level=lvl,
                            attributes=attrs,
                            trait_upgrade=trait_up,
                            talent_upgrade=talent_up
                        ))

                operator_modules.append(Module(
                    moduleId=equip_id,
                    name=equip_info["uniEquipName"],
                    description=equip_info.get("uniEquipDesc"),
                    typeIcon=equip_info["typeIcon"],
                    typeName=equip_info["typeName1"] + ("-" + equip_info["typeName2"] if equip_info.get("typeName2") else ""),
                    levels=module_levels
                ))
        char_info["modules"] = operator_modules

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

def filter_operators(
    name: str = None,
    profession: str = None,
    sub_profession: str = None,
    rarity: int = None,
    position: str = None,
    tag: str = None,
    nation: str = None,
    gender: str = None,
    birth_place: str = None,
    race: str = None,
    max_level: int = None,
    obtain_approach: str = None
) -> List[dict]:
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
    
    return results

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
