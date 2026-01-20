/**
 * 角色详情 API
 * GET /api/actor/[id] - 获取角色详情
 * PUT /api/actor/[id] - 更新角色
 * DELETE /api/actor/[id] - 删除角色（软删除）
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const updateActorSchema = z.object({
  name: z.string().min(1).optional(),
  desc: z.string().optional(),
  color: z.string().regex(/^#[0-9A-Fa-f]{6}$/).optional(),
  tags: z.record(z.any()).optional().nullable(),
});

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const actor = await prisma.actor.findFirst({
      where: {
        id: params.id,
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
    });

    if (!actor) {
      return createErrorResponse('Actor not found', 404);
    }

    // 解析 tags 和 exampleJobs 中的 JSON 字段
    const result = {
      ...actor,
      tags: parseJsonOrNull(actor.tags),
      exampleJobs: actor.exampleJobs.map(job => ({
        ...job,
        results: parseJsonOrNull<string[]>(job.results, []),
        drawArgs: job.drawArgs ? {
          ...job.drawArgs,
          loras: parseJsonOrNull(job.drawArgs.loras),
        } : null,
      })),
    };

    return createSuccessResponse(result);
  } catch (error) {
    console.error('Get actor error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const body = await request.json();
    const validated = updateActorSchema.parse(body);

    const updateData: any = { ...validated };
    if (validated.tags !== undefined) {
      updateData.tags = validated.tags ? stringifyJson(validated.tags) : null;
    }

    const actor = await prisma.actor.update({
      where: { id: params.id },
      data: updateData,
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
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Actor not found', 404);
    }
    console.error('Update actor error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    // 软删除
    const actor = await prisma.actor.update({
      where: { id: params.id },
      data: {
        deletedAt: new Date(),
      },
    });

    return createSuccessResponse(actor);
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Actor not found', 404);
    }
    console.error('Delete actor error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
