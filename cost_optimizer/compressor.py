"""
Prompt压缩模块
"""

import re
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CompressionResult:
    """压缩结果"""
    original: str
    compressed: str
    original_tokens_estimate: int
    compressed_tokens_estimate: int
    savings_percent: float
    
    @property
    def tokens_saved(self) -> int:
        return self.original_tokens_estimate - self.compressed_tokens_estimate


class PromptCompressor:
    """Prompt压缩器"""
    
    def __init__(
        self,
        compress_html: bool = True,
        compress_json: bool = True,
        compress_whitespace: bool = True,
        compress_dedent: bool = True,
    ):
        self.compress_html = compress_html
        self.compress_json = compress_json
        self.compress_whitespace = compress_whitespace
        self.compress_dedent = compress_dedent
        
        # HTML标签模式
        self.html_pattern = re.compile(r'<[^>]+>')
        # 多余空白模式
        self.whitespace_pattern = re.compile(r'[ \t]+')
        # 多余换行模式
        self.newline_pattern = re.compile(r'\n{3,}')
    
    def compress(self, text: str) -> str:
        """执行所有压缩"""
        result = text
        
        if self.compress_html:
            result = self.compress_html_tags(result)
        
        if self.compress_whitespace:
            result = self.normalize_whitespace(result)
        
        if self.compress_dedent:
            result = self.dedent(result)
        
        if self.compress_json:
            result = self.compress_json_content(result)
        
        return result
    
    def compress_html_tags(self, text: str) -> str:
        """移除HTML标签"""
        # 保留换行相关的标签
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        # 移除其他HTML标签
        text = self.html_pattern.sub('', text)
        return text.strip()
    
    def normalize_whitespace(self, text: str) -> str:
        """规范化空白字符"""
        # 合并多余空格
        text = self.whitespace_pattern.sub(' ', text)
        # 合并多余换行
        text = self.newline_pattern.sub('\n\n', text)
        # 移除行首行尾空格
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)
    
    def dedent(self, text: str) -> str:
        """去除冗余缩进"""
        lines = text.split('\n')
        if not lines:
            return text
        
        # 找出最小缩进
        min_indent = float('inf')
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                min_indent = min(min_indent, indent)
        
        if min_indent == float('inf') or min_indent == 0:
            return text
        
        # 移除公共缩进
        result_lines = []
        for line in lines:
            if line.strip():
                result_lines.append(line[min_indent:])
            else:
                result_lines.append('')
        
        return '\n'.join(result_lines).strip()
    
    def compress_json_content(self, text: str) -> str:
        """压缩JSON内容"""
        try:
            # 尝试解析为JSON
            obj = json.loads(text)
            
            # 移除空值和null
            cleaned = self._clean_json(obj)
            
            # 压缩格式
            return json.dumps(cleaned, separators=(',', ':'))
        except (json.JSONDecodeError, TypeError):
            return text
    
    def _clean_json(self, obj: Any) -> Any:
        """清理JSON对象"""
        if isinstance(obj, dict):
            return {
                k: self._clean_json(v)
                for k, v in obj.items()
                if v is not None and v != "" and v != []
            }
        elif isinstance(obj, list):
            return [self._clean_json(item) for item in obj if item is not None]
        return obj
    
    def compress_schema(self, schema: Dict) -> Dict:
        """压缩API Schema"""
        if not isinstance(schema, dict):
            return schema
        
        # 简化description
        if 'description' in schema:
            # 保留首句
            desc = schema['description']
            first_sentence = re.split(r'[.!?]', desc)[0]
            schema['description'] = first_sentence.strip() + '.'
        
        # 递归处理
        if 'properties' in schema:
            for prop in schema['properties'].values():
                self.compress_schema(prop)
        
        if 'items' in schema:
            self.compress_schema(schema['items'])
        
        return schema
    
    def estimate_tokens(self, text: str) -> int:
        """估算token数量 (简化:按字符/4估算)"""
        # 实际应使用tiktoken等精确计算
        return len(text) // 4 + len(text.split())
    
    def compress_with_report(self, text: str) -> CompressionResult:
        """压缩并生成报告"""
        original_tokens = self.estimate_tokens(text)
        compressed = self.compress(text)
        compressed_tokens = self.estimate_tokens(compressed)
        
        savings = (original_tokens - compressed_tokens) / original_tokens * 100 if original_tokens > 0 else 0
        
        return CompressionResult(
            original=text,
            compressed=compressed,
            original_tokens_estimate=original_tokens,
            compressed_tokens_estimate=compressed_tokens,
            savings_percent=savings
        )
    
    def get_suggestions(self, text: str) -> List[str]:
        """获取优化建议"""
        suggestions = []
        
        if self.html_pattern.search(text):
            suggestions.append("检测到HTML标签，可清理以节省token")
        
        if self.whitespace_pattern.search(text):
            suggestions.append("存在多余空白字符，可规范化")
        
        if '\n\n\n' in text:
            suggestions.append("存在多余换行，可精简")
        
        # 检测JSON
        if text.strip().startswith('{') or text.strip().startswith('['):
            suggestions.append("检测到JSON，可压缩格式")
        
        return suggestions


# 预定义压缩策略
class CompressionStrategy:
    """压缩策略"""
    
    @staticmethod
    def minimal(compressor: PromptCompressor):
        """最小压缩: 仅规范化空白"""
        compressor.compress_html = False
        compressor.compress_json = False
        compressor.compress_whitespace = True
        compressor.compress_dedent = True
    
    @staticmethod
    def standard(compressor: PromptCompressor):
        """标准压缩: 保留HTML语义"""
        compressor.compress_html = True
        compressor.compress_json = True
        compressor.compress_whitespace = True
        compressor.compress_dedent = True
    
    @staticmethod
    def aggressive(compressor: PromptCompressor):
        """激进压缩: 移除所有非必要内容"""
        compressor.compress_html = True
        compressor.compress_json = True
        compressor.compress_whitespace = True
        compressor.compress_dedent = True
