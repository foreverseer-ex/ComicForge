/**
 * 更新任务状态 API（便捷接口）
 * PUT /api/job/[id]/update-status
 * 
 * 用于快速更新任务状态，常用于任务完成或失败时
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const updateStatusSchema = z.object({
  status: z.enum(['pending', 'completed', 'failed']),
  results: z.array(z.string()).optional(), // 图片哈希值列表（完成时提供）
});

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
    const validated = updateStatusSchema.parse(body);

    const updateData: any = {
      status: validated.status,
    };

    if (validated.results !== undefined) {
      updateData.results = stringifyJson(validated.results);
    }

    if (validated.status === 'completed') {
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
    console.error('Update job status error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
