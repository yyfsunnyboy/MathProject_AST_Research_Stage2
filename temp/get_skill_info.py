#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Get full info for 20 high school skills"""

import sqlite3

conn = sqlite3.connect('instance/kumon_math.db')
cursor = conn.cursor()

# 20个高中技能列表
skills = [
    'ApplicationsOfDerivatives',
    'UsingSuperpositionToFindExtrema',
    'ApplicationsOfExponentialFunctions',
    'JudgingTheRelationshipOfCircleAndLine',
    'RootsOfNthDegreeEquations',
    'PolynomialInequalities',
    'RealExponentsAndLaws',
    'GeometricMeaningOfLinearEquations',
    'Event',
    'Logarithms',
    'AreaRatioOfLinearTransformations',
    'IrrationalAndRealNumbers',
    'SpatialCoordinateSystem',
    'CommonSeriesSummationFormulas',
    'LinearInequalityInTwoVariables',
    'BasicTrigonometricIdentities',
    'LinearTransformationsOnAPlane',
    'TrigonometricRatiosInRadians',
    'PolarFormOfComplexNumbers',
    'AverageValueOfContinuousFunction',
]

print("【20个高中技能详细信息】\n")
for skill in skills:
    cursor.execute("SELECT * FROM skills_info WHERE skill_en_name = ?", (skill,))
    row = cursor.fetchone()
    
    if row:
        cols = [desc[0] for desc in cursor.description]
        data = dict(zip(cols, row))
        
        print(f"英文: {data.get('skill_en_name')}")
        print(f"中文: {data.get('skill_ch_name')}")
        print(f"分类: {data.get('category')}")
        print(f"描述: {data.get('description')[:100]}...")
        print()
    else:
        print(f"✗ 未找到: {skill}\n")

conn.close()
