/**
 * 内容统计 API
 * GET /api/content/stats?projectId=xxx
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

    const [totalLines, totalChapters, chaptersWithImages] = await Promise.all([
      prisma.content.count({
        where: { projectId },
      }),
      prisma.content.findMany({
        where: { projectId },
        select: { chapter: true },
        distinct: ['chapter'],
      }).then(chapters => chapters.length),
      prisma.content.count({
        where: {
          projectId,
          imageHash: { not: null },
        },
      }),
    ]);

    return createSuccessResponse({
      totalLines,
      totalChapters,
      chaptersWithImages,
    });
  } catch (error) {
    console.error('Get stats error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
