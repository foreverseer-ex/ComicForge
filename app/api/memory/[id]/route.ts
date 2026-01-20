/**
 * 记忆详情 API
 * PUT /api/memory/[id] - 更新记忆
 * DELETE /api/memory/[id] - 删除记忆（软删除）
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const updateMemorySchema = z.object({
  key: z.string().min(1).optional(),
  value: z.string().optional(),
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
    const validated = updateMemorySchema.parse(body);

    const memory = await prisma.memory.update({
      where: { id: params.id },
      data: validated,
    });

    return createSuccessResponse(memory);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Memory not found', 404);
    }
    console.error('Update memory error:', error);
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
    const memory = await prisma.memory.update({
      where: { id: params.id },
      data: {
        deletedAt: new Date(),
      },
    });

    return createSuccessResponse(memory);
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Memory not found', 404);
    }
    console.error('Delete memory error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
