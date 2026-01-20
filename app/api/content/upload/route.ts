/**
 * 内容上传 API
 * POST /api/content/upload
 * 
 * 支持上传 TXT 文件并解析为章节内容
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { parseTxtBuffer } from '@/lib/utils/novel-parser';

export async function POST(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const formData = await request.formData();
    const file = formData.get('file') as File;
    const projectId = formData.get('projectId') as string;

    if (!file) {
      return createErrorResponse('No file provided', 400);
    }

    if (!projectId) {
      return createErrorResponse('Project ID is required', 400);
    }

    // 验证项目存在
    const project = await prisma.project.findUnique({
      where: { id: projectId },
    });

    if (!project) {
      return createErrorResponse('Project not found', 404);
    }

    // 验证文件类型
    const fileType = file.type;
    const fileName = file.name.toLowerCase();

    if (!fileName.endsWith('.txt') && fileType !== 'text/plain') {
      return createErrorResponse('Only TXT files are supported', 400);
    }

    // 验证文件大小（限制 50MB）
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      return createErrorResponse('File size exceeds 50MB limit', 400);
    }

    // 读取文件内容
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    // 解析 TXT 文件
    const parsed = await parseTxtBuffer(buffer);

    // 使用事务批量写入数据库
    await prisma.$transaction(async (tx) => {
      // 删除项目现有的内容（可选：或者保留旧内容）
      // await tx.content.deleteMany({
      //   where: { projectId },
      // });

      // 批量创建内容记录
      // 由于 SQLite 不支持复合唯一键的 upsert，使用 findFirst + create/update
      // 为了性能，分批处理
      const batchSize = 100;
      for (let i = 0; i < parsed.lines.length; i += batchSize) {
        const batch = parsed.lines.slice(i, i + batchSize);
        await Promise.all(
          batch.map(async (line) => {
            // 查找是否已存在
            const existing = await tx.content.findFirst({
              where: {
                projectId,
                chapter: line.chapter,
                line: line.line,
              },
            });

            if (existing) {
              return tx.content.update({
                where: { id: existing.id },
                data: { content: line.content },
              });
            } else {
              return tx.content.create({
                data: {
                  projectId,
                  chapter: line.chapter,
                  line: line.line,
                  content: line.content,
                },
              });
            }
          })
        );
      }

      // 更新项目统计信息
      await tx.project.update({
        where: { id: projectId },
        data: {
          totalLines: parsed.totalLines,
          totalChapters: parsed.totalChapters,
          currentLine: 0,
          currentChapter: 1,
        },
      });
    });

    return createSuccessResponse({
      message: 'Upload and parse successful',
      totalLines: parsed.totalLines,
      totalChapters: parsed.totalChapters,
      chapters: parsed.chapters.map((ch) => ({
        chapter: ch.chapter,
        title: ch.title,
        lines: ch.endLine - ch.startLine + 1,
      })),
    });
  } catch (error) {
    console.error('Upload content error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
