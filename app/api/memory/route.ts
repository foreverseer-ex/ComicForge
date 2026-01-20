/**
 * 记忆管理 API
 * GET /api/memory/all - 获取所有记忆
 * POST /api/memory/create - 创建记忆
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const createMemorySchema = z.object({
  projectId: z.string(),
  key: z.string().min(1),
  value: z.string(),
});

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('projectId');

    const where: any = {
      deletedAt: null,
    };

    if (projectId) {
      where.projectId = projectId;
    }

    const memories = await prisma.memory.findMany({
      where,
      orderBy: {
        createdAt: 'desc',
      },
    });

    return createSuccessResponse(memories);
  } catch (error) {
    console.error('Get memories error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const body = await request.json();
    const validated = createMemorySchema.parse(body);

    const memory = await prisma.memory.create({
      data: {
        projectId: validated.projectId,
        key: validated.key,
        value: validated.value,
      },
    });

    return createSuccessResponse(memory);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create memory error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
