---
name: cost-optimizer-assistant
description: cost optimizer assistant - OpenClaw AI Agent Skill
metadata:
  openclaw:
    emoji: 🔧
    aiFriendly: true
    plugAndPlay: true
    requires:
      minimal: true
    category: general
    tags: ['cost-optimizer-assistant']
version: '1.1.0'
---

# cost optimizer assistant

## 一、AI/Agent友好型设计

### 1.1 标准化的输入输出格式

**输入格式**：
```json
{
  "operation": "要执行的操作",
  "data": "输入数据",
  "options": {},
  "metadata": {
    "request_id": "唯一请求ID",
    "callback_url": "可选回调URL"
  }
}
```

**输出格式**：
```json
{
  "status": "success|error|processing",
  "result": "处理结果",
  "errors": [],
  "warnings": []
}
```

## 安装与兼容性

### 支持的平台
- ✅ **Claude Code** (v0.7.0+)
- ✅ **OpenClaw** (v1.0.0+)
- ✅ **Codex CLI** (latest)
- ✅ **Cursor** (latest)
- 🟡 **Claude Desktop** - 需要手动复制 SKILL.md 到项目目录

### 安装方式

```bash
# OpenClaw
clawhub install chenshuai9101/cost-optimizer-assistant

# Claude Code
claude mcp add chenshuai9101/cost-optimizer-assistant
```

## 结构化输出兼容性指南

如果LLM返回的JSON格式有误，按以下顺序修复:
1. 提取JSON块（去除 ```json 包裹）
2. 替换全角符号（"" → ""）
3. 去除尾部逗号
4. JSON解析失败时使用ast.literal_eval降级

## 边界声明

### NOT FOR
- 通用的代码开发任务
- 不具备完整输入数据的情况
- 实时数据流处理

## 快速上手

### 一分钟开始使用

```bash
cat > input.json << 'EOF'
{
  "operation": "process",
  "data": "<你的数据>",
  "options": {"retry_on_fail": true}
}
EOF
```
