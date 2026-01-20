/**
 * 章节列表 API
 * GET /api/content/chapters?projectId=xxx
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('projectId');

    if (!projectId) {
      return createErrorResponse('Missing projectId', 400);
    }

    // 获取所有章节号
    const chapters = await prisma.content.findMany({
      where: {
        projectId,
      },
      select: {
        chapter: true,
      },
      distinct: ['chapter'],
      orderBy: {
        chapter: 'asc',
      },
    });

    return createSuccessResponse(chapters.map(c => c.chapter));
  } catch (error) {
    console.error('Get chapters error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
