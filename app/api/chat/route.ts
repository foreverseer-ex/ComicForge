/**
 * 聊天消息管理 API
 * GET /api/chat - 获取聊天消息列表
 * POST /api/chat - 创建聊天消息
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const createChatMessageSchema = z.object({
  projectId: z.string().optional().nullable(),
  index: z.number().int(),
  status: z.enum(['pending', 'ready', 'error']),
  messageType: z.enum(['normal', 'thinking', 'tool']),
  role: z.enum(['user', 'assistant', 'system']),
  context: z.string(),
  tools: z.any().optional().default({}),
  suggests: z.any().optional().default([]),
  data: z.any().optional().default({}),
});

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const { searchParams } = new URL(request.url);
    const projectId = searchParams.get('projectId');
    const status = searchParams.get('status');
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');

    const where: any = {};

    if (projectId) {
      where.projectId = projectId;
    }

    if (status) {
      where.status = status;
    }

    const [messages, total] = await Promise.all([
      prisma.chatMessage.findMany({
        where,
        orderBy: {
          index: 'asc',
        },
        take: limit,
        skip: offset,
      }),
      prisma.chatMessage.count({ where }),
    ]);

    // 解析 JSON 字段
    const results = messages.map(msg => ({
      ...msg,
      tools: parseJsonOrNull(msg.tools, {}),
      suggests: parseJsonOrNull(msg.suggests, []),
      data: parseJsonOrNull(msg.data, {}),
    }));

    return createSuccessResponse({
      messages: results,
      total,
      limit,
      offset,
    });
  } catch (error) {
    console.error('Get chat messages error:', error);
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
    const validated = createChatMessageSchema.parse(body);

    const message = await prisma.chatMessage.create({
      data: {
        projectId: validated.projectId,
        index: validated.index,
        status: validated.status,
        messageType: validated.messageType,
        role: validated.role,
        context: validated.context,
        tools: stringifyJson(validated.tools),
        suggests: stringifyJson(validated.suggests),
        data: stringifyJson(validated.data),
      },
    });

    // 返回时解析 JSON 字段
    const result = {
      ...message,
      tools: parseJsonOrNull(message.tools, {}),
      suggests: parseJsonOrNull(message.suggests, []),
      data: parseJsonOrNull(message.data, {}),
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create chat message error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
