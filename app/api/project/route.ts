/**
 * 项目管理 API
 * GET /api/project - 获取所有项目
 * POST /api/project - 创建项目
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const createProjectSchema = z.object({
  title: z.string().min(1),
  novelPath: z.string().optional(),
  projectPath: z.string().min(1),
});

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const projects = await prisma.project.findMany({
      where: {
        deletedAt: null,
      },
      orderBy: {
        updatedAt: 'desc',
      },
    });

    return createSuccessResponse(projects);
  } catch (error) {
    console.error('Get projects error:', error);
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
    const validated = createProjectSchema.parse(body);

    const project = await prisma.project.create({
      data: {
        title: validated.title,
        novelPath: validated.novelPath,
        projectPath: validated.projectPath,
      },
    });

    return createSuccessResponse(project);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create project error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
