"""
测试 SD-Forge 的 ControlNet reference_only 功能。

这个测试文件不依赖 api 模块，直接调用 SD-Forge 的 HTTP API。
"""
import base64
import httpx
import pytest
from pathlib import Path


def _server_available(base_url: str) -> bool:
    """检查 SD Forge 服务器是否可用。
    
    :param base_url: 服务器基础URL
    :return: 服务器是否可用
    """
    try:
        with httpx.Client(timeout=2.0) as c:
            r = c.get(f"{base_url}/sdapi/v1/sd-models")
            r.raise_for_status()
            return True
    except Exception:
        return False


def _get_controlnet_models(base_url: str) -> list:
    """获取可用的 ControlNet 模型列表。
    
    :param base_url: 服务器基础URL
    :return: ControlNet 模型列表
    """
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(f"{base_url}/controlnet/model_list")
            r.raise_for_status()
            models = r.json()
            return models.get("model_list", [])
    except Exception:
        return []


@pytest.mark.skipif(
    not _server_available("http://127.0.0.1:7860"),
    reason="sd-forge 服务器不可用"
)
def test_controlnet_reference_only_with_image():
    """测试 ControlNet reference_only 功能（使用参考图像）。
    
    验证 SD-Forge 的 ControlNet reference_only 是否能正常工作：
    1. 创建一张基础图像
    2. 使用该图像作为 reference_only 参考生成新图像
    3. 验证新生成的图像与参考图像在人物特征上保持一致
    """
    base_url = "http://127.0.0.1:7860"
    
    # 检查 ControlNet 是否可用
    controlnet_models = _get_controlnet_models(base_url)
    if "reference_only" not in controlnet_models and "reference" not in controlnet_models:
        pytest.skip("ControlNet reference_only 模型不可用，请确保已安装 ControlNet 扩展")
    
    # 使用 reference_only 或 reference（根据实际模型名称）
    model_name = "reference_only" if "reference_only" in controlnet_models else "reference"
    
    with httpx.Client(timeout=60.0) as client:
        # 1. 首先生成一张参考图像（一个角色的立绘）
        reference_payload = {
            "prompt": "1girl, beautiful, long hair, detailed face, masterpiece, best quality",
            "negative_prompt": "worst quality, bad quality, lowres, blurry",
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
            "sampler_name": "Euler a",
            "seed": 42,
            "n_iter": 1,
            "batch_size": 1,
            "send_images": True,
            "save_images": False,
        }
        
        print("正在生成参考图像...")
        ref_resp = client.post(f"{base_url}/sdapi/v1/txt2img", json=reference_payload)
        ref_resp.raise_for_status()
        ref_result = ref_resp.json()
        
        assert "images" in ref_result and isinstance(ref_result["images"], list)
        assert len(ref_result["images"]) >= 1
        
        reference_image_base64 = ref_result["images"][0]
        print(f"✅ 参考图像已生成，大小: {len(reference_image_base64)} 字符")
        
        # 2. 使用参考图像通过 ControlNet reference_only 生成新图像
        # 构建 ControlNet reference_only 参数
        controlnet_args = {
            "input_image": reference_image_base64,  # 参考图像的 base64 编码
            "model": model_name,  # ControlNet reference_only 模型
            "weight": 0.8,  # 参考权重
            "control_mode": 1,  # 1=更偏向提示词，但保持人物特征
            "resize_mode": 1,  # 1=缩放以适配
            "pixel_perfect": False,
            "processor_res": 512,
            "threshold_a": 64,
            "threshold_b": 64,
            "guidance_start": 0.0,
            "guidance_end": 1.0,
        }
        
        # 构建 txt2img 请求，包含 ControlNet 参数
        test_payload = {
            "prompt": "1girl, beautiful, long hair, detailed face, sitting, masterpiece, best quality",
            "negative_prompt": "worst quality, bad quality, lowres, blurry",
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
            "sampler_name": "Euler a",
            "seed": -1,  # 使用随机种子，但应该保持人物特征
            "n_iter": 1,
            "batch_size": 1,
            "send_images": True,
            "save_images": False,
            # 添加 alwayson_scripts 字段（ControlNet 扩展）
            "alwayson_scripts": {
                "controlnet": {
                    "args": [controlnet_args]
                }
            }
        }
        
        print(f"正在使用 ControlNet {model_name} 生成图像...")
        test_resp = client.post(f"{base_url}/sdapi/v1/txt2img", json=test_payload)
        test_resp.raise_for_status()
        test_result = test_resp.json()
        
        assert "images" in test_result and isinstance(test_result["images"], list)
        assert len(test_result["images"]) >= 1
        
        generated_image_base64 = test_result["images"][0]
        print(f"✅ 使用 ControlNet reference_only 生成的图像已生成，大小: {len(generated_image_base64)} 字符")
        
        # 3. 验证结果（基本验证：检查图像是否生成）
        assert len(generated_image_base64) > 0
        assert len(reference_image_base64) > 0
        
        # 注意：实际的视觉一致性验证需要图像比较算法
        # 这里只验证 API 调用是否成功和图像是否生成
        print("✅ ControlNet reference_only 测试通过：图像已成功生成")


@pytest.mark.skipif(
    not _server_available("http://127.0.0.1:7860"),
    reason="sd-forge 服务器不可用"
)
def test_controlnet_reference_only_with_file():
    """测试 ControlNet reference_only 功能（使用参考图像文件）。
    
    验证从文件读取参考图像并用于 ControlNet reference_only：
    1. 从文件读取参考图像
    2. 转换为 base64
    3. 使用 ControlNet reference_only 生成新图像
    """
    base_url = "http://127.0.0.1:7860"
    
    # 检查 ControlNet 是否可用
    controlnet_models = _get_controlnet_models(base_url)
    if "reference_only" not in controlnet_models and "reference" not in controlnet_models:
        pytest.skip("ControlNet reference_only 模型不可用，请确保已安装 ControlNet 扩展")
    
    # 使用 reference_only 或 reference（根据实际模型名称）
    model_name = "reference_only" if "reference_only" in controlnet_models else "reference"
    
    # 查找测试用的参考图像文件
    # 如果存在测试图像，使用它；否则跳过
    test_image_path = Path(__file__).parent / "test_reference_image.png"
    
    if not test_image_path.exists():
        pytest.skip(f"测试参考图像不存在: {test_image_path}，请准备一张测试图像")
    
    # 读取参考图像文件并转换为 base64
    with open(test_image_path, 'rb') as f:
        image_bytes = f.read()
    reference_image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    print(f"✅ 已读取参考图像文件: {test_image_path}，大小: {len(image_bytes)} 字节")
    
    # 构建 ControlNet reference_only 参数
    controlnet_args = {
        "input_image": reference_image_base64,
        "model": model_name,
        "weight": 0.8,
        "control_mode": 1,
        "resize_mode": 1,
        "pixel_perfect": False,
        "processor_res": 512,
        "threshold_a": 64,
        "threshold_b": 64,
        "guidance_start": 0.0,
        "guidance_end": 1.0,
    }
    
    # 构建 txt2img 请求
    test_payload = {
        "prompt": "1girl, beautiful, long hair, detailed face, standing, masterpiece, best quality",
        "negative_prompt": "worst quality, bad quality, lowres, blurry",
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg_scale": 7.0,
        "sampler_name": "Euler a",
        "seed": -1,
        "n_iter": 1,
        "batch_size": 1,
        "send_images": True,
        "save_images": False,
        "alwayson_scripts": {
            "controlnet": {
                "args": [controlnet_args]
            }
        }
    }
    
    with httpx.Client(timeout=60.0) as client:
        print(f"正在使用 ControlNet {model_name} 和文件参考图像生成图像...")
        test_resp = client.post(f"{base_url}/sdapi/v1/txt2img", json=test_payload)
        test_resp.raise_for_status()
        test_result = test_resp.json()
        
        assert "images" in test_result and isinstance(test_result["images"], list)
        assert len(test_result["images"]) >= 1
        
        generated_image_base64 = test_result["images"][0]
        print(f"✅ 使用文件参考图像和 ControlNet reference_only 生成的图像已生成")
        
        # 验证结果
        assert len(generated_image_base64) > 0
        print("✅ ControlNet reference_only（文件输入）测试通过：图像已成功生成")


if __name__ == "__main__":
    """直接运行测试（不使用 pytest）"""
    print("=" * 60)
    print("SD-Forge ControlNet reference_only 测试")
    print("=" * 60)
    
    if not _server_available("http://127.0.0.1:7860"):
        print("❌ SD-Forge 服务器不可用，请确保服务器运行在 http://127.0.0.1:7860")
        exit(1)
    
    print("✅ SD-Forge 服务器可用")
    
    # 运行测试
    try:
        print("\n测试 1: 使用生成的参考图像")
        test_controlnet_reference_only_with_image()
        print("✅ 测试 1 通过\n")
    except Exception as e:
        print(f"❌ 测试 1 失败: {e}\n")
    
    try:
        print("测试 2: 使用文件参考图像")
        test_controlnet_reference_only_with_file()
        print("✅ 测试 2 通过\n")
    except pytest.skip.Exception as e:
        print(f"⏭️  测试 2 跳过: {e}\n")
    except Exception as e:
        print(f"❌ 测试 2 失败: {e}\n")
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)

