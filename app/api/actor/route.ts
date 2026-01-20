/**
 * 角色/模板管理 API
 * GET /api/actor/all - 获取所有角色/模板
 * POST /api/actor/create - 创建角色/模板
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const createActorSchema = z.object({
  projectId: z.string().nullable().optional(),
  name: z.string().min(1),
  desc: z.string(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/),
  tags: z.record(z.any()).optional().nullable(),
  isTemplate: z.boolean().optional().default(false),
});

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('projectId');
    const isTemplate = searchParams.get('isTemplate');

    const where: any = {
      deletedAt: null,
    };

    if (projectId !== null && projectId !== '') {
      where.projectId = projectId;
    }

    if (isTemplate !== null) {
      where.isTemplate = isTemplate === 'true';
    }

    const actors = await prisma.actor.findMany({
      where,
      orderBy: {
        createdAt: 'desc',
      },
    });

    // 解析 tags
    const results = actors.map(actor => ({
      ...actor,
      tags: parseJsonOrNull(actor.tags),
    }));

    return createSuccessResponse(results);
  } catch (error) {
    console.error('Get actors error:', error);
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
    const validated = createActorSchema.parse(body);

    // 验证：模板必须 projectId 为 null
    if (validated.isTemplate && validated.projectId !== null) {
      return createErrorResponse('Template must not have projectId', 400);
    }

    // 验证：角色必须 projectId 不为 null
    if (!validated.isTemplate && !validated.projectId) {
      return createErrorResponse('Actor must have projectId', 400);
    }

    const actor = await prisma.actor.create({
      data: {
        projectId: validated.isTemplate ? null : validated.projectId!,
        name: validated.name,
        desc: validated.desc,
        color: validated.color,
        tags: validated.tags ? stringifyJson(validated.tags) : null,
        isTemplate: validated.isTemplate,
      },
    });

    // 返回时解析 tags
    const result = {
      ...actor,
      tags: parseJsonOrNull(actor.tags),
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create actor error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
