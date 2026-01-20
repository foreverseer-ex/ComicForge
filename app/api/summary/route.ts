/**
 * 摘要管理 API
 * GET /api/summary/all - 获取所有摘要
 * POST /api/summary/create - 创建摘要
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const createSummarySchema = z.object({
  projectId: z.string(),
  content: z.string().min(1),
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

    const summaries = await prisma.summary.findMany({
      where,
      orderBy: {
        createdAt: 'desc',
      },
    });

    return createSuccessResponse(summaries);
  } catch (error) {
    console.error('Get summaries error:', error);
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
    const validated = createSummarySchema.parse(body);

    const summary = await prisma.summary.create({
      data: {
        projectId: validated.projectId,
        content: validated.content,
      },
    });

    return createSuccessResponse(summary);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create summary error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
