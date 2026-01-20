/**
 * 单行查询 API
 * GET /api/content/line?projectId=xxx&chapter=1&line=1
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
    const line = searchParams.get('line');

    if (!projectId || !chapter || !line) {
      return createErrorResponse('Missing required parameters', 400);
    }

    const content = await prisma.content.findFirst({
      where: {
        projectId,
        chapter: parseInt(chapter),
        line: parseInt(line),
      },
    });

    if (!content) {
      return createErrorResponse('Content not found', 404);
    }

    return createSuccessResponse(content);
  } catch (error) {
    console.error('Get line error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
