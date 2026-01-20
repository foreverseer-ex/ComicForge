/**
 * 章节详情 API
 * GET /api/content/chapter/[id]?projectId=xxx
 * PUT /api/content/chapter/[id] - 更新章节（批量更新该章节的所有行）
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const updateChapterSchema = z.object({
  projectId: z.string(),
  chapter: z.number().int(),
  contents: z.array(z.object({
    line: z.number().int(),
    content: z.string(),
    imageHash: z.string().optional().nullable(),
  })),
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

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('projectId');
    const chapter = parseInt(params.id);

    if (!projectId) {
      return createErrorResponse('Missing projectId', 400);
    }

    const contents = await prisma.content.findMany({
      where: {
        projectId,
        chapter,
      },
      orderBy: {
        line: 'asc',
      },
    });

    return createSuccessResponse(contents);
  } catch (error) {
    console.error('Get chapter error:', error);
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
    const validated = updateChapterSchema.parse(body);
    const chapter = parseInt(params.id);

    // 批量更新或创建（使用事务）
    const results = await Promise.all(
      validated.contents.map(async (content) => {
        const existing = await prisma.content.findFirst({
          where: {
            projectId: validated.projectId,
            chapter,
            line: content.line,
          },
        });

        if (existing) {
          return prisma.content.update({
            where: { id: existing.id },
            data: {
              content: content.content,
              imageHash: content.imageHash,
            },
          });
        } else {
          return prisma.content.create({
            data: {
              projectId: validated.projectId,
              chapter,
              line: content.line,
              content: content.content,
              imageHash: content.imageHash,
            },
          });
        }
      })
    );

    return createSuccessResponse(results);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Update chapter error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
