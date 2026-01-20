/**
 * 绘图任务管理 API
 * GET /api/job - 获取任务列表
 * POST /api/job - 创建任务
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const createJobSchema = z.object({
  name: z.string().optional().nullable(),
  desc: z.string().optional().nullable(),
  status: z.enum(['pending', 'completed', 'failed']).default('pending'),
  source: z.enum(['batch', 'single', 'actor_portrait', 'actor_example', 'model_example']),
  drawArgsId: z.string(),
  expectedCount: z.number().int().min(1).optional().nullable(),
  actorId: z.string().optional().nullable(),
  modelMetaId: z.number().int().optional().nullable(),
});

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const { searchParams } = new URL(request.url);
    const status = searchParams.get('status');
    const source = searchParams.get('source');
    const actorId = searchParams.get('actorId');
    const modelMetaId = searchParams.get('modelMetaId');
    const limit = parseInt(searchParams.get('limit') || '50');
    const offset = parseInt(searchParams.get('offset') || '0');

    const where: any = {};

    if (status) {
      where.status = status;
    }

    if (source) {
      where.source = source;
    }

    if (actorId) {
      where.actorId = actorId;
    }

    if (modelMetaId) {
      where.modelMetaId = parseInt(modelMetaId);
    }

    const [jobs, total] = await Promise.all([
      prisma.job.findMany({
        where,
        include: {
          drawArgs: true,
          actor: true,
          modelMeta: true,
        },
        orderBy: {
          createdAt: 'desc',
        },
        take: limit,
        skip: offset,
      }),
      prisma.job.count({ where }),
    ]);

    // 解析 JSON 字段
    const results = jobs.map(job => ({
      ...job,
      results: parseJsonOrNull<string[]>(job.results, []),
      drawArgs: job.drawArgs ? {
        ...job.drawArgs,
        loras: parseJsonOrNull(job.drawArgs.loras),
      } : null,
    }));

    return createSuccessResponse({
      jobs: results,
      total,
      limit,
      offset,
    });
  } catch (error) {
    console.error('Get jobs error:', error);
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
    const validated = createJobSchema.parse(body);

    // 验证 drawArgs 存在
    const drawArgs = await prisma.drawArgs.findUnique({
      where: { id: validated.drawArgsId },
    });

    if (!drawArgs) {
      return createErrorResponse('Draw args not found', 404);
    }

    // 如果指定了 actorId，验证 actor 存在
    if (validated.actorId) {
      const actor = await prisma.actor.findUnique({
        where: { id: validated.actorId },
      });

      if (!actor) {
        return createErrorResponse('Actor not found', 404);
      }
    }

    // 如果指定了 modelMetaId，验证 modelMeta 存在
    if (validated.modelMetaId) {
      const modelMeta = await prisma.modelMeta.findUnique({
        where: { versionId: validated.modelMetaId },
      });

      if (!modelMeta) {
        return createErrorResponse('Model meta not found', 404);
      }
    }

    const job = await prisma.job.create({
      data: {
        name: validated.name,
        desc: validated.desc,
        status: validated.status,
        source: validated.source,
        drawArgsId: validated.drawArgsId,
        results: stringifyJson([]), // 初始化为空列表
        expectedCount: validated.expectedCount,
        actorId: validated.actorId,
        modelMetaId: validated.modelMetaId,
      },
      include: {
        drawArgs: true,
        actor: true,
        modelMeta: true,
      },
    });

    // 返回时解析 JSON 字段
    const result = {
      ...job,
      results: parseJsonOrNull<string[]>(job.results, []),
      drawArgs: job.drawArgs ? {
        ...job.drawArgs,
        loras: parseJsonOrNull(job.drawArgs.loras),
      } : null,
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create job error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
