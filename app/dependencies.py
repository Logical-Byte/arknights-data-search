from dataclasses import dataclass
from typing import Optional
from fastapi import Query

@dataclass
class FilterParams:
    name: Optional[str] = Query(None, title="名称", description="干员的名称 (支持模糊搜索)")
    profession: Optional[str] = Query(None, title="职业", description="干员的职业")
    sub_profession: Optional[str] = Query(None, title="分支", description="干员的子职业")
    rarity: Optional[int] = Query(None, title="稀有度", ge=1, le=6, description="干员的稀有度 (1-6)")
    position: Optional[str] = Query(None, title="位置", description="干员的位置 (MELEE or RANGED)")
    tag: Optional[str] = Query(None, title="词缀", description="干员的标签")
    nation: Optional[str] = Query(None, title="势力", description="干员所属的势力")
    gender: Optional[str] = Query(None, title="性别", description="干员的性别")
    birth_place: Optional[str] = Query(None, title="出身地", description="干员的出身地")
    race: Optional[str] = Query(None, title="种族", description="干员的种族")
    obtain_approach: Optional[str] = Query(None, title="获取途径", description="干员的获取途径")

@dataclass
class CalculationParams:
    elite: Optional[int] = Query(None, title="目标精英阶段", ge=0, le=2, description="计算属性时的精英阶段 (0-2)")
    level: Optional[int] = Query(None, title="目标等级", ge=1, le=90, description="计算属性时的等级")
    potential: Optional[int] = Query(5, title="目标潜能", ge=0, le=5, description="计算属性时的潜能等级 (0-5, 0为潜能1, 5为满潜)")
    trust: Optional[int] = Query(100, title="目标信赖", ge=0, le=200, description="计算属性时的信赖值 (0-200, 属性加成100封顶)")
