/**
 * 图片上传 API
 * POST /api/file/upload
 * 
 * 上传图片文件，返回图片哈希值和元信息
 */

import { NextRequest } from 'next/server';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { saveImage } from '@/lib/utils/image';

export async function POST(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return createErrorResponse('No file provided', 400);
    }

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      return createErrorResponse('File must be an image', 400);
    }

    // 读取文件内容
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // 保存图片
    const imageInfo = await saveImage(buffer, {
      originalFilename: file.name,
    });

    return createSuccessResponse({
      hash: imageInfo.hash,
      mimeType: imageInfo.mimeType,
      width: imageInfo.width,
      height: imageInfo.height,
      size: imageInfo.size,
      url: `/api/file/image/${imageInfo.hash}?mimeType=${encodeURIComponent(imageInfo.mimeType)}`,
    });
  } catch (error) {
    console.error('Upload image error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
