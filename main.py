from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Query

from models import (
    Operator, 
    OperatorBase, 
    OperatorAttributesResponse, 
    OperatorSkillsResponse, 
    OperatorModulesResponse
)
from services import load_data, calculate_attributes, operators_data, filter_operators

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API starting up. Performing initial data load...")
    load_data()
    print("Startup data load complete.")
    yield

app = FastAPI(
    title="Arknights Game Data API",
    description="An API to query Arknights operator data from the local game data files.",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {"message": "欢迎使用明日方舟干员数据查询 API"}

# --- Common Query Parameters ---
# Defined as a dependency or just reused in function signatures for clarity (FastAPI works well with explicit params)

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
    elite: Optional[int] = Query(None, title="目标精英阶段", ge=0, le=2, description="计算属性时的精英阶段 (0-2)"),
    level: Optional[int] = Query(None, title="目标等级", ge=1, le=90, description="计算属性时的等级"),
    potential: Optional[int] = Query(5, title="目标潜能", ge=0, le=5, description="计算属性时的潜能等级 (0-5, 0为潜能1, 5为满潜)"),
    trust: Optional[int] = Query(100, title="目标信赖", ge=0, le=200, description="计算属性时的信赖值 (0-200, 属性加成100封顶)")
):
    results = filter_operators(name, profession, sub_profession, rarity, position, tag, nation, gender, birth_place, race, max_level, obtain_approach)
    
    final_results = []
    for op in results:
        op_copy = op.copy()
        op_copy["attributes"] = calculate_attributes(op, elite, level, trust, potential)
        final_results.append(op_copy)

    return final_results

@app.get("/api/operators/basic", response_model=List[OperatorBase])
def get_operators_basic(
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
    obtain_approach: Optional[str] = Query(None, title="获取途径", description="干员的获取途径")
):
    return filter_operators(name, profession, sub_profession, rarity, position, tag, nation, gender, birth_place, race, max_level, obtain_approach)

@app.get("/api/operators/attributes", response_model=List[OperatorAttributesResponse])
def get_operators_attributes(
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
    elite: Optional[int] = Query(None, title="目标精英阶段", ge=0, le=2, description="计算属性时的精英阶段 (0-2)"),
    level: Optional[int] = Query(None, title="目标等级", ge=1, le=90, description="计算属性时的等级"),
    potential: Optional[int] = Query(5, title="目标潜能", ge=0, le=5, description="计算属性时的潜能等级 (0-5, 0为潜能1, 5为满潜)"),
    trust: Optional[int] = Query(100, title="目标信赖", ge=0, le=200, description="计算属性时的信赖值 (0-200, 属性加成100封顶)")
):
    results = filter_operators(name, profession, sub_profession, rarity, position, tag, nation, gender, birth_place, race, max_level, obtain_approach)
    
    final_results = []
    for op in results:
        # We only need charId, name, and attributes for this response
        attributes = calculate_attributes(op, elite, level, trust, potential)
        final_results.append({
            "charId": op["charId"],
            "name": op["name"],
            "attributes": attributes
        })
    return final_results

@app.get("/api/operators/skills", response_model=List[OperatorSkillsResponse])
def get_operators_skills(
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
    obtain_approach: Optional[str] = Query(None, title="获取途径", description="干员的获取途径")
):
    return filter_operators(name, profession, sub_profession, rarity, position, tag, nation, gender, birth_place, race, max_level, obtain_approach)

@app.get("/api/operators/modules", response_model=List[OperatorModulesResponse])
def get_operators_modules(
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
    obtain_approach: Optional[str] = Query(None, title="获取途径", description="干员的获取途径")
):
    return filter_operators(name, profession, sub_profession, rarity, position, tag, nation, gender, birth_place, race, max_level, obtain_approach)