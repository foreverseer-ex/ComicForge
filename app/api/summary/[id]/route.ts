/**
 * 摘要详情 API
 * PUT /api/summary/[id] - 更新摘要
 * DELETE /api/summary/[id] - 删除摘要（软删除）
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const updateSummarySchema = z.object({
  content: z.string().min(1).optional(),
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
    const validated = updateSummarySchema.parse(body);

    const summary = await prisma.summary.update({
      where: { id: params.id },
      data: validated,
    });

    return createSuccessResponse(summary);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Summary not found', 404);
    }
    console.error('Update summary error:', error);
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

    // 软删除
    const summary = await prisma.summary.update({
      where: { id: params.id },
      data: {
        deletedAt: new Date(),
      },
    });

    return createSuccessResponse(summary);
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Summary not found', 404);
    }
    console.error('Delete summary error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
