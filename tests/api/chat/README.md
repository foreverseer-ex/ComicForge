# 聊天功能测试包

本测试包专门测试聊天相关的所有功能。

## 测试文件结构

```
tests/api/chat/
├── __init__.py                      # 包初始化
├── conftest.py                      # 共享 fixtures
├── test_chat_invoke.py              # 直接聊天（invoke模式）
├── test_chat_invoke_with_tools.py   # 直接聊天+工具调用
├── test_chat_stream.py               # 流式传输
├── test_chat_stream_with_tools.py   # 流式传输+工具调用
├── test_chat_iteration.py            # 迭代对话
└── test_chat_summary.py              # 聊天总结
```

## 测试说明

### 1. 直接聊天（invoke模式）

**文件**: `test_chat_invoke.py`

测试非流式的直接聊天功能，使用 `simple_chat()` 方法。

**测试用例**:
- `test_simple_chat_basic`: 基本直接聊天
- `test_simple_chat_with_context`: 带上下文的直接聊天
- `test_simple_chat_error_handling`: 错误处理

### 2. 直接聊天+工具调用

**文件**: `test_chat_invoke_with_tools.py`

测试在直接聊天过程中工具调用的功能。

**测试用例**:
- `test_chat_with_tool_call_get_project`: 测试调用 get_project 工具
- `test_chat_with_tool_call_create_memory`: 测试调用 create_memory 工具
- `test_tool_call_result_stored`: 测试工具调用结果是否正确存储

### 3. 流式传输

**文件**: `test_chat_stream.py`

测试 SSE 流式响应功能。

**测试用例**:
- `test_stream_chat_basic`: 基本流式聊天
- `test_stream_chat_real_time`: 测试流式聊天的实时性
- `test_stream_chat_database_update`: 测试流式聊天时数据库实时更新

### 4. 流式传输+工具调用

**文件**: `test_chat_stream_with_tools.py`

测试在流式响应过程中工具调用的功能。

**测试用例**:
- `test_stream_chat_with_tool_call`: 测试流式聊天时工具调用
- `test_stream_chat_tool_call_real_time_update`: 测试工具调用实时更新到数据库
- `test_stream_chat_multiple_tool_calls`: 测试多个工具调用

### 5. 迭代对话

**文件**: `test_chat_iteration.py`

测试迭代式对话功能。

**测试用例**:
- `test_iteration_chat_basic`: 基本迭代对话
- `test_iteration_chat_progress_update`: 测试迭代进度更新
- `test_iteration_chat_final_operation`: 测试迭代的最终操作

### 6. 聊天总结

**文件**: `test_chat_summary.py`

测试自动生成聊天摘要的功能。

**测试用例**:
- `test_summary_generation_trigger`: 测试总结触发条件
- `test_summary_usage_in_chat`: 测试总结在后续对话中的使用
- `test_summary_storage`: 测试总结的存储
- `test_summary_retrieval`: 测试总结的检索

## 运行测试

### 运行所有聊天测试

```bash
uv run pytest tests/api/chat/ -v
```

### 运行特定测试文件

```bash
# 测试直接聊天
uv run pytest tests/api/chat/test_chat_invoke.py -v

# 测试流式传输
uv run pytest tests/api/chat/test_chat_stream.py -v

# 测试迭代对话
uv run pytest tests/api/chat/test_chat_iteration.py -v
```

### 运行特定测试用例

```bash
# 测试基本直接聊天
uv run pytest tests/api/chat/test_chat_invoke.py::TestInvokeChat::test_simple_chat_basic -v

# 测试流式+工具调用
uv run pytest tests/api/chat/test_chat_stream_with_tools.py::TestStreamChatWithTools::test_stream_chat_with_tool_call -v
```

## 注意事项

1. **LLM 服务配置**: 测试需要配置 LLM 服务（API Key 等），如果未配置或网络不可用，测试会跳过
2. **数据库**: 测试会自动初始化数据库，测试数据会写入实际数据库文件
3. **网络依赖**: 部分测试需要网络连接 LLM API，如果网络不可用会跳过相关测试
4. **异步测试**: 测试使用 `asyncio.run()` 来运行异步函数，确保正确处理异步代码

## 测试覆盖

- ✅ 直接聊天（invoke模式）
- ✅ 直接聊天+工具调用
- ✅ 流式传输（stream模式）
- ✅ 流式传输+工具调用
- ✅ 迭代对话
- ✅ 聊天总结

所有测试都包含错误处理和网络异常的跳过逻辑。
