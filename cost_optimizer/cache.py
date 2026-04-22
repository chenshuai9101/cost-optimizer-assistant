"""
缓存管理模块
"""

from dataclasses import dataclass
from typing import Dict, Optional, Any, Callable, Awaitable, Union
from collections import OrderedDict
import time
import hashlib
import asyncio
import json
import os


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    access_count: int = 0
    last_accessed: float = 0
    
    def is_expired(self, ttl: int) -> bool:
        return time.time() - self.created_at > ttl


class ExactCache:
    """精确匹配缓存 (LRU)"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
    
    def _make_key(self, prompt: str, model: str) -> str:
        """生成缓存键"""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def get(self, prompt: str, model: str) -> Optional[Any]:
        """获取缓存"""
        key = self._make_key(prompt, model)
        
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # 检查过期
        if entry.is_expired(self.ttl):
            del self._cache[key]
            return None
        
        # 更新访问顺序 (LRU)
        self._cache.move_to_end(key)
        entry.access_count += 1
        entry.last_accessed = time.time()
        
        return entry.value
    
    def set(self, prompt: str, model: str, value: Any):
        """设置缓存"""
        key = self._make_key(prompt, model)
        
        # 如果已存在，更新值
        if key in self._cache:
            self._cache[key].value = value
            self._cache.move_to_end(key)
            return
        
        # 如果超过容量，删除最旧的
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            last_accessed=time.time()
        )
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    @property
    def size(self) -> int:
        return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        return {
            "size": self.size,
            "max_size": self.max_size,
            "ttl": self.ttl,
        }


class SemanticCache:
    """语义缓存 (基于相似度)"""
    
    def __init__(
        self,
        max_size: int = 500,
        ttl: int = 3600,
        similarity_threshold: float = 0.95
    ):
        self.max_size = max_size
        self.ttl = ttl
        self.threshold = similarity_threshold
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._embeddings: Dict[str, list] = {}  # 简化版:使用hash代替embedding
    
    def _make_key(self, content: str) -> str:
        """生成语义键 (简化:使用内容hash)"""
        # 实际生产中应使用真实的embedding
        # 这里用n-gram哈希作为简化
        words = content.lower().split()
        ngrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        key = hashlib.md5('|'.join(ngrams[:20]).encode()).hexdigest()
        return key
    
    def _compute_similarity(self, key1: str, key2: str) -> float:
        """计算相似度 (简化实现)"""
        # 实际生产中应使用向量相似度
        # 这里简化为字符重叠度
        set1, set2 = set(key1), set(key2)
        if not set1 or not set2:
            return 0.0
        return len(set1 & set2) / len(set1 | set2)
    
    def get(self, prompt: str) -> Optional[Any]:
        """获取最相似的缓存"""
        key = self._make_key(prompt)
        
        best_match = None
        best_score = 0.0
        
        for cache_key, entry in self._cache.items():
            if entry.is_expired(self.ttl):
                continue
            
            score = self._compute_similarity(key, cache_key)
            if score >= self.threshold and score > best_score:
                best_score = score
                best_match = entry
        
        if best_match:
            return best_match.value
        return None
    
    def set(self, prompt: str, value: Any):
        """设置缓存"""
        key = self._make_key(prompt)
        
        if key in self._cache:
            self._cache[key].value = value
            self._cache.move_to_end(key)
            return
        
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time()
        )
    
    def clear(self):
        self._cache.clear()
    
    @property
    def size(self) -> int:
        return len(self._cache)


class CacheManager:
    """缓存管理器 - 支持多层缓存"""
    
    def __init__(
        self,
        exact_cache: Optional[ExactCache] = None,
        semantic_cache: Optional[SemanticCache] = None
    ):
        self.exact = exact_cache or ExactCache()
        self.semantic = semantic_cache or SemanticCache()
        self.stats = {
            "exact_hits": 0,
            "semantic_hits": 0,
            "misses": 0,
        }
    
    async def get_or_compute(
        self,
        prompt: str,
        model: str,
        compute_fn: Callable[[], Awaitable[Any]]
    ) -> tuple[Any, bool]:
        """
        获取缓存或计算新值
        返回: (结果, 是否命中缓存)
        """
        # L1: 精确缓存
        cached = self.exact.get(prompt, model)
        if cached is not None:
            self.stats["exact_hits"] += 1
            return cached, True
        
        # L2: 语义缓存
        cached = self.semantic.get(prompt)
        if cached is not None:
            self.stats["semantic_hits"] += 1
            # 回填L1
            self.exact.set(prompt, model, cached)
            return cached, True
        
        # 未命中: 计算
        self.stats["misses"] += 1
        result = await compute_fn()
        
        # 存入双层缓存
        self.exact.set(prompt, model, result)
        self.semantic.set(prompt, result)
        
        return result, False
    
    def get_hit_rate(self) -> float:
        """获取命中率"""
        total = self.stats["exact_hits"] + self.stats["semantic_hits"] + self.stats["misses"]
        if total == 0:
            return 0.0
        return (self.stats["exact_hits"] + self.stats["semantic_hits"]) / total
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "exact_cache": self.exact.get_stats(),
            "semantic_cache": {
                "size": self.semantic.size,
                "threshold": self.semantic.threshold,
            },
            "hits": self.stats,
            "hit_rate": f"{self.get_hit_rate():.1%}",
        }
    
    def clear(self):
        """清空所有缓存"""
        self.exact.clear()
        self.semantic.clear()
        self.stats = {"exact_hits": 0, "semantic_hits": 0, "misses": 0}
