from typing import List, Optional
from fastapi import FastAPI, Query

from models import Operator
from services import load_data, calculate_attributes, operators_data

app = FastAPI(
    title="Arknights Game Data API",
    description="An API to query Arknights operator data from the local game data files."
)

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
    max_level: Optional[int] = Query(None, title="精英等级过滤", ge=0, le=2, description="筛选能够达到该精英等级的干员 (旧参数)"),
    obtain_approach: Optional[str] = Query(None, title="获取途径", description="干员的获取途径"),
    # New calculation parameters
    elite: Optional[int] = Query(None, title="目标精英阶段", ge=0, le=2, description="计算属性时的精英阶段 (0-2)"),
    level: Optional[int] = Query(None, title="目标等级", ge=1, le=90, description="计算属性时的等级"),
    potential: Optional[int] = Query(5, title="目标潜能", ge=0, le=5, description="计算属性时的潜能等级 (0-5, 0为潜能1, 5为满潜)"),
    trust: Optional[int] = Query(100, title="目标信赖", ge=0, le=200, description="计算属性时的信赖值 (0-200, 属性加成100封顶)")
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
    
    if max_level is not None:
        results = [op for op in results if len(op.get("phases", [])) > max_level]

    if obtain_approach:
        results = [op for op in results if op.get("itemObtainApproach") and op.get("itemObtainApproach").lower() == obtain_approach.lower()]

    # Dynamic Attribute Calculation
    # We create a new list of Operator objects (or dicts) to avoid modifying the global cache
    final_results = []
    for op in results:
        # Shallow copy to avoid side effects on the global operators_data
        op_copy = op.copy()
        
        # Calculate attributes based on parameters or default to max
        # If parameters are not provided, calculate_attributes handles defaults (Max/Max)
        # Note: If elite/level are None, it calculates max stats for that operator.
        # This overwrites the statically loaded 'attributes' with a dynamically calculated one.
        op_copy["attributes"] = calculate_attributes(op, elite, level, trust, potential)
        final_results.append(op_copy)

    return final_results