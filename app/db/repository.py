from typing import List, Dict, Optional
from app.config import PROFESSION_MAP, POSITION_MAP

class OperatorRepository:
    def __init__(self):
        self._operators: List[dict] = []
        self._nation_map: Dict[str, str] = {}
        self._subpro_map: Dict[str, str] = {}
        
    def load_data(self, operators: List[dict], nation_map: Dict[str, str], subpro_map: Dict[str, str]):
        self._operators = operators
        self._nation_map = nation_map
        self._subpro_map = subpro_map
        
    def get_all(self) -> List[dict]:
        return self._operators
        
    def filter_operators(
        self,
        name: str = None,
        profession: str = None,
        sub_profession: str = None,
        rarity: int = None,
        position: str = None,
        tags: List[str] = None,
        nation: str = None,
        gender: str = None,
        birth_place: str = None,
        race: str = None,
        obtain_approach: str = None
    ) -> List[dict]:
        results = self._operators

        if name:
            results = [op for op in results if op.get("name") and name.lower() in op.get("name").lower()]

        if profession:
            mapped_prof = PROFESSION_MAP.get(profession, profession)
            results = [op for op in results if op.get("profession") and op.get("profession").lower() == mapped_prof.lower()]
        
        if sub_profession:
            mapped_sub = self._subpro_map.get(sub_profession, sub_profession)
            results = [op for op in results if op.get("subProfessionId") and op.get("subProfessionId").lower() == mapped_sub.lower()]

        if rarity:
            rarity_str = f"TIER_{rarity}"
            results = [op for op in results if op.get("rarity") == rarity_str]

        if position:
            mapped_pos = POSITION_MAP.get(position, position)
            results = [op for op in results if op.get("position") and op.get("position").lower() == mapped_pos.lower()]

        if tags:
            requested_tags = [t.lower() for t in tags]
            results = [
                op for op in results 
                if op.get("tagList") and all(req_tag in [t.lower() for t in op["tagList"]] for req_tag in requested_tags)
            ]
        
        if nation:
            mapped_nation = self._nation_map.get(nation, nation)
            results = [op for op in results if op.get("nationId") and op.get("nationId").lower() == mapped_nation.lower()]

        if gender:
            results = [op for op in results if op.get("gender") and op.get("gender").lower() == gender.lower()]

        if birth_place:
            results = [op for op in results if op.get("birth_place") and op.get("birth_place").lower() == birth_place.lower()]
        
        if race:
            results = [op for op in results if op.get("race") and op.get("race").lower() == race.lower()]
        
        if obtain_approach:
            results = [op for op in results if op.get("itemObtainApproach") and op.get("itemObtainApproach").lower() == obtain_approach.lower()]
        
        return results

# Global Singleton
db = OperatorRepository()
