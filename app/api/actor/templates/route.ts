/**
 * 获取所有模板 API
 * GET /api/actor/templates
 * 
 * 用于 LLM 参考绘图参数
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { parseJsonOrNull } from '@/lib/utils/json';

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const templates = await prisma.actor.findMany({
      where: {
        isTemplate: true,
        deletedAt: null,
      },
      include: {
        exampleJobs: {
          where: {
            status: 'completed',
          },
          include: {
            drawArgs: true,
          },
          orderBy: {
            createdAt: 'desc',
          },
        },
      },
      orderBy: {
        name: 'asc',
      },
    });

    // 解析 JSON 字段
    const results = templates.map(template => ({
      ...template,
      tags: parseJsonOrNull(template.tags),
      exampleJobs: template.exampleJobs.map(job => ({
        ...job,
        results: parseJsonOrNull<string[]>(job.results, []),
        drawArgs: job.drawArgs ? {
          ...job.drawArgs,
          loras: parseJsonOrNull(job.drawArgs.loras),
        } : null,
      })),
    }));

    return createSuccessResponse(results);
  } catch (error) {
    console.error('Get templates error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
