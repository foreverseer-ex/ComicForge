"""
生成 PWA 图标脚本

从 public/icon.svg 的设计生成两个 PNG 图标文件：
- pwa-192x192.png (192x192 像素)
- pwa-512x512.png (512x512 像素)

使用方法：
    python tests/generate_pwa_icons.py

依赖：
    - Pillow: 已包含在项目依赖中（pyproject.toml）

说明：
    由于 Windows 上 cairo 库的复杂性，此脚本直接使用 Pillow 手动绘制图标。
    图标设计基于 icon.svg：蓝色背景 (#6366f1) + 白色书本图标。
    如果需要完整的 SVG 转换（包括 emoji），可以考虑使用在线工具。
"""
import sys
from pathlib import Path

# 设置输出编码（Windows 兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image


def generate_pwa_icons():
    """从 SVG 生成 PWA 图标 PNG 文件"""
    # 路径配置
    public_dir = project_root / "public"
    svg_path = public_dir / "icon.svg"
    
    # 检查 SVG 文件是否存在
    if not svg_path.exists():
        print(f"[错误] SVG 文件不存在: {svg_path}")
        sys.exit(1)
    
    # 要生成的图标尺寸
    sizes = [
        (192, 192, "pwa-192x192.png"),
        (512, 512, "pwa-512x512.png"),
    ]
    
    print(f"正在从 {svg_path} 生成 PWA 图标...\n")
    
    for width, height, filename in sizes:
        output_path = public_dir / filename
        
        try:
            # 由于 Windows 上 cairo 库的复杂性，我们直接使用 Pillow 手动绘制图标
            # 这基于 icon.svg 的设计：蓝色背景 (#6366f1) + 书本图标
            
            # 创建新的图像（蓝色背景）
            img = Image.new('RGB', (width, height), color='#6366f1')
            
            # 绘制书本图标
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            
            # 计算书本的位置和尺寸
            margin = width // 8
            book_width = width - 2 * margin
            book_height = height - 2 * margin
            book_x = margin
            book_y = margin + book_height // 4  # 稍微偏上，与 SVG 中的文本位置相似
            
            # 绘制书本主体（白色矩形，代表书本）
            draw.rectangle(
                [book_x, book_y, book_x + book_width, book_y + book_height],
                fill='white',
                outline='white'
            )
            
            # 绘制书本的线条（代表书页，与 SVG 中的书本 emoji 类似）
            for i in range(3):
                line_y = book_y + book_height // 4 + i * (book_height // 4)
                draw.line(
                    [book_x + book_width // 4, line_y, book_x + 3 * book_width // 4, line_y],
                    fill='#6366f1',
                    width=max(1, width // 64)
                )
            
            # 保存 PNG 文件
            img.save(output_path, "PNG", optimize=True)
            print(f"[成功] 已生成: {filename} ({width}x{height})")
            
        except Exception as e:
            print(f"[错误] 生成 {filename} 失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    print("\n[完成] 所有 PWA 图标已成功生成！")
    print(f"文件位置: {public_dir}")


if __name__ == "__main__":
    generate_pwa_icons()

