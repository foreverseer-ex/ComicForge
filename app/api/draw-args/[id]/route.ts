/**
 * 绘图参数详情 API
 * GET /api/draw-args/[id] - 获取绘图参数详情
 * PUT /api/draw-args/[id] - 更新绘图参数
 * DELETE /api/draw-args/[id] - 删除绘图参数
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const updateDrawArgsSchema = z.object({
  model: z.string().min(1).optional(),
  prompt: z.string().min(1).optional(),
  negativePrompt: z.string().optional().nullable(),
  steps: z.number().int().min(1).max(150).optional(),
  cfgScale: z.number().min(0).max(20).optional(),
  sampler: z.string().optional().nullable(),
  seed: z.number().int().optional().nullable(),
  width: z.number().int().min(64).max(4096).optional(),
  height: z.number().int().min(64).max(4096).optional(),
  clipSkip: z.number().int().min(0).max(12).optional().nullable(),
  vae: z.string().optional().nullable(),
  loras: z.record(z.any()).optional().nullable(),
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

    const drawArgs = await prisma.drawArgs.findUnique({
      where: { id: params.id },
      include: {
        jobs: {
          orderBy: {
            createdAt: 'desc',
          },
          take: 10, // 只返回最近的 10 个任务
        },
      },
    });

    if (!drawArgs) {
      return createErrorResponse('Draw args not found', 404);
    }

    // 解析 JSON 字段
    const result = {
      ...drawArgs,
      loras: parseJsonOrNull(drawArgs.loras),
      jobs: drawArgs.jobs.map(job => ({
        ...job,
        results: parseJsonOrNull<string[]>(job.results, []),
      })),
    };

    return createSuccessResponse(result);
  } catch (error) {
    console.error('Get draw args error:', error);
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

    const body = await request.json();
    const validated = updateDrawArgsSchema.parse(body);

    const updateData: any = { ...validated };
    if (validated.loras !== undefined) {
      updateData.loras = validated.loras ? stringifyJson(validated.loras) : null;
    }

    const drawArgs = await prisma.drawArgs.update({
      where: { id: params.id },
      data: updateData,
    });

    // 返回时解析 loras
    const result = {
      ...drawArgs,
      loras: parseJsonOrNull(drawArgs.loras),
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Draw args not found', 404);
    }
    console.error('Update draw args error:', error);
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

    // 检查是否有关联的任务
    const jobCount = await prisma.job.count({
      where: { drawArgsId: params.id },
    });

    if (jobCount > 0) {
      return createErrorResponse(
        `Cannot delete draw args: ${jobCount} job(s) are using it`,
        400
      );
    }

    await prisma.drawArgs.delete({
      where: { id: params.id },
    });

    return createSuccessResponse({ message: 'Draw args deleted successfully' });
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to delete not found')) {
      return createErrorResponse('Draw args not found', 404);
    }
    console.error('Delete draw args error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
