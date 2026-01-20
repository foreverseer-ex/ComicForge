/**
 * 批量删除记忆 API
 * POST /api/memory/clear
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const clearMemorySchema = z.object({
  projectId: z.string(),
});

export async function POST(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const body = await request.json();
    const validated = clearMemorySchema.parse(body);

    // 批量软删除
    const result = await prisma.memory.updateMany({
      where: {
        projectId: validated.projectId,
        deletedAt: null,
      },
      data: {
        deletedAt: new Date(),
      },
    });

    return createSuccessResponse({ deletedCount: result.count });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Clear memories error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
