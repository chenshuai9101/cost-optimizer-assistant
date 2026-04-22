"""
成本优化配置模块
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os


@dataclass
class CostConfig:
    """成本优化配置"""
    
    # ============ 缓存配置 ============
    cache_enabled: bool = True  # 是否启用缓存
    cache_ttl: int = 3600  # 缓存有效期(秒)
    cache_max_size: int = 1000  # 最大缓存条数
    similarity_threshold: float = 0.95  # 语义缓存相似度阈值
    exact_cache_enabled: bool = True  # 精确缓存
    semantic_cache_enabled: bool = True  # 语义缓存
    
    # ============ 压缩配置 ============
    compress_enabled: bool = True  # 是否启用压缩
    compress_html: bool = True  # 清理HTML标签
    compress_json: bool = True  # 压缩JSON空白
    compress_whitespace: bool = True  # 规范化空白字符
    compress_dedent: bool = True  # 去除冗余缩进
    
    # ============ 监控配置 ============
    monitor_only: bool = False  # 仅监控，不优化
    budget_alert: Optional[float] = None  # 预算告警阈值 ($)
    budget_period: str = "monthly"  # 预算周期: daily/weekly/monthly
    report_interval: int = 3600  # 报告生成间隔(秒)
    enable_cost_tracking: bool = True  # 启用成本追踪
    
    # ============ 存储配置 ============
    persist_cache: bool = True  # 持久化缓存
    storage_path: str = "./.cost_cache"  # 缓存存储路径
    log_requests: bool = True  # 记录请求日志
    
    # ============ 高级配置 ============
    custom_pricing: Dict[str, Dict[str, float]] = field(default_factory=dict)  # 自定义定价
    fallback_model: str = "gpt-3.5-turbo"  # 降级模型
    timeout: int = 60  # 请求超时(秒)
    
    def __post_init__(self):
        """验证配置"""
        if self.similarity_threshold < 0 or self.similarity_threshold > 1:
            raise ValueError("similarity_threshold必须在0-1之间")
        
        if self.cache_ttl <= 0:
            raise ValueError("cache_ttl必须大于0")
        
        if self.cache_max_size <= 0:
            raise ValueError("cache_max_size必须大于0")
        
        # 确保存储目录存在
        if self.persist_cache and not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cache_max_size": self.cache_max_size,
            "similarity_threshold": self.similarity_threshold,
            "compress_enabled": self.compress_enabled,
            "budget_alert": self.budget_alert,
            "storage_path": self.storage_path,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CostConfig":
        """从字典创建"""
        return cls(**data)
    
    @classmethod
    def production(cls) -> "CostConfig":
        """生产环境配置"""
        return cls(
            cache_enabled=True,
            compress_enabled=True,
            persist_cache=True,
            log_requests=True,
            budget_alert=100.0,
        )
    
    @classmethod
    def development(cls) -> "CostConfig":
        """开发环境配置"""
        return cls(
            cache_enabled=True,
            compress_enabled=True,
            persist_cache=False,
            log_requests=True,
            monitor_only=True,  # 开发环境仅监控
        )
    
    @classmethod
    def minimal(cls) -> "CostConfig":
        """最小配置"""
        return cls(
            cache_enabled=True,
            compress_enabled=False,
            persist_cache=False,
            log_requests=False,
            monitor_only=True,
        )
