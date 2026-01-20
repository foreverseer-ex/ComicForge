/**
 * 模型元数据详情 API
 * GET /api/model/[id] - 获取模型详情
 * PUT /api/model/[id] - 更新模型元数据
 * DELETE /api/model/[id] - 删除模型元数据
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const updateModelMetaSchema = z.object({
  filename: z.string().min(1).optional(),
  name: z.string().min(1).optional(),
  version: z.string().min(1).optional(),
  desc: z.string().optional().nullable(),
  baseModel: z.string().optional().nullable(),
  trainedWords: z.array(z.string()).optional().nullable(),
  url: z.string().url().optional().nullable(),
  webPageUrl: z.string().url().optional().nullable(),
  preference: z.string().optional().nullable(),
});

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const versionId = parseInt(params.id);
    if (isNaN(versionId)) {
      return createErrorResponse('Invalid model ID', 400);
    }

    const modelMeta = await prisma.modelMeta.findUnique({
      where: { versionId },
      include: {
        exampleJobs: {
          where: {
            status: 'completed',
          },
          include: {
            drawArgs: true,
          },
          orderBy: {
            createdAt: 'desc',
          },
        },
      },
    });

    if (!modelMeta) {
      return createErrorResponse('Model not found', 404);
    }

    // 解析 JSON 字段
    const result = {
      ...modelMeta,
      trainedWords: parseJsonOrNull<string[]>(modelMeta.trainedWords, []),
      exampleJobs: modelMeta.exampleJobs.map(job => ({
        ...job,
        results: parseJsonOrNull<string[]>(job.results, []),
        drawArgs: job.drawArgs ? {
          ...job.drawArgs,
          loras: parseJsonOrNull(job.drawArgs.loras),
        } : null,
      })),
    };

    return createSuccessResponse(result);
  } catch (error) {
    console.error('Get model error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const versionId = parseInt(params.id);
    if (isNaN(versionId)) {
      return createErrorResponse('Invalid model ID', 400);
    }

    const body = await request.json();
    const validated = updateModelMetaSchema.parse(body);

    const updateData: any = { ...validated };
    if (validated.trainedWords !== undefined) {
      updateData.trainedWords = validated.trainedWords ? stringifyJson(validated.trainedWords) : null;
    }

    const modelMeta = await prisma.modelMeta.update({
      where: { versionId },
      data: updateData,
    });

    // 返回时解析 trainedWords
    const result = {
      ...modelMeta,
      trainedWords: parseJsonOrNull<string[]>(modelMeta.trainedWords, []),
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Model not found', 404);
    }
    console.error('Update model error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const versionId = parseInt(params.id);
    if (isNaN(versionId)) {
      return createErrorResponse('Invalid model ID', 400);
    }

    await prisma.modelMeta.delete({
      where: { versionId },
    });

    return createSuccessResponse({ message: 'Model deleted successfully' });
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to delete not found')) {
      return createErrorResponse('Model not found', 404);
    }
    console.error('Delete model error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
