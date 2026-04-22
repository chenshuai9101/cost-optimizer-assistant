"""
成本计算模块
"""

from dataclasses import dataclass
from typing import Dict, Optional, Union
from . import ALL_PRICING


@dataclass
class CostRecord:
    """成本记录"""
    model: str
    prompt_tokens: int
    completion_tokens: int
    input_cost: float
    output_cost: float
    
    @property
    def total_cost(self) -> float:
        return self.input_cost + self.output_cost


class CostCalculator:
    """成本计算器"""
    
    def __init__(self, custom_pricing: Optional[Dict[str, Dict[str, float]]] = None):
        self.pricing = ALL_PRICING.copy()
        if custom_pricing:
            self.pricing.update(custom_pricing)
    
    def calculate(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> CostRecord:
        """计算单次请求成本"""
        pricing = self._get_pricing(model)
        
        input_cost = (prompt_tokens / 1000) * pricing["input"]
        output_cost = (completion_tokens / 1000) * pricing["output"]
        
        return CostRecord(
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
        )
    
    def _get_pricing(self, model: str) -> Dict[str, float]:
        """获取模型定价"""
        # 精确匹配
        if model in self.pricing:
            return self.pricing[model]
        
        # 前缀匹配
        for pricing_model, price in self.pricing.items():
            if model.startswith(pricing_model):
                return price
        
        # 默认定价 (按gpt-3.5-turbo)
        return {
            "input": 0.001,
            "output": 0.002,
        }
    
    def calculate_savings(
        self,
        original_tokens: int,
        optimized_tokens: int,
        model: str,
        is_input: bool = True
    ) -> float:
        """计算节省金额"""
        saved_tokens = original_tokens - optimized_tokens
        pricing = self._get_pricing(model)
        rate = pricing["input"] if is_input else pricing["output"]
        return (saved_tokens / 1000) * rate
    
    def estimate_monthly_cost(
        self,
        daily_requests: int,
        avg_prompt_tokens: int,
        avg_completion_tokens: int,
        model: str
    ) -> float:
        """估算月成本"""
        days_per_month = 30
        record = self.calculate(
            model=model,
            prompt_tokens=avg_prompt_tokens,
            completion_tokens=avg_completion_tokens
        )
        return record.total_cost * daily_requests * days_per_month
    
    def compare_models(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        models: list
    ) -> Dict[str, float]:
        """比较多个模型的成本"""
        result = {}
        for model in models:
            cost = self.calculate(prompt_tokens, completion_tokens, model)
            result[model] = cost.total_cost
        return result


# 全局默认计算器
_default_calculator: Optional[CostCalculator] = None


def get_calculator(custom_pricing: Optional[Dict] = None) -> CostCalculator:
    """获取成本计算器单例"""
    global _default_calculator
    if _default_calculator is None or custom_pricing:
        _default_calculator = CostCalculator(custom_pricing)
    return _default_calculator
