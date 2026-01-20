/**
 * 图片存储工具函数
 * 
 * 所有图片统一存储在 storage/data/images/ 目录下
 * 使用 MD5 哈希值作为文件名，格式：{hash}.{ext}
 * 在需要图片的地方直接存储哈希值字符串
 */

import crypto from 'crypto';
import fs from 'fs/promises';
import path from 'path';
import sharp from 'sharp';
import { existsSync } from 'fs';

const IMAGE_STORAGE_DIR = path.join(process.cwd(), 'storage', 'data', 'images');

/**
 * 计算图片的 MD5 哈希值
 */
export function calculateImageHash(buffer: Buffer): string {
  return crypto.createHash('md5').update(buffer).digest('hex');
}

/**
 * 检测图片 MIME 类型
 */
export async function detectMimeType(buffer: Buffer): Promise<string> {
  try {
    const metadata = await sharp(buffer).metadata();
    const format = metadata.format;
    
    const mimeMap: Record<string, string> = {
      'png': 'image/png',
      'jpeg': 'image/jpeg',
      'jpg': 'image/jpeg',
      'webp': 'image/webp',
      'gif': 'image/gif',
    };
    
    return mimeMap[format || 'png'] || 'image/png';
  } catch {
    // 如果 sharp 无法识别，默认返回 png
    return 'image/png';
  }
}

/**
 * MIME 类型转文件扩展名
 */
export function mimeTypeToExt(mimeType: string): string {
  const extMap: Record<string, string> = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/webp': 'webp',
    'image/gif': 'gif',
  };
  
  return extMap[mimeType] || 'png';
}

/**
 * 图片信息接口
 */
export interface ImageInfo {
  hash: string;
  mimeType: string;
  width: number;
  height: number;
  size: number;
}

/**
 * 保存图片到存储目录，返回哈希值和元数据
 * 
 * @param buffer 图片 Buffer
 * @param options 选项
 * @returns 图片信息（包含哈希值、MIME 类型、尺寸等）
 */
export async function saveImage(
  buffer: Buffer,
  options?: {
    originalFilename?: string;
    convertToFormat?: 'png' | 'jpeg' | 'webp';
  }
): Promise<ImageInfo> {
  // 如果需要转换格式
  let processedBuffer = buffer;
  if (options?.convertToFormat) {
    processedBuffer = await sharp(buffer)
      .toFormat(options.convertToFormat)
      .toBuffer();
  }
  
  // 计算 MD5 哈希
  const hash = calculateImageHash(processedBuffer);
  
  // 检测文件类型
  const mimeType = await detectMimeType(processedBuffer);
  const ext = mimeTypeToExt(mimeType);
  
  // 确保目录存在
  await fs.mkdir(IMAGE_STORAGE_DIR, { recursive: true });
  
  // 获取图片尺寸
  const metadata = await sharp(processedBuffer).metadata();
  const width = metadata.width || 0;
  const height = metadata.height || 0;
  
  // 保存文件（如果已存在则跳过，实现去重）
  const filePath = path.join(IMAGE_STORAGE_DIR, `${hash}.${ext}`);
  try {
    await fs.access(filePath);
    // 文件已存在，直接返回（去重机制）
  } catch {
    // 文件不存在，写入新文件
    await fs.writeFile(filePath, processedBuffer);
  }
  
  return {
    hash,
    mimeType,
    width,
    height,
    size: processedBuffer.length,
  };
}

/**
 * 根据哈希值获取图片文件路径
 * 
 * @param hash MD5 哈希值
 * @param mimeType 可选的 MIME 类型（用于确定扩展名）
 * @returns 文件路径
 */
export function getImagePath(hash: string, mimeType?: string): string {
  // 如果提供了 MIME 类型，使用对应的扩展名
  if (mimeType) {
    const ext = mimeTypeToExt(mimeType);
    return path.join(IMAGE_STORAGE_DIR, `${hash}.${ext}`);
  }
  
  // 否则返回默认路径（调用者需要尝试多个扩展名）
  return path.join(IMAGE_STORAGE_DIR, `${hash}.png`);
}

/**
 * 根据哈希值读取图片 Buffer
 * 
 * @param hash MD5 哈希值
 * @param mimeType 可选的 MIME 类型（用于确定扩展名）
 * @returns 图片 Buffer，如果不存在则返回 null
 */
export async function getImage(hash: string, mimeType?: string): Promise<Buffer | null> {
  // 如果提供了 MIME 类型，直接尝试
  if (mimeType) {
    const filePath = getImagePath(hash, mimeType);
    if (existsSync(filePath)) {
      return await fs.readFile(filePath);
    }
    return null;
  }
  
  // 否则尝试常见扩展名
  const commonExts = ['png', 'jpg', 'jpeg', 'webp', 'gif'];
  for (const ext of commonExts) {
    const filePath = path.join(IMAGE_STORAGE_DIR, `${hash}.${ext}`);
    if (existsSync(filePath)) {
      return await fs.readFile(filePath);
    }
  }
  
  return null;
}

/**
 * 检查图片是否存在
 * 
 * @param hash MD5 哈希值
 * @param mimeType 可选的 MIME 类型
 * @returns 是否存在
 */
export async function imageExists(hash: string, mimeType?: string): Promise<boolean> {
  if (mimeType) {
    const filePath = getImagePath(hash, mimeType);
    return existsSync(filePath);
  }
  
  // 尝试常见扩展名
  const commonExts = ['png', 'jpg', 'jpeg', 'webp', 'gif'];
  for (const ext of commonExts) {
    const filePath = path.join(IMAGE_STORAGE_DIR, `${hash}.${ext}`);
    if (existsSync(filePath)) {
      return true;
    }
  }
  
  return false;
}

/**
 * 删除图片文件
 * 
 * 注意：删除前需要检查是否还有其他引用，避免误删
 * 
 * @param hash MD5 哈希值
 * @param mimeType 可选的 MIME 类型
 * @returns 是否删除成功
 */
export async function deleteImage(hash: string, mimeType?: string): Promise<boolean> {
  if (mimeType) {
    const filePath = getImagePath(hash, mimeType);
    try {
      await fs.unlink(filePath);
      return true;
    } catch {
      return false;
    }
  }
  
  // 尝试常见扩展名
  const commonExts = ['png', 'jpg', 'jpeg', 'webp', 'gif'];
  for (const ext of commonExts) {
    const filePath = path.join(IMAGE_STORAGE_DIR, `${hash}.${ext}`);
    try {
      await fs.unlink(filePath);
      return true;
    } catch {
      // 继续尝试
    }
  }
  
  return false;
}

/**
 * 获取图片 URL（用于前端访问）
 * 
 * @param hash MD5 哈希值
 * @param mimeType 可选的 MIME 类型
 * @returns 图片 URL
 */
export function getImageUrl(hash: string, mimeType?: string): string {
  const params = new URLSearchParams();
  if (mimeType) {
    params.set('mimeType', mimeType);
  }
  const query = params.toString();
  return `/api/file/image/${hash}${query ? `?${query}` : ''}`;
}
