"""
成本监控模块
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import time
import json
import os


@dataclass
class CostAlert:
    """成本告警"""
    timestamp: float
    alert_type: str  # budget_warning / budget_exceeded / anomaly
    current_cost: float
    threshold: float
    message: str


@dataclass 
class CostReport:
    """成本报告"""
    total_cost: float
    total_requests: int
    total_tokens: int
    cache_hit_rate: float
    by_model: Dict[str, Dict[str, Any]]
    by_day: Dict[str, float]
    period_days: float
    savings_from_cache: float
    savings_from_compression: float
    alerts: List[CostAlert]
    suggestions: List[str]


class CostMonitor:
    """成本监控器"""
    
    def __init__(
        self,
        budget_limit: Optional[float] = None,
        warning_threshold: float = 0.8,
        alert_callback: Optional[Callable[[CostAlert], None]] = None
    ):
        self.budget_limit = budget_limit
        self.warning_threshold = warning_threshold
        self.alert_callback = alert_callback
        
        # 统计数据
        self.total_cost = 0.0
        self.total_requests = 0
        self.total_tokens = 0
        self.cache_hits = 0
        
        # 分组统计
        self._by_model: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"cost": 0, "requests": 0, "tokens": 0}
        )
        self._by_day: Dict[str, float] = defaultdict(float)
        self._by_hour: Dict[int, float] = defaultdict(float)
        
        # 告警历史
        self.alerts: List[CostAlert] = []
        
        # 节省统计
        self.savings_cache = 0.0
        self.savings_compression = 0.0
        
        # 时间追踪
        self._start_time = time.time()
        self._last_alert_time = 0
    
    def record_request(
        self,
        model: str,
        cost: float,
        tokens: int,
        cache_hit: bool = False,
        compression_savings: float = 0.0
    ):
        """记录一次请求"""
        self.total_cost += cost
        self.total_requests += 1
        self.total_tokens += tokens
        
        if cache_hit:
            self.cache_hits += 1
        
        # 分组统计
        self._by_model[model]["cost"] += cost
        self._by_model[model]["requests"] += 1
        self._by_model[model]["tokens"] += tokens
        
        # 时间统计
        now = datetime.now()
        day_key = now.strftime("%Y-%m-%d")
        self._by_day[day_key] += cost
        self._by_hour[now.hour] += cost
        
        # 节省统计
        if cache_hit:
            self.savings_cache += cost
        self.savings_compression += compression_savings
        
        # 检查告警
        self._check_alerts()
    
    def _check_alerts(self):
        """检查是否触发告警"""
        if self.budget_limit is None:
            return
        
        # 检查是否超过阈值
        if self.total_cost >= self.budget_limit:
            self._create_alert("budget_exceeded", 
                f"已超过预算限制: ${self.total_cost:.2f} / ${self.budget_limit:.2f}")
        
        elif self.total_cost >= self.budget_limit * self.warning_threshold:
            # 避免重复告警 (每小时最多一次)
            if time.time() - self._last_alert_time > 3600:
                self._create_alert("budget_warning",
                    f"预算使用超过{self.warning_threshold*100:.0f}%: ${self.total_cost:.2f}")
    
    def _create_alert(self, alert_type: str, message: str):
        """创建告警"""
        alert = CostAlert(
            timestamp=time.time(),
            alert_type=alert_type,
            current_cost=self.total_cost,
            threshold=self.budget_limit or 0,
            message=message
        )
        
        self.alerts.append(alert)
        self._last_alert_time = time.time()
        
        if self.alert_callback:
            self.alert_callback(alert)
    
    def get_cache_hit_rate(self) -> float:
        """获取缓存命中率"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    def generate_report(self) -> CostReport:
        """生成成本报告"""
        suggestions = self._generate_suggestions()
        
        return CostReport(
            total_cost=self.total_cost,
            total_requests=self.total_requests,
            total_tokens=self.total_tokens,
            cache_hit_rate=self.get_cache_hit_rate(),
            by_model=dict(self._by_model),
            by_day=dict(self._by_day),
            period_days=(time.time() - self._start_time) / 86400,
            savings_from_cache=self.savings_cache,
            savings_from_compression=self.savings_compression,
            alerts=self.alerts[-10:],  # 最近10条告警
            suggestions=suggestions
        )
    
    def _generate_suggestions(self) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        cache_hit_rate = self.get_cache_hit_rate()
        if cache_hit_rate < 0.3:
            suggestions.append("缓存命中率较低(<30%)，考虑增加缓存容量或延长TTL")
        
        if self.total_requests > 0:
            avg_cost = self.total_cost / self.total_requests
            if avg_cost > 0.1:
                suggestions.append(f"平均请求成本较高(${avg_cost:.3f})，考虑使用更轻量的模型处理简单任务")
        
        # 检查是否有昂贵的模型使用
        for model, stats in self._by_model.items():
            if stats["cost"] > 50 and "gpt-4" in model.lower():
                suggestions.append(f"模型 {model} 成本较高，考虑使用 gpt-3.5-turbo 或其他替代方案")
        
        return suggestions
    
    def export_report(self, path: str):
        """导出报告到文件"""
        report = self.generate_report()
        
        with open(path, 'w') as f:
            json.dump({
                "generated_at": datetime.now().isoformat(),
                "total_cost": report.total_cost,
                "total_requests": report.total_requests,
                "cache_hit_rate": f"{report.cache_hit_rate:.1%}",
                "savings": {
                    "cache": report.savings_from_cache,
                    "compression": report.savings_from_compression,
                },
                "by_model": report.by_model,
                "suggestions": report.suggestions,
            }, f, indent=2)
    
    def reset(self):
        """重置监控数据"""
        self.total_cost = 0.0
        self.total_requests = 0
        self.total_tokens = 0
        self.cache_hits = 0
        self._by_model.clear()
        self._by_day.clear()
        self._by_hour.clear()
        self.alerts.clear()
        self.savings_cache = 0.0
        self.savings_compression = 0.0
        self._start_time = time.time()
        self._last_alert_time = 0
    
    def get_today_cost(self) -> float:
        """获取今日成本"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self._by_day.get(today, 0.0)
    
    def get_hourly_average(self) -> float:
        """获取每小时平均成本"""
        total_hours = sum(self._by_hour.values())
        hours_counted = len(self._by_hour) or 1
        return total_hours / hours_counted
