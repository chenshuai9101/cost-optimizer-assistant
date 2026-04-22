"""
成本优化器主模块
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any, Callable, Awaitable
import asyncio
import time
import json

from .config import CostConfig
from .token_tracker import TokenTracker, TokenRecord
from .cost_calculator import CostCalculator, CostRecord
from .cache import CacheManager, ExactCache, SemanticCache
from .compressor import PromptCompressor, CompressionResult
from .monitor import CostMonitor, CostReport, CostAlert


@dataclass
class LLMRequest:
    """LLM请求"""
    prompt: str
    model: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    disable_cache: bool = False
    disable_compress: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    cache_hit: bool = False
    compression_savings: float = 0.0
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CostOptimizer:
    """成本优化器"""
    
    def __init__(
        self,
        config: Optional[CostConfig] = None,
        llm_callable: Optional[Callable[..., Awaitable[LLMResponse]]] = None
    ):
        self.config = config or CostConfig()
        self.llm_callable = llm_callable
        
        # 初始化各模块
        self._init_modules()
    
    def _init_modules(self):
        """初始化各模块"""
        # Token追踪
        self.token_tracker = TokenTracker()
        
        # 成本计算
        self.cost_calculator = CostCalculator(
            custom_pricing=self.config.custom_pricing
        )
        
        # 缓存管理
        if self.config.cache_enabled:
            self.cache_manager = CacheManager(
                exact_cache=ExactCache(
                    max_size=self.config.cache_max_size,
                    ttl=self.config.cache_ttl
                ),
                semantic_cache=SemanticCache(
                    max_size=self.config.cache_max_size // 2,
                    ttl=self.config.cache_ttl,
                    similarity_threshold=self.config.similarity_threshold
                )
            )
        else:
            self.cache_manager = None
        
        # Prompt压缩
        if self.config.compress_enabled:
            self.compressor = PromptCompressor(
                compress_html=self.config.compress_html,
                compress_json=self.config.compress_json,
                compress_whitespace=self.config.compress_whitespace,
                compress_dedent=self.config.compress_dedent
            )
        else:
            self.compressor = None
        
        # 成本监控
        self.monitor = CostMonitor(
            budget_limit=self.config.budget_alert
        )
        
        # 请求历史
        self._request_log: list = []
    
    async def call_llm(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        **kwargs
    ) -> LLMResponse:
        """
        调用LLM (带成本优化)
        """
        request = LLMRequest(
            prompt=prompt,
            model=model,
            **kwargs
        )
        
        return await self._execute_request(request)
    
    async def _execute_request(self, request: LLMRequest) -> LLMResponse:
        """执行请求"""
        start_time = time.time()
        
        # 1. 缓存检查
        cache_hit = False
        if self.cache_manager and not request.disable_cache:
            cached_result, cache_hit = await self.cache_manager.get_or_compute(
                prompt=request.prompt,
                model=request.model,
                compute_fn=lambda: None  # 临时值
            )
            
            if cache_hit and cached_result is not None:
                # 从缓存获取结果
                return self._build_response_from_cache(cached_result, request, start_time)
        
        # 2. Prompt压缩
        original_prompt = request.prompt
        compression_result: Optional[CompressionResult] = None
        compression_savings = 0.0
        
        if self.compressor and not request.disable_compress:
            compression_result = self.compressor.compress_with_report(request.prompt)
            request.prompt = compression_result.compressed
            compression_savings = compression_result.savings_percent
        
        # 3. 调用LLM
        if self.llm_callable:
            response = await self.llm_callable(request)
        else:
            # 模拟响应 (测试用)
            response = await self._mock_llm_call(request)
        
        # 4. 记录成本
        self._record_usage(request, response, cache_hit, compression_savings)
        
        # 5. 存入缓存
        if self.cache_manager and not request.disable_cache and not cache_hit:
            self.cache_manager.exact.set(
                original_prompt,
                request.model,
                response.content
            )
        
        return response
    
    def _build_response_from_cache(
        self,
        cached_content: Any,
        request: LLMRequest,
        start_time: float
    ) -> LLMResponse:
        """从缓存构建响应"""
        # 估算缓存命中的成本节省
        cost_record = self.cost_calculator.calculate(
            model=request.model,
            prompt_tokens=0,  # 无实际API调用
            completion_tokens=0
        )
        
        return LLMResponse(
            content=cached_content,
            model=request.model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost=0.0,  # 缓存命中无成本
            cache_hit=True,
            latency_ms=(time.time() - start_time) * 1000
        )
    
    async def _mock_llm_call(self, request: LLMRequest) -> LLMResponse:
        """模拟LLM调用 (用于测试)"""
        # 模拟token计数
        prompt_tokens = len(request.prompt) // 4
        completion_tokens = len(request.prompt) // 2
        
        # 模拟延迟
        await asyncio.sleep(0.1)
        
        cost_record = self.cost_calculator.calculate(
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        return LLMResponse(
            content=f"[Mock response for: {request.prompt[:50]}...]",
            model=request.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            cost=cost_record.total_cost,
            latency_ms=100
        )
    
    def _record_usage(
        self,
        request: LLMRequest,
        response: LLMResponse,
        cache_hit: bool,
        compression_savings: float
    ):
        """记录使用情况"""
        # Token追踪
        self.token_tracker.track(
            model=request.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            cache_hit=cache_hit
        )
        
        # 成本监控
        self.monitor.record_request(
            model=request.model,
            cost=response.cost,
            tokens=response.total_tokens,
            cache_hit=cache_hit,
            compression_savings=compression_savings
        )
        
        # 记录到历史
        self._request_log.append({
            "timestamp": time.time(),
            "model": request.model,
            "cost": response.cost,
            "tokens": response.total_tokens,
            "cache_hit": cache_hit
        })
    
    def get_total_cost(self) -> float:
        """获取总成本"""
        return self.monitor.total_cost
    
    def get_total_requests(self) -> int:
        """获取总请求数"""
        return self.monitor.total_requests
    
    def generate_report(self) -> CostReport:
        """生成成本报告"""
        return self.monitor.generate_report()
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """获取压缩统计"""
        if not self.compressor:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "html_compression": self.config.compress_html,
            "json_compression": self.config.compress_json,
            "whitespace_compression": self.config.compress_whitespace,
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self.cache_manager:
            return {"enabled": False}
        
        return self.cache_manager.get_stats()
    
    def clear_cache(self):
        """清空缓存"""
        if self.cache_manager:
            self.cache_manager.clear()
    
    def reset_stats(self):
        """重置统计"""
        self.token_tracker.reset()
        self.monitor.reset()
        self._request_log.clear()
    
    async def optimize_batch(
        self,
        requests: list
    ) -> list:
        """批量优化请求"""
        tasks = [
            self._execute_request(LLMRequest(**req))
            for req in requests
        ]
        return await asyncio.gather(*tasks)


# 便捷函数
def create_optimizer(
    cache_enabled: bool = True,
    compress_enabled: bool = True,
    budget_alert: Optional[float] = None,
    **kwargs
) -> CostOptimizer:
    """创建优化器的便捷函数"""
    config = CostConfig(
        cache_enabled=cache_enabled,
        compress_enabled=compress_enabled,
        budget_alert=budget_alert,
        **kwargs
    )
    return CostOptimizer(config)
