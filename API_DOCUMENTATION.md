# API Documentation

## Overview

The Arknights Data Search API provides access to detailed information about operators, including their basic info, attributes (stats), skills, and modules. The data is automatically sourced and cached from community-maintained repositories.

**Base URL**: `http://127.0.0.1:8000`

## Endpoints

### 1. Search Operators (Full Details)

**GET** `/api/operators`

Retrieves complete information for operators matching the search criteria.

**Query Parameters:**

| Parameter | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `name` | string | Operator name (supports partial/fuzzy match). | `None` |
| `profession` | string | Operator class (e.g., `WARRIOR`, `MEDIC`, `SNIPER`, `CASTER`, `SPECIAL`, `SUPPORT`, `PIONEER`, `TANK`). | `None` |
| `rarity` | int | Rarity (star count), 1-6. | `None` |
| `position` | string | Deployment position (`MELEE` or `RANGED`). | `None` |
| `tag` | string | Tag (e.g., `输出`, `治疗`). | `None` |
| `nation` | string | Nation/Faction ID (e.g., `rhodes`, `minos`). | `None` |
| `race` | string | Race (e.g., `卡特斯`, `黎博利`). | `None` |
| `elite` | int | **[Calc]** Target Elite phase for stat calculation (0-2). | Max available |
| `level` | int | **[Calc]** Target Level for stat calculation (1-90). | Max available |
| `trust` | int | **[Calc]** Trust value for stat calculation (0-200). Stats cap at 100. | `100` |
| `potential` | int | **[Calc]** Potential rank (0-5, where 0 is Pot 1, 5 is Pot 6). | `5` |

**Response:** A list of complete `Operator` objects.

### 2. Basic Information

**GET** `/api/operators/basic`

Retrieves lightweight basic information (ID, name, description, rarity, tags, etc.) without heavy data like stats, skills, or modules. Ideal for list views.

**Query Parameters:** Same as `/api/operators` (excluding calculation params).

**Response:** A list of `OperatorBase` objects.

### 3. Operator Attributes (Stats)

**GET** `/api/operators/attributes`

Calculates and retrieves specific panel attributes (HP, ATK, DEF, RES, etc.) based on the provided level parameters.

**Query Parameters:** Same as `/api/operators`. Use `elite`, `level`, `trust`, and `potential` to customize the calculation.

**Example Request:**
`GET /api/operators/attributes?name=阿米娅&elite=1&level=50`

**Response:**
```json
[
  {
    "charId": "char_002_amiya",
    "name": "阿米娅",
    "attributes": {
      "maxHp": 1128,
      "atk": 478,
      "def_": 101,
      "magicResistance": 15.0,
      "cost": 20,
      "blockCnt": 1,
      "moveSpeed": 1.0,
      "attackSpeed": 100.0,
      "baseAttackTime": 1.6,
      "respawnTime": 70
    }
  }
]
```

### 4. Operator Skills

**GET** `/api/operators/skills`

Retrieves detailed skill information, including all levels (1-7, M1-M3). Skill descriptions are automatically parsed to replace placeholders (e.g., `{atk_scale}`) with actual values.

**Query Parameters:** Same as `/api/operators` (excluding calculation params).

**Response:** A list of `OperatorSkillsResponse` objects.

### 5. Operator Modules

**GET** `/api/operators/modules`

Retrieves information about operator modules (Uniequip), including their stages, attribute bonuses, and trait/talent upgrades.

**Query Parameters:** Same as `/api/operators` (excluding calculation params).

**Response:** A list of `OperatorModulesResponse` objects.

## Data Models

### Operator (Full)
Contains all fields from `OperatorBase`, plus `attributes`, `skills`, `potentials`, and `modules`.

### CharacterAttributes
| Field | Type | Description |
| :--- | :--- | :--- |
| `maxHp` | int | Maximum Health |
| `atk` | int | Attack Power |
| `def_` | int | Defense |
| `magicResistance` | float | Arts Resistance |
| `cost` | int | Deployment Cost |
| `blockCnt` | int | Block Count |
| `attackSpeed` | float | Attack Speed (Base 100) |
| `baseAttackTime` | float | Attack Interval (seconds) |
| `respawnTime` | int | Redeploy Time (seconds) |

### Module
Contains `moduleId`, `name`, `description`, `typeIcon`, and a list of `levels`.
Each `level` contains `attributes` (stats added) and `trait_upgrade` / `talent_upgrade` (text descriptions of effect changes).