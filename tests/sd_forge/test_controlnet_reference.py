"""
测试 SD-Forge 的 ControlNet reference_only 功能。

这个测试文件不依赖 api 模块，直接调用 SD-Forge 的 SD-WebUI API（通过 webuiapi SDK）。
"""
import httpx
import pytest
from pathlib import Path
from PIL import Image
from webuiapi import WebUIApi, ControlNetUnit


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


def _get_controlnet_modules(base_url: str) -> list:
    """获取可用的 ControlNet 预处理器模块列表。
    
    :param base_url: 服务器基础URL
    :return: ControlNet 模块列表
    """
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(f"{base_url}/controlnet/module_list")
            r.raise_for_status()
            modules = r.json()
            return modules.get("module_list", [])
    except Exception:
        return []


def _get_controlnet_models(base_url: str) -> list:
    """获取可用的 ControlNet 模型列表。
    
    :param base_url: 服务器基础URL
    :return: ControlNet 模型列表（可能只包含 "None"）
    """
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(f"{base_url}/controlnet/model_list")
            r.raise_for_status()
            models = r.json()
            return models.get("model_list", [])
    except Exception:
        return []


def _get_sd_models(base_url: str) -> list:
    """获取可用的基础模型列表。
    
    :param base_url: 服务器基础URL
    :return: 基础模型列表
    """
    try:
        with httpx.Client(timeout=5.0) as c:
            r = c.get(f"{base_url}/sdapi/v1/sd-models")
            r.raise_for_status()
            models = r.json()
            return models if isinstance(models, list) else []
    except Exception:
        return []


def _create_api_client(base_url: str) -> WebUIApi:
    """根据 base_url 创建 WebUIApi 客户端。"""
    base = base_url.rstrip("/")
    return WebUIApi(baseurl=f"{base}/sdapi/v1")


@pytest.mark.skipif(
    not _server_available("http://127.0.0.1:7860"),
    reason="sd-forge 服务器不可用"
)
def test_without_controlnet():
    """测试不使用 ControlNet 的生成（用于对比）。
    
    验证不使用 ControlNet 时是否仍然报错，以及生成的图像效果。
    """
    base_url = "http://127.0.0.1:7860"
    
    # 获取基础模型列表
    sd_models = _get_sd_models(base_url)
    if not sd_models:
        pytest.skip("没有可用的基础模型")
    sd_model_title = sd_models[2].get("title", "") if isinstance(sd_models[0], dict) else str(sd_models[0])
    print(f"✅ 使用基础模型: {sd_model_title}")
    
    api = _create_api_client(base_url)
    print(f"正在使用基础模型={sd_model_title} 生成图像（不使用 ControlNet）...")
    result = api.txt2img(
        prompt="1girl,",
        negative_prompt="",
        width=1024,
        height=1024,
        steps=20,
        cfg_scale=5,
        sampler_name="DPM++ 2M SDE",
        seed=-1,
        batch_size=4,
        n_iter=1,
        send_images=True,
        save_images=False,
        override_settings={
            "sd_model_checkpoint": sd_model_title
        },
    )

    assert result.images and len(result.images) >= 4

    output_dir = Path(__file__).parent
    for i, pil_image in enumerate(result.images, start=1):
        output_file = output_dir / f"test_without_controlnet_{i}.png"
        pil_image.save(output_file)
        print(f"✅ 生成的图像 {i} 已保存到: {output_file}")

    print("✅ 不使用 ControlNet 的测试通过：图像已成功生成并保存")


@pytest.mark.skipif(
    not _server_available("http://127.0.0.1:7860"),
    reason="sd-forge 服务器不可用"
)
def test_controlnet_reference_only():
    """测试 ControlNet reference_only 功能（使用参考图像文件）。
    
    验证从文件读取参考图像并用于 ControlNet reference_only：
    1. 从文件读取参考图像
    2. 转换为 base64
    3. 使用 ControlNet reference_only 生成新图像（生成4张以观察随机性）
    
    错误分析：
    - KeyError: 0 发生在 ControlNet 扩展的 postprocess_batch_list 中
    - 错误位置：self.current_params[i]，说明 current_params 字典中没有键 0
    - 可能原因：ControlNet 扩展在处理参数时，没有正确初始化 current_params
    - 与"不像"的关联：虽然主要生成流程完成，但后处理步骤失败可能影响最终效果
    - 需要对比有无 ControlNet 的结果来判断是否真的应用了 ControlNet
    """
    base_url = "http://127.0.0.1:7860"
    
    # 检查 ControlNet 模块是否可用（reference_only 是预处理器模块，不是模型文件）
    controlnet_modules = _get_controlnet_modules(base_url)
    if "reference_only" not in controlnet_modules:
        pytest.skip("ControlNet reference_only 模块不可用，请确保已安装 ControlNet 扩展")
    
    # 获取可用的 ControlNet 模型列表
    controlnet_models = _get_controlnet_models(base_url)
    # 使用第一个可用的模型，如果没有则使用 None
    controlnet_model_name = controlnet_models[0] if controlnet_models and controlnet_models[0] != "None" else None
    module_name = "reference_only"
    
    # 获取基础模型列表
    sd_models = _get_sd_models(base_url)
    if not sd_models:
        pytest.skip("没有可用的基础模型")
    sd_model_title = sd_models[2].get("title", "") if isinstance(sd_models[0], dict) else str(sd_models[0])
    print(f"✅ 使用基础模型: {sd_model_title}")
    
    # 使用指定的参考图像文件
    test_image_path = Path(r"C:\Users\zxb\Desktop\00039-309053998.png")
    
    if not test_image_path.exists():
        pytest.skip(f"测试参考图像不存在: {test_image_path}")
    
    reference_image = Image.open(test_image_path).convert("RGB")
    print(f"✅ 已读取参考图像文件: {test_image_path}")

    api = _create_api_client(base_url)
    controlnet_unit = ControlNetUnit(
        image=reference_image,
        module=module_name,
        model=controlnet_model_name or "None",
        weight=1.0,
        resize_mode="Just Resize",
        low_vram=False,
        processor_res=0.5,
        threshold_a=0.5,
        threshold_b=0.5,
        guidance_start=0.0,
        guidance_end=1.0,
        control_mode=0,
        pixel_perfect=False,
        hr_option="Both",
        enabled=True,
    )

    print(f"正在使用基础模型={sd_model_title}, ControlNet module={module_name}, model={controlnet_model_name} 和文件参考图像生成图像...")
    result = api.txt2img(
        prompt="1girl,",
        negative_prompt="",
        width=1024,
        height=1024,
        steps=20,
        cfg_scale=5,
        sampler_name="DPM++ 2M SDE",
        seed=-1,
        batch_size=4,
        n_iter=1,
        send_images=True,
        save_images=False,
        override_settings={
            "sd_model_checkpoint": sd_model_title
        },
        controlnet_units=[controlnet_unit],
    )

    assert result.images and len(result.images) >= 4

    output_dir = Path(__file__).parent
    for i, pil_image in enumerate(result.images, start=1):
        output_file = output_dir / f"test_controlnet_reference_output_{i}.png"
        pil_image.save(output_file)
        print(f"✅ 生成的图像 {i} 已保存到: {output_file}")
    
    print("✅ ControlNet reference_only 测试通过：图像已成功生成并保存")
    print("💡 请对比生成的图像与参考图像的相似度，以及有无 ControlNet 的差异")


if __name__ == "__main__":
    """直接运行测试（不使用 pytest）"""
    print("=" * 60)
    print("SD-Forge ControlNet reference_only 测试")
    print("=" * 60)
    
    if not _server_available("http://127.0.0.1:7860"):
        print("❌ SD-Forge 服务器不可用，请确保服务器运行在 http://127.0.0.1:7860")
        exit(1)
    
    print("✅ SD-Forge 服务器可用")
    
    # # 运行测试
    # print("\n" + "=" * 60)
    # print("测试 1: 不使用 ControlNet（用于对比）")
    # print("=" * 60)
    # try:
    #     test_without_controlnet()
    #     print("✅ 测试 1 通过\n")
    # except pytest.skip.Exception as e:
    #     print(f"⏭️  测试 1 跳过: {e}\n")
    # except Exception as e:
    #     print(f"❌ 测试 1 失败: {e}\n")
    #     import traceback
    #     traceback.print_exc()
    
    print("=" * 60)
    print("测试 2: 使用 ControlNet reference_only")
    print("=" * 60)
    try:
        test_controlnet_reference_only()
        print("✅ 测试 2 通过\n")
    except pytest.skip.Exception as e:
        print(f"⏭️  测试 2 跳过: {e}\n")
    except Exception as e:
        print(f"❌ 测试 2 失败: {e}\n")
        import traceback
        traceback.print_exc()

    print("=" * 60)
    print("测试完成")
    print("=" * 60)
