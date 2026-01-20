/**
 * 项目详情 API
 * GET /api/project/[id] - 获取项目详情
 * PUT /api/project/[id] - 更新项目
 * DELETE /api/project/[id] - 删除项目（软删除）
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const updateProjectSchema = z.object({
  title: z.string().min(1).optional(),
  novelPath: z.string().optional().nullable(),
  projectPath: z.string().min(1).optional(),
  totalLines: z.number().int().min(0).optional(),
  totalChapters: z.number().int().min(0).optional(),
  currentLine: z.number().int().min(0).optional(),
  currentChapter: z.number().int().min(0).optional(),
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

    const project = await prisma.project.findFirst({
      where: {
        id: params.id,
        deletedAt: null,
      },
    });

    if (!project) {
      return createErrorResponse('Project not found', 404);
    }

    return createSuccessResponse(project);
  } catch (error) {
    console.error('Get project error:', error);
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
    const validated = updateProjectSchema.parse(body);

    const project = await prisma.project.update({
      where: { id: params.id },
      data: validated,
    });

    return createSuccessResponse(project);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Project not found', 404);
    }
    console.error('Update project error:', error);
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
    const project = await prisma.project.update({
      where: { id: params.id },
      data: {
        deletedAt: new Date(),
      },
    });

    return createSuccessResponse(project);
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Project not found', 404);
    }
    console.error('Delete project error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
