# 成本优化助手 Skill

> AI Agent API成本优化工具箱 - 缓存、压缩、监控、路由

## 功能特性

| 功能 | 说明 | 节省比例 |
|-----|------|---------|
| Token统计 | 实时追踪每个请求的token消耗 | 可视化 |
| 成本计算 | 按模型价格计算实际花费 | 成本可见 |
| 结果缓存 | 内存+持久化双层缓存 | 30-70% |
| Prompt压缩 | HTML清理/JSON压缩/去重 | 5-60% |
| 成本报告 | 详细的花销分析和趋势 | 可优化 |
| 预算告警 | 阈值预警，避免超支 | 风控 |

## 快速开始

### 安装

```python
# 方式1: 直接导入
from cost_optimizer import CostOptimizer, CostConfig

# 方式2: 独立使用
pip install cost-optimizer-assistant
```

### 基础用法

```python
from cost_optimizer import CostOptimizer, CostConfig

# 初始化配置
config = CostConfig(
    cache_enabled=True,      # 启用缓存
    compress_enabled=True,   # 启用压缩
    budget_alert=100.0       # 预算告警阈值 ($)
)

# 创建优化器
optimizer = CostOptimizer(config)

# 使用优化器调用LLM
response = await optimizer.call_llm(
    prompt="分析这段代码的性能问题",
    model="gpt-4",
    api_key="your-api-key"
)

print(f"本次请求成本: ${response.cost:.4f}")
print(f"累计成本: ${optimizer.get_total_cost():.2f}")
```

## 核心模块

### 1. Token统计

```python
from cost_optimizer import TokenTracker

tracker = TokenTracker()

# 追踪请求
tracker.track(
    model="gpt-4",
    prompt_tokens=1500,
    completion_tokens=300
)

# 生成报告
report = tracker.generate_report()
print(f"总Token: {report.total_tokens}")
print(f"预估成本: ${report.total_cost:.2f}")
```

### 2. 缓存管理

```python
from cost_optimizer import SemanticCache

cache = SemanticCache(
    similarity_threshold=0.95,  # 语义相似度阈值
    max_size=1000              # 缓存条目上限
)

# 获取或计算
result = await cache.get_or_compute(
    prompt="如何优化Python代码性能?",
    compute_fn=lambda: llm.call(prompt)
)
```

### 3. Prompt压缩

```python
from cost_optimizer import PromptCompressor

compressor = PromptCompressor()

# 压缩HTML内容
compressed = compressor.compress_html(raw_html)

# 压缩JSON
compressed = compressor.compress_json(api_response)

# Schema压缩
compressed = compressor.compress_schema(tool_schema)
```

### 4. 成本监控

```python
from cost_optimizer import CostMonitor

monitor = CostMonitor()

# 设置告警
monitor.set_budget_limit(monthly=500.0)

# 检查是否超预算
if monitor.is_over_budget():
    monitor.send_alert("飞书/邮件/日志")
```

## 模型定价参考

```python
# OpenAI
OPENAI_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},  # $ / 1K tokens
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}

# Anthropic
ANTHROPIC_PRICING = {
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
}

# Google
GOOGLE_PRICING = {
    "gemini-pro": {"input": 0.00125, "output": 0.00375},
    "gemini-flash": {"input": 0.000075, "output": 0.0003},
}
```

## 配置选项

```python
from cost_optimizer import CostConfig

config = CostConfig(
    # 缓存配置
    cache_enabled=True,
    cache_ttl=3600,           # 缓存有效期(秒)
    cache_max_size=1000,       # 最大缓存条数
    similarity_threshold=0.95, # 语义缓存相似度阈值
    
    # 压缩配置
    compress_enabled=True,
    compress_html=True,        # 清理HTML标签
    compress_json=True,        # 压缩JSON空白
    compress_whitespace=True,  # 规范化空白字符
    
    # 监控配置
    budget_alert=100.0,        # 预算告警阈值
    report_interval=3600,      # 报告生成间隔
    
    # 存储配置
    persist_cache=True,        # 持久化缓存
    storage_path="./.cost_cache"  # 缓存存储路径
)
```

## 成本节省示例

### 场景1: RAG应用

```python
# 原始请求: 15,000 tokens
# 压缩后: 12,750 tokens (15%压缩)
# 节省: 2,250 tokens × $0.03/1K = $0.0675/请求
# 假设每天1000请求，月节省: $200+
```

### 场景2: 重复查询

```python
# 相同问题首次: 完整API调用
# 后续命中缓存: 直接返回 (几乎零成本)
# 命中率40%时，月节省: 40% × 总API费用
```

### 场景3: 模型选择

```python
# 简单任务: "解释这段代码" 
# - gpt-4: $0.05/请求
# - gpt-3.5-turbo: $0.002/请求
# 节省: 96%
```

## 最佳实践

### 1. 渐进式优化

```python
# 阶段1: 仅开启统计，了解现状
config = CostConfig(
    cache_enabled=False,
    compress_enabled=False,
    monitor_only=True
)

# 阶段2: 开启缓存
config.cache_enabled = True

# 阶段3: 开启压缩
config.compress_enabled = True
```

### 2. 关键任务保护

```python
# 对于重要任务，禁用自动优化
response = await optimizer.call_llm(
    prompt=important_task,
    model="gpt-4",
    disable_cache=True,    # 不使用缓存
    disable_compress=True  # 不压缩Prompt
)
```

### 3. 定期审计

```python
# 每周生成成本报告
async def weekly_audit():
    report = await optimizer.generate_report(
        period="7d",
        group_by="model"
    )
    
    # 识别异常高消耗
    anomalies = report.find_anomalies()
    if anomalies:
        await send_alert(anomalies)
```

## 常见问题

### Q: 缓存命中率低怎么办?
A: 检查语义相似度阈值是否过高，或考虑改用精确匹配缓存

### Q: 压缩会影响输出质量吗?
A: 提供3种模式: 无压缩 / 安全压缩(无损) / 激进压缩(可能有损)

### Q: 如何设置预算?
A: 通过 `config.budget_alert` 设置阈值，触发时自动告警

## 更新日志

### v1.0.0 (2026-04)
- 初始版本发布
- 支持Token统计、成本计算
- 支持内存缓存
- 支持Prompt压缩
- 支持成本报告

---

**License**: MIT
**Author**: Skill工厂牧云野店
