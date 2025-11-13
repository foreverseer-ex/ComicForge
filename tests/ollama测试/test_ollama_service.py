"""
Ollama 独立功能测试。

独立测试 Ollama SDK 的各项功能，不依赖项目内部模块：
- 获取模型列表（ollama.list()）
- 获取模型列表（使用 Client）
- 测试模型对话
- 测试错误处理
"""
import sys
import os
import asyncio

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import ollama
from loguru import logger


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"


def test_get_ollama_models_direct():
    """测试 1: 使用 ollama.list() 直接获取模型列表"""
    logger.info("=" * 60)
    logger.info("测试 1: 使用 ollama.list() 直接获取模型列表")
    logger.info("=" * 60)
    
    try:
        # 使用默认的 ollama.list()
        data = ollama.list()
        
        # 提取模型名称列表
        models = []
        if hasattr(data, 'models'):
            models = [model.name for model in data.models]
        elif isinstance(data, dict):
            models = [model.get('name') for model in data.get('models', []) if model.get('name')]
        
        logger.info(f"✅ 成功获取 {len(models)} 个 Ollama 模型")
        for i, model in enumerate(models, 1):
            logger.info(f"  {i}. {model}")
        
        assert len(models) > 0, "应该至少有一个 Ollama 模型"
        return models
        
    except Exception as e:
        logger.error(f"❌ 获取模型列表失败: {e}")
        logger.error(f"   请确保 Ollama 服务正在运行（{DEFAULT_OLLAMA_BASE_URL}）")
        raise


def test_get_ollama_models_with_client():
    """测试 2: 使用 Client(host=base_url).list() 获取模型列表"""
    logger.info("=" * 60)
    logger.info("测试 2: 使用 Client(host=base_url).list() 获取模型列表")
    logger.info("=" * 60)
    
    try:
        base_url = DEFAULT_OLLAMA_BASE_URL
        
        # 使用 Client 指定 host
        client = ollama.Client(host=base_url)
        data = client.list()
        
        # 提取模型名称列表
        models = []
        if hasattr(data, 'models'):
            models = [model.name for model in data.models]
        elif isinstance(data, dict):
            models = [model.get('name') for model in data.get('models', []) if model.get('name')]
        
        logger.info(f"✅ 成功获取 {len(models)} 个 Ollama 模型 (base_url: {base_url})")
        for i, model in enumerate(models, 1):
            logger.info(f"  {i}. {model}")
        
        assert len(models) > 0, "应该至少有一个 Ollama 模型"
        return models
        
    except Exception as e:
        logger.error(f"❌ 获取模型列表失败: {e}")
        logger.error(f"   请确保 Ollama 服务正在运行（{base_url}）")
        raise


def test_get_ollama_models_async():
    """测试 3: 使用 AsyncClient 异步获取模型列表"""
    logger.info("=" * 60)
    logger.info("测试 3: 使用 AsyncClient 异步获取模型列表")
    logger.info("=" * 60)
    
    async def async_get_models():
        try:
            base_url = DEFAULT_OLLAMA_BASE_URL
            
            # 使用 AsyncClient
            from ollama import AsyncClient
            client = AsyncClient(host=base_url)
            data = await client.list()
            
            # 提取模型名称列表
            models = []
            if hasattr(data, 'models'):
                models = [model.name for model in data.models]
            elif isinstance(data, dict):
                models = [model.get('name') for model in data.get('models', []) if model.get('name')]
            
            logger.info(f"✅ 异步成功获取 {len(models)} 个 Ollama 模型")
            for i, model in enumerate(models, 1):
                logger.info(f"  {i}. {model}")
            
            assert len(models) > 0, "应该至少有一个 Ollama 模型"
            return models
            
        except Exception as e:
            logger.error(f"❌ 异步获取模型列表失败: {e}")
            logger.error(f"   请确保 Ollama 服务正在运行（{base_url}）")
            raise
    
    return asyncio.run(async_get_models())


def test_ollama_chat_sync():
    """测试 4: 同步方式调用模型对话"""
    logger.info("=" * 60)
    logger.info("测试 4: 同步方式调用模型对话")
    logger.info("=" * 60)
    
    try:
        # 先获取可用模型
        models = [m.model for m in ollama.list()]

        if not models:
            logger.warning("⚠️ 没有可用模型，跳过对话测试")
            return None
        
        model_name = models[0]
        logger.info(f"使用模型: {model_name}")
        
        # 测试简单对话
        message = "你好，请用一句话介绍你自己"
        logger.info(f"发送消息: {message}")
        
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': message
                }
            ]
        )
        
        # 提取回复
        reply = response.get('message', {}).get('content', '') if isinstance(response, dict) else ''
        if not reply and hasattr(response, 'message'):
            reply = response.message.content if hasattr(response.message, 'content') else str(response.message)
        
        logger.info(f"✅ 收到回复: {len(reply)} 字符")
        logger.info(f"回复内容: {reply[:200]}...")
        
        assert len(reply) > 0, "应该收到回复"
        return reply
        
    except Exception as e:
        logger.error(f"❌ 同步对话测试失败: {e}")
        logger.error(f"   请确保 Ollama 服务正在运行并且模型已下载")
        raise


async def test_ollama_chat_async():
    """测试 5: 异步方式调用模型对话"""
    logger.info("=" * 60)
    logger.info("测试 5: 异步方式调用模型对话")
    logger.info("=" * 60)
    
    try:
        from ollama import AsyncClient
        
        # 先获取可用模型
        client = AsyncClient(host=DEFAULT_OLLAMA_BASE_URL)
        data = await client.list()
        
        models = []
        if hasattr(data, 'models') and len(data.models) > 0:
            models = [model.name for model in data.models]
        elif isinstance(data, dict) and data.get('models'):
            models = [model.get('name') for model in data.get('models', []) if model.get('name')]
        
        if not models:
            logger.warning("⚠️ 没有可用模型，跳过对话测试")
            return None
        
        model_name = models[0]
        logger.info(f"使用模型: {model_name}")
        
        # 测试简单对话
        message = "你好，请用一句话介绍你自己"
        logger.info(f"发送消息: {message}")
        
        response = await client.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': message
                }
            ]
        )
        
        # 提取回复
        reply = response.get('message', {}).get('content', '') if isinstance(response, dict) else ''
        if not reply and hasattr(response, 'message'):
            reply = response.message.content if hasattr(response.message, 'content') else str(response.message)
        
        logger.info(f"✅ 异步收到回复: {len(reply)} 字符")
        logger.info(f"回复内容: {reply[:200]}...")
        
        assert len(reply) > 0, "应该收到回复"
        return reply
        
    except Exception as e:
        logger.error(f"❌ 异步对话测试失败: {e}")
        logger.error(f"   请确保 Ollama 服务正在运行并且模型已下载")
        raise


async def test_ollama_chat_stream():
    """测试 6: 流式对话（异步）"""
    logger.info("=" * 60)
    logger.info("测试 6: 流式对话（异步）")
    logger.info("=" * 60)
    
    try:
        from ollama import AsyncClient
        
        # 先获取可用模型
        client = AsyncClient(host=DEFAULT_OLLAMA_BASE_URL)
        data = await client.list()
        
        models = []
        if hasattr(data, 'models') and len(data.models) > 0:
            models = [model.name for model in data.models]
        elif isinstance(data, dict) and data.get('models'):
            models = [model.get('name') for model in data.get('models', []) if model.get('name')]
        
        if not models:
            logger.warning("⚠️ 没有可用模型，跳过流式对话测试")
            return None
        
        model_name = models[0]
        logger.info(f"使用模型: {model_name}")
        
        # 测试流式对话
        message = "请简单介绍一下人工智能"
        logger.info(f"发送消息: {message}")
        logger.info("接收流式回复:")
        logger.info("-" * 60)
        
        content_parts = []
        async for chunk in await client.chat(
            model=model_name,
            messages=[
                {
                    'role': 'user',
                    'content': message
                }
            ],
            stream=True
        ):
            # 提取内容
            content = ''
            if isinstance(chunk, dict):
                content = chunk.get('message', {}).get('content', '')
            elif hasattr(chunk, 'message'):
                content = chunk.message.content if hasattr(chunk.message, 'content') else str(chunk.message)
            
            if content:
                content_parts.append(content)
                print(content, end='', flush=True)
        
        print()  # 换行
        logger.info("-" * 60)
        
        full_content = ''.join(content_parts)
        logger.info(f"✅ 流式接收完成，共 {len(full_content)} 字符")
        logger.info(f"完整内容预览: {full_content[:200]}...")
        
        assert len(full_content) > 0, "应该收到回复"
        return full_content
        
    except Exception as e:
        logger.error(f"❌ 流式对话测试失败: {e}")
        logger.error(f"   请确保 Ollama 服务正在运行并且模型已下载")
        raise


def test_ollama_error_handling_invalid_model():
    """测试 7: 错误处理 - 不存在的模型"""
    logger.info("=" * 60)
    logger.info("测试 7: 错误处理 - 不存在的模型")
    logger.info("=" * 60)
    
    try:
        invalid_model = "non-existent-model-12345-does-not-exist"
        logger.info(f"尝试使用不存在的模型: {invalid_model}")
        
        response = ollama.chat(
            model=invalid_model,
            messages=[
                {
                    'role': 'user',
                    'content': "你好"
                }
            ]
        )
        
        logger.warning("⚠️ 未抛出预期异常，模型可能被自动下载或返回了响应")
        logger.info(f"响应: {response}")
        
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e)
        
        logger.info(f"✅ 正确捕获错误: {error_type}: {error_str}")
        
        # 检查错误类型
        if "ResponseError" in error_type or "status code" in error_str.lower():
            logger.info(f"   错误类型: HTTP 响应错误")
            # 尝试提取状态码
            import re
            match = re.search(r'status code[:\s]+(\d+)', error_str)
            if match:
                status_code = match.group(1)
                logger.info(f"   状态码: {status_code}")
        elif "not found" in error_str.lower() or "不存在" in error_str.lower():
            logger.info(f"   错误类型: 模型不存在")
        else:
            logger.info(f"   错误类型: {error_type}")


def test_ollama_error_handling_invalid_host():
    """测试 8: 错误处理 - 无效的主机地址"""
    logger.info("=" * 60)
    logger.info("测试 8: 错误处理 - 无效的主机地址")
    logger.info("=" * 60)
    
    try:
        invalid_host = "http://127.0.0.1:99999"  # 不存在的端口
        logger.info(f"尝试连接到无效地址: {invalid_host}")
        
        client = ollama.Client(host=invalid_host)
        data = client.list()
        
        logger.warning("⚠️ 未抛出预期异常")
        
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e)
        
        logger.info(f"✅ 正确捕获错误: {error_type}: {error_str}")
        
        # 检查错误类型
        if "connection" in error_str.lower() or "connect" in error_str.lower():
            logger.info(f"   错误类型: 连接错误")
        elif "ResponseError" in error_type:
            logger.info(f"   错误类型: HTTP 响应错误")
        else:
            logger.info(f"   错误类型: {error_type}")


def run_all_tests():
    """运行所有测试"""
    logger.info("")
    logger.info("🚀 开始运行 Ollama 独立功能测试...")
    logger.info("")
    
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0
    }
    
    # 测试 1: 获取模型列表（直接）
    try:
        test_get_ollama_models_direct()
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 1 失败: {e}")
        logger.info("")
    
    # 测试 2: 获取模型列表（Client）
    try:
        test_get_ollama_models_with_client()
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 2 失败: {e}")
        logger.info("")
    
    # 测试 3: 异步获取模型列表
    try:
        test_get_ollama_models_async()
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 3 失败: {e}")
        logger.info("")
    
    # 测试 4: 同步对话
    try:
        test_ollama_chat_sync()
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 4 失败: {e}")
        logger.info("")
    
    # 测试 5: 异步对话
    try:
        asyncio.run(test_ollama_chat_async())
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 5 失败: {e}")
        logger.info("")
    
    # 测试 6: 流式对话
    try:
        asyncio.run(test_ollama_chat_stream())
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 6 失败: {e}")
        logger.info("")
    
    # 测试 7: 错误处理 - 无效模型
    try:
        test_ollama_error_handling_invalid_model()
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 7 失败: {e}")
        logger.info("")
    
    # 测试 8: 错误处理 - 无效主机
    try:
        test_ollama_error_handling_invalid_host()
        results['passed'] += 1
        logger.info("")
    except Exception as e:
        results['failed'] += 1
        logger.error(f"❌ 测试 8 失败: {e}")
        logger.info("")
    
    # 输出测试总结
    logger.info("=" * 60)
    logger.info("📊 测试总结")
    logger.info("=" * 60)
    logger.info(f"✅ 通过: {results['passed']}")
    logger.info(f"❌ 失败: {results['failed']}")
    logger.info(f"⏭️  跳过: {results['skipped']}")
    logger.info(f"📈 总计: {results['passed'] + results['failed'] + results['skipped']}")
    logger.info("")
    
    if results['failed'] == 0:
        logger.info("🎉 所有测试通过！")
    else:
        logger.warning(f"⚠️ 有 {results['failed']} 个测试失败")
    
    logger.info("")


if __name__ == "__main__":
    models = [m.model for m in ollama.list().models]