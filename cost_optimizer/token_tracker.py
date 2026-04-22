"""
Token追踪模块
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import time


@dataclass
class TokenRecord:
    """Token记录"""
    timestamp: float
    model: str
    prompt_tokens: int
    completion_tokens: int
    request_id: str = ""
    cache_hit: bool = False
    
    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class TokenReport:
    """Token报告"""
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_requests: int
    cache_hit_rate: float
    by_model: Dict[str, Dict[str, int]]
    period_seconds: float
    
    def to_dict(self) -> Dict:
        return {
            "total_tokens": self.total_tokens,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_requests": self.total_requests,
            "cache_hit_rate": f"{self.cache_hit_rate:.1%}",
            "by_model": self.by_model,
            "period_seconds": self.period_seconds,
        }


class TokenTracker:
    """Token使用追踪器"""
    
    def __init__(self):
        self.records: List[TokenRecord] = []
        self._by_model: Dict[str, List[TokenRecord]] = defaultdict(list)
        self._start_time = time.time()
        self._cache_hits = 0
    
    def track(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        request_id: str = "",
        cache_hit: bool = False
    ) -> TokenRecord:
        """追踪一次Token使用"""
        record = TokenRecord(
            timestamp=time.time(),
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            request_id=request_id,
            cache_hit=cache_hit
        )
        
        self.records.append(record)
        self._by_model[model].append(record)
        
        if cache_hit:
            self._cache_hits += 1
        
        return record
    
    def get_total_tokens(self) -> int:
        """获取总Token数"""
        return sum(r.total_tokens for r in self.records)
    
    def get_total_requests(self) -> int:
        """获取总请求数"""
        return len(self.records)
    
    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        if not self.records:
            return 0.0
        return self._cache_hits / len(self.records)
    
    def get_by_model(self) -> Dict[str, Dict[str, int]]:
        """按模型分组统计"""
        result = {}
        for model, records in self._by_model.items():
            result[model] = {
                "requests": len(records),
                "prompt_tokens": sum(r.prompt_tokens for r in records),
                "completion_tokens": sum(r.completion_tokens for r in records),
                "total_tokens": sum(r.total_tokens for r in records),
            }
        return result
    
    def generate_report(self) -> TokenReport:
        """生成Token使用报告"""
        total_requests = len(self.records)
        
        return TokenReport(
            total_tokens=self.get_total_tokens(),
            total_prompt_tokens=sum(r.prompt_tokens for r in self.records),
            total_completion_tokens=sum(r.completion_tokens for r in self.records),
            total_requests=total_requests,
            cache_hit_rate=self.get_cache_hit_rate(),
            by_model=self.get_by_model(),
            period_seconds=time.time() - self._start_time,
        )
    
    def reset(self):
        """重置统计数据"""
        self.records.clear()
        self._by_model.clear()
        self._start_time = time.time()
        self._cache_hits = 0
    
    def get_recent(self, minutes: int = 60) -> List[TokenRecord]:
        """获取最近N分钟的记录"""
        cutoff = time.time() - minutes * 60
        return [r for r in self.records if r.timestamp >= cutoff]
