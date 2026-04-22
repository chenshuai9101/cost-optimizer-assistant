"""
成本优化助手 - 核心模块

AI Agent API成本优化工具箱
支持: Token统计、成本计算、缓存管理、Prompt压缩、成本监控
"""

from .config import CostConfig
from .token_tracker import TokenTracker
from .cost_calculator import CostCalculator
from .cache import SemanticCache, ExactCache
from .compressor import PromptCompressor
from .monitor import CostMonitor
from .optimizer import CostOptimizer

__version__ = "1.0.0"
__all__ = [
    "CostConfig",
    "TokenTracker",
    "CostCalculator",
    "SemanticCache",
    "ExactCache", 
    "PromptCompressor",
    "CostMonitor",
    "CostOptimizer",
]

# 模型定价表 (单位: $/1K tokens)
OPENAI_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
}

ANTHROPIC_PRICING = {
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-3.5-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3.5-haiku": {"input": 0.0008, "output": 0.004},
}

GOOGLE_PRICING = {
    "gemini-pro": {"input": 0.00125, "output": 0.00375},
    "gemini-flash": {"input": 0.000075, "output": 0.0003},
    "gemini-2.0-flash": {"input": 0.0, "output": 0.0},  # 免费
}

# 合并所有定价
ALL_PRICING = {}
ALL_PRICING.update(OPENAI_PRICING)
ALL_PRICING.update(ANTHROPIC_PRICING)
ALL_PRICING.update(GOOGLE_PRICING)
