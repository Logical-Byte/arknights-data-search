import json
import time
import os
import urllib.request
from app.models import CharacterAttributes, SkillLevel, Skill, PotentialInfo, ModuleLevel, Module, Token
from app.utils import clean_markup, replace_description_placeholders, parse_handbook_info
from app.config import CACHE_DIR, REMOTE_BASE_URL, CACHE_DURATION, REQUIRED_FILES
from app.db.repository import db

# Global State
operators_data = []
NATION_MAP = {}
SUBPRO_MAP = {}

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
    # Local variables to hold data before committing to DB
    temp_nation_map = {}
    temp_subpro_map = {}
    
    # 1. Update cache before loading
    update_cache_if_needed()

    print(f"Loading data from cache: {CACHE_DIR}")
    
    # Paths now point to the CACHE_DIR
    char_table_path = CACHE_DIR / "character_table.json"
    handbook_path = CACHE_DIR / "handbook_info_table.json"
    skill_table_path = CACHE_DIR / "skill_table.json"
    favor_table_path = CACHE_DIR / "favor_table.json"
    uniequip_table_path = CACHE_DIR / "uniequip_table.json"
    battle_equip_table_path = CACHE_DIR / "battle_equip_table.json"
    handbook_team_path = CACHE_DIR / "handbook_team_table.json"

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
            uniequip_full_data = json.load(f)
            uniequip_data = uniequip_full_data.get("equipDict", {})
            # Load sub-profession mapping from uniequip_table.json
            subpro_data = uniequip_full_data.get("subProfDict", {})
        with open(battle_equip_table_path, 'r', encoding='utf-8') as f:
            battle_equip_data = json.load(f)
        
        # Load mapping tables
        if handbook_team_path.exists():
            with open(handbook_team_path, 'r', encoding='utf-8') as f:
                team_data = json.load(f)
                for team_id, team_info in team_data.items():
                    if isinstance(team_info, dict) and "powerName" in team_info:
                        temp_nation_map[team_info["powerName"]] = team_id
        
        # Populate SUBPRO_MAP from uniequip_table.json's subProfDict
        for sub_id, sub_info in subpro_data.items():
            if isinstance(sub_info, dict) and "subProfessionName" in sub_info:
                # Use subProfessionId if available, otherwise fallback to key
                # Assuming uniequip_table.json has correct IDs
                prof_id = sub_info.get("subProfessionId", sub_id)
                temp_subpro_map[sub_info["subProfessionName"]] = prof_id

    except Exception as e:
        print(f"Failed to load or parse data files: {e}")
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
        # Enhanced filtering to exclude tokens and non-characters
        if not isinstance(char_info, dict): continue
        sub_prof = char_info.get("subProfessionId", "")
        if sub_prof == "notchar" or sub_prof.startswith("notchar"): continue
        if char_info.get("profession") == "TOKEN": continue

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

        # --- Add Skill Info & Extract Tokens ---
        operator_skills = []
        operator_tokens = []
        token_ids_added = set()
        
        if char_info.get("skills"):
            for skill_ref in char_info["skills"]:
                # 1. Extract Token Info
                token_id = skill_ref.get("overrideTokenKey")
                if token_id and token_id not in token_ids_added:
                    token_data = character_data.get(token_id)
                    if token_data:
                        operator_tokens.append(Token(
                            tokenId=token_id,
                            name=token_data.get("name"),
                            description=clean_markup(token_data.get("description")),
                            profession=token_data.get("profession"),
                            subProfessionId=token_data.get("subProfessionId")
                        ))
                        token_ids_added.add(token_id)
                
                # 2. Build Skill Object
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
        char_info["tokens"] = operator_tokens

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
                                        # Merge attribute blackboard with candidate blackboard
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
    
    db.load_data(temp_operators_data, temp_nation_map, temp_subpro_map)
    print(f"Data loaded successfully. {len(temp_operators_data)} operators.")