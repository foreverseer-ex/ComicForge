/**
 * 图片访问 API
 * 
 * GET /api/file/image/[hash]
 * 
 * 根据 MD5 哈希值返回图片文件
 */

import { getImage } from '@/lib/utils/image';
import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: { hash: string } }
) {
  try {
    const { hash } = params;
    const mimeType = request.nextUrl.searchParams.get('mimeType') || undefined;
    
    // 验证哈希格式（MD5 应该是 32 个十六进制字符）
    if (!/^[a-f0-9]{32}$/i.test(hash)) {
      return new NextResponse('Invalid hash format', { status: 400 });
    }
    
    const imageBuffer = await getImage(hash, mimeType);
    
    if (!imageBuffer) {
      return new NextResponse('Image not found', { status: 404 });
    }
    
    // 返回图片，设置缓存头
    return new NextResponse(imageBuffer, {
      headers: {
        'Content-Type': mimeType || 'image/png',
        'Cache-Control': 'public, max-age=31536000, immutable', // 缓存 1 年
      },
    });
  } catch (error) {
    console.error('Error serving image:', error);
    return new NextResponse('Internal server error', { status: 500 });
  }
}
