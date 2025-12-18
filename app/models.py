from typing import List, Optional, Dict
from pydantic import BaseModel

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

class ModuleLevel(BaseModel):
    level: int
    attributes: Optional[dict] = None
    trait_upgrade: Optional[str] = None
    talent_upgrade: Optional[str] = None

class ModuleBase(BaseModel):
    moduleId: str
    name: str
    description: Optional[str] = None
    typeIcon: str
    typeName: str

class Module(ModuleBase):
    levels: List[ModuleLevel]

class OperatorBase(BaseModel):
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
    modules: Optional[List[ModuleBase]] = None

class OperatorAttributesResponse(BaseModel):
    charId: str
    name: str
    attributes: Optional[CharacterAttributes] = None

class OperatorSkillsResponse(BaseModel):
    charId: str
    name: str
    skills: Optional[List[Skill]] = None

class OperatorModulesResponse(BaseModel):
    charId: str
    name: str
    modules: Optional[List[Module]] = None

class Operator(OperatorBase):
    attributes: Optional[CharacterAttributes] = None
    skills: Optional[List[Skill]] = None
    potentials: Optional[List[PotentialInfo]] = None
    modules: Optional[List[Module]] = None
