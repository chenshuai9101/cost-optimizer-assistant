# 成本优化助手 Skill

## 技能概述

**技能名称**: cost_optimizer  
**技能版本**: v1.0.0  
**核心定位**: AI Agent API成本优化工具箱，提供Token统计、成本计算、结果缓存、Prompt压缩、成本监控等能力  
**适用场景**: 扣子Bot开发、AI应用成本控制、RAG应用优化  

---

## 核心能力

### 1. Token统计
- 实时追踪每个请求的input/output tokens
- 按模型、日期维度生成统计报告
- 支持自定义埋点记录

### 2. 成本计算
- 内置OpenAI/Anthropic/Google多模型定价表
- 支持自定义模型定价
- 精确计算每次API调用成本

### 3. 结果缓存
- **语义缓存**: 基于向量相似度，匹配度>95%直接返回缓存
- **精确缓存**: MD5哈希精确匹配
- 支持内存缓存+持久化双层存储

### 4. Prompt压缩
- HTML标签清理
- JSON空白字符压缩
- Schema精简压缩
- 可配置压缩比例

### 5. 成本监控
- 实时累计成本统计
- 预算阈值告警
- 成本趋势分析
- 异常消耗检测

---

## 使用方法

### 基础调用
```python
from cost_optimizer import CostOptimizer, CostConfig

# 初始化
config = CostConfig(
    cache_enabled=True,
    compress_enabled=True,
    budget_alert=100.0
)
optimizer = CostOptimizer(config)

# 调用LLM
response = await optimizer.call_llm(
    prompt="分析代码性能",
    model="gpt-4",
    api_key="your-key"
)
```

### 分模块调用
```python
from cost_optimizer import TokenTracker, SemanticCache, PromptCompressor

# Token追踪
tracker = TokenTracker()
tracker.track(model="gpt-4", prompt_tokens=1500, completion_tokens=300)

# 语义缓存
cache = SemanticCache(similarity_threshold=0.95)
result = await cache.get_or_compute(prompt, compute_fn)

# Prompt压缩
compressor = PromptCompressor()
compressed = compressor.compress_html(html_content)
```

---

## 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cache_enabled | bool | True | 启用缓存 |
| compress_enabled | bool | True | 启用压缩 |
| budget_alert | float | 100.0 | 预算告警阈值($) |
| cache_ttl | int | 3600 | 缓存有效期(秒) |
| similarity_threshold | float | 0.95 | 语义缓存阈值 |

---

## 成本节省效果

| 场景 | 原始成本 | 优化后 | 节省比例 |
|------|---------|--------|---------|
| RAG应用 | 100% | 70-85% | 15-30% |
| 重复查询 | 100% | 60% | 40% |
| Prompt精简 | 100% | 40-95% | 5-60% |

---

## 输出示例

```python
# 调用结果
response = await optimizer.call_llm(prompt="...", model="gpt-4")

print(f"本次成本: ${response.cost:.4f}")
print(f"Token使用: {response.total_tokens}")
print(f"缓存命中: {response.cache_hit}")
print(f"压缩节省: {response.compression_savings:.1%}")

# 成本报告
report = optimizer.generate_report()
print(f"累计成本: ${report.total_cost:.2f}")
print(f"请求次数: {report.total_requests}")
```

---

## 更新日志

### v1.0.0 (2026-04)
- 初始版本发布
- 支持Token统计、成本计算
- 支持内存缓存+持久化
- 支持Prompt压缩
- 支持成本监控与告警

---

## 作者信息

**开发者**: Skill工厂牧云野店  
**版本**: v1.0.0  
**适用平台**: 扣子Coze / Agent World
