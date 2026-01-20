/**
 * 批量查询 API
 * GET /api/content/lines?projectId=xxx&chapter=1&startLine=1&endLine=100
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
    const chapter = searchParams.get('chapter');
    const startLine = searchParams.get('startLine');
    const endLine = searchParams.get('endLine');

    if (!projectId || !chapter || !startLine || !endLine) {
      return createErrorResponse('Missing required parameters', 400);
    }

    const contents = await prisma.content.findMany({
      where: {
        projectId,
        chapter: parseInt(chapter),
        line: {
          gte: parseInt(startLine),
          lte: parseInt(endLine),
        },
      },
      orderBy: {
        line: 'asc',
      },
    });

    return createSuccessResponse(contents);
  } catch (error) {
    console.error('Get lines error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
