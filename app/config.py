from pathlib import Path

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
    "battle_equip_table.json",
    "handbook_team_table.json"
]

# Static Mappings
PROFESSION_MAP = {
    "近卫": "WARRIOR",
    "狙击": "SNIPER",
    "重装": "TANK",
    "医疗": "MEDIC",
    "辅助": "SUPPORT",
    "术师": "CASTER",
    "特种": "SPECIAL",
    "先锋": "PIONEER"
}

POSITION_MAP = {
    "近战位": "MELEE",
    "远程位": "RANGED"
}
