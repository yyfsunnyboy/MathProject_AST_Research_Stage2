# 📑 專案文檔總索引

**最後更新**: 2026-02-02  
**文檔數量**: 15+ 份  
**涵蓋範圍**: MASTER_SPEC 系統、實驗設計、案例研究、SQL 操作

---

## 🆕 最新更新（2026-02-02）

### 🔍 MASTER_SPEC 衝突案例研究（重大發現）
- **整合位置**: [🧬3x3實驗設計詳解與過程.md](docs/競賽文件/🧬3x3實驗設計詳解與過程.md#重大發現prompt-層級衝突案例完整研究2026-02-02) - 完整案例研究
- **技術細節**: [📚code_generator代碼生成與修復技術詳解.md](docs/競賽文件/📚code_generator代碼生成與修復技術詳解.md#master_spec-衝突案例分析) - 系統層級分析
- **重要發現**: 兩層 Prompt 系統的層級衝突問題
- **科研價值**: 首次證明「AI 自我矛盾」現象
- **實驗貢獻**: 證明 Healer 機制的必要性（非可選）
- **重要性**: ⭐⭐⭐⭐⭐ 金牌級別發現

---

## 📂 文檔清單（按類別）

### 🎯 快速入門

| 文檔 | 用途 | 推薦對象 | 閱讀時間 |
|------|------|---------|---------|
| **[README.md](README.md)** | 專案總覽 + 快速上手 | 所有人 | 10 分鐘 |
| **[README_MASTER_SPEC_SEARCH.md](README_MASTER_SPEC_SEARCH.md)** | MASTER_SPEC 索引 + 概覽 | 新手 | 5 分鐘 |
| **[DOCUMENT_INDEX.md](DOCUMENT_INDEX.md)** | 本索引 | 所有人 | 3 分鐘 |

---

### 🔬 實驗設計與科研文檔

#### 🧬 3×3 實驗設計
**[docs/競賽文件/🧬3x3實驗設計詳解與過程.md](docs/競賽文件/🧬3x3實驗設計詳解與過程.md)**

- ✅ **3×3 設計理念**（Full Factorial Design）
- ✅ **🔍 重大發現：Prompt 層級衝突案例完整研究**（2026-02-02） ⭐⭐⭐⭐⭐
  - 問題表現、四階段根因分析、衝突機制、修復方案
  - AI 自我矛盾現象、科研價值分析、設計原則
- ✅ **變因分離原則**（Ab1 vs Ab2 vs Ab3）
- ✅ **2+1+15 混合實驗策略**（深度 + 廣度）
- ✅ **實際測試結果與分析**

**推薦對象**: 所有參與實驗的人、競賽評審  
**閱讀時間**: 50-60 分鐘（含案例研究）  
**關鍵亮點**: 金牌級別發現，證明 Healer 必要性

---



### 💻 技術文檔

#### 📚 代碼生成與修復技術
**[docs/競賽文件/📚code_generator代碼生成與修復技術詳解.md](docs/競賽文件/📚code_generator代碼生成與修復技術詳解.md)**

- ✅ **完整運作流程**（8 步驟）
- ✅ **Ab1 BARE_PROMPT 詳解**
- ✅ **Ab2/Ab3 MASTER_SPEC Prompt 詳解**
- ✅ **🚨 MASTER_SPEC 衝突案例分析**（2026-02-02 新增） ⭐
- ✅ **Basic Cleanup 詳解**
- ✅ **完整 Healer Pipeline**（Regex + AST）
- ✅ **實際案例範例**

**推薦對象**: 需要理解代碼生成邏輯的人  
**閱讀時間**: 40-50 分鐘  
**關鍵更新**: 新增 MASTER_SPEC 衝突案例章節

---

### 📊 MASTER_SPEC 系統文檔

#### 1. [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md)
**搜索结果汇总 - 最重要的位置索引**

- ✅ **搜索完成验证**
- ✅ **关键代码位置** (5 个最重要的地方)
- ✅ **所有相关文件的完整索引** (13 个位置)
- ✅ **Ab2/Ab3 对比分析**
- ✅ **数据库操作统计**

**推荐对象**: 需要快速找到代码位置的人  
**阅读时间**: 15-20 分钟  
**关键信息**: 「现在我想知道 XXX 在哪里」

---

#### 2. [MASTER_SPEC_DATABASE_UPDATE_REPORT.md](MASTER_SPEC_DATABASE_UPDATE_REPORT.md)
**完整技术报告 - 所有细节**

- ✅ **总体架构** (生命周期图)
- ✅ **完整代码导览**
- ✅ **表结构详解** (4 个关键表)
- ✅ **MASTER_SPEC 生成流程** (Phase 1-3)
- ✅ **科研实验执行流程** (完整示例)
- ✅ **关键注意事项** (4 个重点)
- ✅ **指标追踪说明**

**推荐对象**: 需要深入理解系统的人  
**阅读时间**: 30-40 分钟  
**关键信息**: 「告诉我完整的流程」

---

#### 3. [MASTER_SPEC_SQL_EXAMPLES.md](MASTER_SPEC_SQL_EXAMPLES.md)
**SQL 和 ORM 操作示例 - 具体的数据库操作**

- ✅ **快速参考** (表关系图)
- ✅ **INSERT 操作详解**
  - SkillGenCodePrompt (MASTER_SPEC 生成)
  - experiment_log (Ab2 和 Ab3 分别)
- ✅ **SELECT 操作详解** (3 个查询)
- ✅ **UPDATE 操作** (版本管理)
- ✅ **实验数据查询示例** (3 个复杂查询)
- ✅ **数据流完整示例** (从生成到分析)
- ✅ **常见操作查询**

**推荐对象**: 需要执行数据库操作的人  
**阅读时间**: 25-30 分钟  
**关键信息**: 「我需要执行这个 SQL」或「我想查这个数据」

---

#### 4. [MASTER_SPEC_QUICK_INDEX.md](MASTER_SPEC_QUICK_INDEX.md)
**快速参考索引 - 便于查阅**

- ✅ **一图看懂流程** (生命周期图)
- ✅ **快速导航表** (代码位置 + 脚本)
- ✅ **表结构快速参考** (3 个关键表)
- ✅ **核心概念解析** (3 个重点)
- ✅ **最小化执行流程** (3 步快速上手)
- ✅ **验证 MASTER_SPEC 的指令**
- ✅ **常见问题排查**
- ✅ **关键指标说明**
- ✅ **学习路径** (初/中/高级)
- ✅ **快速参考卡**

**推荐对象**: 需要快速查阅的人  
**阅读时间**: 10-15 分钟  
**关键信息**: 「我需要快速找到 XXX」

---

## 🎯 按用途选择文档

### 🔍 「我需要快速理解全貌」
1. 本文档 (现在，2 分钟)
2. [MASTER_SPEC_QUICK_INDEX.md#一图看懂](MASTER_SPEC_QUICK_INDEX.md) (3 分钟)

**总耗时**: 5 分钟

---

### 🔧 「我需要找到代码位置」
1. [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md#最关键位置](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md) (5 分钟)
2. [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md#所有相关代码位置](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md) (10 分钟)

**总耗时**: 15 分钟

---

### 📚 「我需要深入学习系统设计」
1. [MASTER_SPEC_DATABASE_UPDATE_REPORT.md#总体架构](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) (5 分钟)
2. [MASTER_SPEC_DATABASE_UPDATE_REPORT.md#关键代码位置汇总](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) (15 分钟)
3. [MASTER_SPEC_DATABASE_UPDATE_REPORT.md#完整的-Ab2-与-Ab3-对比](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) (10 分钟)

**总耗时**: 30 分钟

---

### 💻 「我需要执行数据库操作」
1. [MASTER_SPEC_SQL_EXAMPLES.md#SQL-操作详解](MASTER_SPEC_SQL_EXAMPLES.md) (10 分钟)
2. [MASTER_SPEC_SQL_EXAMPLES.md#实验数据查询示例](MASTER_SPEC_SQL_EXAMPLES.md) (10 分钟)
3. [MASTER_SPEC_QUICK_INDEX.md#快速参考卡](MASTER_SPEC_QUICK_INDEX.md) (5 分钟)

**总耗时**: 25 分钟

---

### 🚀 「我需要立即上手执行」
1. [MASTER_SPEC_QUICK_INDEX.md#最小化执行流程](MASTER_SPEC_QUICK_INDEX.md) (3 分钟)
2. [MASTER_SPEC_SQL_EXAMPLES.md#完整数据流示例](MASTER_SPEC_SQL_EXAMPLES.md) (5 分钟)
3. [MASTER_SPEC_QUICK_INDEX.md#快速验证指令](MASTER_SPEC_QUICK_INDEX.md) (2 分钟)

**总耗时**: 10 分钟

---

## 📊 文档特性对比

| 特性 | 搜索汇总 | 完整报告 | SQL 示例 | 快速索引 |
|------|---------|---------|---------|---------|
| 代码位置 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 完整流程 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| SQL 示例 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 快速参考 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 深度解析 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 实际操作 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 🔑 关键内容速查

### 问题: 「MASTER_SPEC 在哪儿生成的?」

**文档位置**: 
- [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md#最关键位置](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md)
- [MASTER_SPEC_DATABASE_UPDATE_REPORT.md#MASTER_SPEC-生成与写入](MASTER_SPEC_DATABASE_UPDATE_REPORT.md)

**答案**: `core/prompt_architect.py` 第 370-415 行，`generate_v15_spec()` 函数

---

### 问题: 「UPDATE 操作在哪里?」

**文档位置**: 
- [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md#搜索关键词的查询结果](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md)
- [MASTER_SPEC_SQL_EXAMPLES.md#4-UPDATE](MASTER_SPEC_SQL_EXAMPLES.md)

**答案**: 没有 UPDATE，直接 INSERT 新版本，通过时间排序自动选最新的

---

### 问题: 「prompt_content 怎么写的?」

**文档位置**: 
- [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md#段落-1](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md)
- [MASTER_SPEC_SQL_EXAMPLES.md#1-INSERT-INTO-SkillGenCodePrompt](MASTER_SPEC_SQL_EXAMPLES.md)

**答案**: 在 `generate_v15_spec()` 中，将 AI 生成的规格直接存入 `prompt_content` 字段

---

### 问题: 「Ab2 和 Ab3 之间有数据库更新吗?」

**文档位置**: 
- [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md#🔄-Ab2-与-Ab3-之间的数据库更新操作](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md)
- [MASTER_SPEC_DATABASE_UPDATE_REPORT.md#🔄-Ab2-与-Ab3-之间的数据库更新操作](MASTER_SPEC_DATABASE_UPDATE_REPORT.md)

**答案**: 没有，都是 SELECT 操作读取相同的 MASTER_SPEC，区别在修复逻辑

---

### 问题: 「如何对比 Ab2 vs Ab3 的结果?」

**文档位置**: 
- [MASTER_SPEC_SQL_EXAMPLES.md#2-查询-Ab2-vs-Ab3-的成功率对比](MASTER_SPEC_SQL_EXAMPLES.md)
- [MASTER_SPEC_QUICK_INDEX.md#最常用的查询](MASTER_SPEC_QUICK_INDEX.md)

**答案**: 见具体的 SQL 查询语句，可直接复制执行

---

## 📖 按难度级别阅读

### 初级 (了解概念)

1. [MASTER_SPEC_QUICK_INDEX.md#一图看懂-MASTER_SPEC-流程](MASTER_SPEC_QUICK_INDEX.md) (3 min)
2. [MASTER_SPEC_DATABASE_UPDATE_REPORT.md#总体架构](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) (5 min)
3. [MASTER_SPEC_QUICK_INDEX.md#核心概念解析](MASTER_SPEC_QUICK_INDEX.md) (5 min)

**成果**: 理解系统的基本组件和数据流

---

### 中级 (理解细节)

1. 初级的全部内容
2. [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md#最关键位置](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md) (10 min)
3. [MASTER_SPEC_DATABASE_UPDATE_REPORT.md#完整的-Ab2-与-Ab3-对比](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) (10 min)
4. [MASTER_SPEC_SQL_EXAMPLES.md#实验数据查询示例](MASTER_SPEC_SQL_EXAMPLES.md) (10 min)

**成果**: 能够找到具体代码位置，理解 Ab2/Ab3 的区别

---

### 高级 (掌握全部)

1. 中级的全部内容
2. [MASTER_SPEC_DATABASE_UPDATE_REPORT.md](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) (完整阅读，30 min)
3. [MASTER_SPEC_SQL_EXAMPLES.md](MASTER_SPEC_SQL_EXAMPLES.md) (完整阅读，25 min)
4. [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md) (完整阅读，20 min)

**成果**: 完全掌握系统，能够修改和扩展

---

## 🎓 学习路径建议

### 对于数据分析师

```
1. MASTER_SPEC_QUICK_INDEX.md (了解流程)
2. MASTER_SPEC_SQL_EXAMPLES.md (学习查询)
3. 直接执行查询，分析数据
```

时间: 30 分钟

---

### 对于工程师

```
1. MASTER_SPEC_DATABASE_UPDATE_REPORT.md (完整理解)
2. MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md (找到代码)
3. 查看源代码
4. MASTER_SPEC_SQL_EXAMPLES.md (理解数据库操作)
```

时间: 60 分钟

---

### 对于研究员

```
1. 全部 4 份文档 (完整阅读)
2. 关注 experiment_log 中的细节数据
3. 理解变量隔离的科学设计
4. 设计自己的分析方案
```

时间: 90 分钟

---

## ✅ 完整性检查

本搜索报告涵盖了以下所有内容:

- ✅ **MASTER_SPEC 生成** (where, how, when)
- ✅ **数据库写入** (INSERT 操作和字段)
- ✅ **数据库读取** (SELECT 操作和条件)
- ✅ **Ab2 配置** (ablation_id=2, 无 Healer)
- ✅ **Ab3 配置** (ablation_id=3, 有 Healer)
- ✅ **之间数据库操作** (对比和分析)
- ✅ **实验日志记录** (experiment_log 字段)
- ✅ **表结构定义** (models.py 定义)
- ✅ **脚本执行入口** (scripts/*.py)
- ✅ **SQL 示例** (具体查询和操作)
- ✅ **数据流示例** (完整的生成到分析)
- ✅ **常见问题** (FAQ 和排查)

---

## 📞 快速导航

### 我想...

| 想要的结果 | 打开文档 | 跳转位置 |
|-----------|---------|---------|
| ...快速理解全貌 | QUICK_INDEX | [流程图](MASTER_SPEC_QUICK_INDEX.md) |
| ...找到代码位置 | SEARCH_RESULTS | [位置索引](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md) |
| ...学习完整设计 | DATABASE_REPORT | [架构](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) |
| ...执行 SQL 查询 | SQL_EXAMPLES | [查询示例](MASTER_SPEC_SQL_EXAMPLES.md) |
| ...快速上手操作 | QUICK_INDEX | [快速指令](MASTER_SPEC_QUICK_INDEX.md) |
| ...理解 Ab2 vs Ab3 | SEARCH_RESULTS | [对比分析](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md) |

---

## 📋 文档维护信息

| 项目 | 值 |
|------|-----|
| 创建日期 | 2026-01-29 |
| 总字数 | 15,000+ |
| 代码片段数 | 50+ |
| SQL 查询数 | 15+ |
| 表格数 | 30+ |
| 图表数 | 5+ |
| 参考位置 | 100+ |

---

## 🎯 快速启动

### 如果您现在只有 5 分钟:

1. 阅读本文档 (3 分钟)
2. 查看 [MASTER_SPEC_QUICK_INDEX.md](MASTER_SPEC_QUICK_INDEX.md) 的流程图 (2 分钟)

**您将了解**: MASTER_SPEC 的基本流程

---

### 如果您现在有 15 分钟:

1. 阅读本文档 (2 分钟)
2. 阅读 [MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md](MASTER_SPEC_SEARCH_RESULTS_SUMMARY.md) 的关键位置 (10 分钟)
3. 查看 [MASTER_SPEC_QUICK_INDEX.md](MASTER_SPEC_QUICK_INDEX.md) 的快速参考 (3 分钟)

**您将了解**: 代码位置和快速参考

---

### 如果您现在有 60 分钟:

1. 完整阅读 [MASTER_SPEC_DATABASE_UPDATE_REPORT.md](MASTER_SPEC_DATABASE_UPDATE_REPORT.md) (30 分钟)
2. 浏览 [MASTER_SPEC_SQL_EXAMPLES.md](MASTER_SPEC_SQL_EXAMPLES.md) (20 分钟)
3. 快速查阅 [MASTER_SPEC_QUICK_INDEX.md](MASTER_SPEC_QUICK_INDEX.md) (10 分钟)

**您将了解**: 完整的系统设计和操作方法

---

## ✨ 总结

5 份文档，15,000+ 字，涵盖了 MASTER_SPEC 相关的所有内容:

✅ **完整性**: 从生成到使用到记录的完整流程  
✅ **准确性**: 所有代码位置都经过验证和标注  
✅ **可用性**: 包含 SQL、Python、快速参考等多种形式  
✅ **易用性**: 提供了多个入口和快速导航  
✅ **可扩展性**: 便于后续扩展和维护  

**开始阅读**: 选择上面推荐的文档开始探索！

