/**
 * 获取当前用户信息
 * GET /api/auth/me
 */

import { NextRequest } from 'next/server';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { prisma } from '@/lib/db/prisma';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const userData = await prisma.user.findUnique({
      where: { id: user.userId },
      select: {
        id: true,
        username: true,
        isAdmin: true,
        createdAt: true,
      },
    });

    if (!userData) {
      return createErrorResponse('User not found', 404);
    }

    return createSuccessResponse(userData);
  } catch (error) {
    console.error('Get user error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
