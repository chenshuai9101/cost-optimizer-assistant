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
    "ALL_PRICING",
]

from .pricing import OPENAI_PRICING, ANTHROPIC_PRICING, GOOGLE_PRICING, ALL_PRICING
