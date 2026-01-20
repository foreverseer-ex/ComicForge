/**
 * 任务详情 API
 * GET /api/job/[id] - 获取任务详情
 * PUT /api/job/[id] - 更新任务（主要用于更新状态和结果）
 * DELETE /api/job/[id] - 删除任务
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const updateJobSchema = z.object({
  name: z.string().optional().nullable(),
  desc: z.string().optional().nullable(),
  status: z.enum(['pending', 'completed', 'failed']).optional(),
  results: z.array(z.string()).optional(), // 图片哈希值列表
  completedAt: z.string().datetime().optional().nullable(),
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

    const job = await prisma.job.findUnique({
      where: { id: params.id },
      include: {
        drawArgs: true,
        actor: true,
        modelMeta: true,
      },
    });

    if (!job) {
      return createErrorResponse('Job not found', 404);
    }

    // 解析 JSON 字段
    const result = {
      ...job,
      results: parseJsonOrNull<string[]>(job.results, []),
      drawArgs: job.drawArgs ? {
        ...job.drawArgs,
        loras: parseJsonOrNull(job.drawArgs.loras),
      } : null,
    };

    return createSuccessResponse(result);
  } catch (error) {
    console.error('Get job error:', error);
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
    const validated = updateJobSchema.parse(body);

    const updateData: any = {};

    if (validated.name !== undefined) {
      updateData.name = validated.name;
    }

    if (validated.desc !== undefined) {
      updateData.desc = validated.desc;
    }

    if (validated.status !== undefined) {
      updateData.status = validated.status;
    }

    if (validated.results !== undefined) {
      updateData.results = stringifyJson(validated.results);
    }

    if (validated.completedAt !== undefined) {
      updateData.completedAt = validated.completedAt ? new Date(validated.completedAt) : null;
    } else if (validated.status === 'completed' && !validated.completedAt) {
      // 如果状态变为 completed 且没有指定 completedAt，自动设置
      updateData.completedAt = new Date();
    }

    const job = await prisma.job.update({
      where: { id: params.id },
      data: updateData,
      include: {
        drawArgs: true,
        actor: true,
        modelMeta: true,
      },
    });

    // 返回时解析 JSON 字段
    const result = {
      ...job,
      results: parseJsonOrNull<string[]>(job.results, []),
      drawArgs: job.drawArgs ? {
        ...job.drawArgs,
        loras: parseJsonOrNull(job.drawArgs.loras),
      } : null,
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Job not found', 404);
    }
    console.error('Update job error:', error);
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

    await prisma.job.delete({
      where: { id: params.id },
    });

    return createSuccessResponse({ message: 'Job deleted successfully' });
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to delete not found')) {
      return createErrorResponse('Job not found', 404);
    }
    console.error('Delete job error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
