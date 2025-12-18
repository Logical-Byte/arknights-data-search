from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.models import (
    Operator, 
    OperatorBase, 
    OperatorAttributesResponse, 
    OperatorSkillsResponse, 
    OperatorModulesResponse
)
from app.dependencies import FilterParams, CalculationParams
from app.core.logic import calculate_attributes, validate_calculation_params
from app.db.repository import db

router = APIRouter()

@router.get("/operators", response_model=List[Operator])
def search_operators(
    filters: FilterParams = Depends(),
    calc: CalculationParams = Depends()
):
    results = db.filter_operators(
        char_id=filters.char_id,
        name=filters.name, profession=filters.profession, sub_profession=filters.sub_profession,
        rarity=filters.rarity, position=filters.position, tags=[filters.tag] if filters.tag else None,
        nation=filters.nation, gender=filters.gender, birth_place=filters.birth_place,
        race=filters.race, obtain_approach=filters.obtain_approach
    )
    
    if len(results) == 1:
        try:
            validate_calculation_params(results[0], calc.elite, calc.level, calc.potential)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    final_results = []
    for op in results:
        op_copy = op.copy()
        op_copy["attributes"] = calculate_attributes(op, calc.elite, calc.level, calc.trust, calc.potential)
        final_results.append(op_copy)

    return final_results

@router.get("/operators/basic", response_model=List[OperatorBase])
def get_operators_basic(filters: FilterParams = Depends()):
    return db.filter_operators(
        char_id=filters.char_id,
        name=filters.name, profession=filters.profession, sub_profession=filters.sub_profession,
        rarity=filters.rarity, position=filters.position, tags=[filters.tag] if filters.tag else None,
        nation=filters.nation, gender=filters.gender, birth_place=filters.birth_place,
        race=filters.race, obtain_approach=filters.obtain_approach
    )

@router.get("/operators/attributes", response_model=List[OperatorAttributesResponse])
def get_operators_attributes(
    filters: FilterParams = Depends(),
    calc: CalculationParams = Depends()
):
    results = db.filter_operators(
        char_id=filters.char_id,
        name=filters.name, profession=filters.profession, sub_profession=filters.sub_profession,
        rarity=filters.rarity, position=filters.position, tags=[filters.tag] if filters.tag else None,
        nation=filters.nation, gender=filters.gender, birth_place=filters.birth_place,
        race=filters.race, obtain_approach=filters.obtain_approach
    )
    
    if len(results) == 1:
        try:
            validate_calculation_params(results[0], calc.elite, calc.level, calc.potential)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    final_results = []
    for op in results:
        attributes = calculate_attributes(op, calc.elite, calc.level, calc.trust, calc.potential)
        final_results.append({
            "charId": op["charId"],
            "name": op["name"],
            "attributes": attributes
        })
    return final_results

@router.get("/operators/skills", response_model=List[OperatorSkillsResponse])
def get_operators_skills(filters: FilterParams = Depends()):
    return db.filter_operators(
        char_id=filters.char_id,
        name=filters.name, profession=filters.profession, sub_profession=filters.sub_profession,
        rarity=filters.rarity, position=filters.position, tags=[filters.tag] if filters.tag else None,
        nation=filters.nation, gender=filters.gender, birth_place=filters.birth_place,
        race=filters.race, obtain_approach=filters.obtain_approach
    )

@router.get("/operators/modules", response_model=List[OperatorModulesResponse])
def get_operators_modules(filters: FilterParams = Depends()):
    return db.filter_operators(
        char_id=filters.char_id,
        name=filters.name, profession=filters.profession, sub_profession=filters.sub_profession,
        rarity=filters.rarity, position=filters.position, tags=[filters.tag] if filters.tag else None,
        nation=filters.nation, gender=filters.gender, birth_place=filters.birth_place,
        race=filters.race, obtain_approach=filters.obtain_approach
    )
