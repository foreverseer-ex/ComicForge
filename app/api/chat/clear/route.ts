/**
 * 清空聊天记录 API
 * POST /api/chat/clear
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const clearChatSchema = z.object({
  projectId: z.string().optional().nullable(),
});

export async function POST(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const body = await request.json();
    const validated = clearChatSchema.parse(body);

    const where: any = {};

    if (validated.projectId) {
      where.projectId = validated.projectId;
    }

    const result = await prisma.chatMessage.deleteMany({
      where,
    });

    return createSuccessResponse({ deletedCount: result.count });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Clear chat messages error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
