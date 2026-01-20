/**
 * 聊天消息详情 API
 * GET /api/chat/[id] - 获取消息详情
 * PUT /api/chat/[id] - 更新消息
 * DELETE /api/chat/[id] - 删除消息
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const updateChatMessageSchema = z.object({
  status: z.enum(['pending', 'ready', 'error']).optional(),
  messageType: z.enum(['normal', 'thinking', 'tool']).optional(),
  context: z.string().optional(),
  tools: z.any().optional(),
  suggests: z.any().optional(),
  data: z.any().optional(),
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

    const message = await prisma.chatMessage.findUnique({
      where: { id: params.id },
    });

    if (!message) {
      return createErrorResponse('Message not found', 404);
    }

    // 解析 JSON 字段
    const result = {
      ...message,
      tools: parseJsonOrNull(message.tools, {}),
      suggests: parseJsonOrNull(message.suggests, []),
      data: parseJsonOrNull(message.data, {}),
    };

    return createSuccessResponse(result);
  } catch (error) {
    console.error('Get chat message error:', error);
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
    const validated = updateChatMessageSchema.parse(body);

    const updateData: any = {};

    if (validated.status !== undefined) {
      updateData.status = validated.status;
    }

    if (validated.messageType !== undefined) {
      updateData.messageType = validated.messageType;
    }

    if (validated.context !== undefined) {
      updateData.context = validated.context;
    }

    if (validated.tools !== undefined) {
      updateData.tools = stringifyJson(validated.tools);
    }

    if (validated.suggests !== undefined) {
      updateData.suggests = stringifyJson(validated.suggests);
    }

    if (validated.data !== undefined) {
      updateData.data = stringifyJson(validated.data);
    }

    const message = await prisma.chatMessage.update({
      where: { id: params.id },
      data: updateData,
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
    if (error instanceof Error && error.message.includes('Record to update not found')) {
      return createErrorResponse('Message not found', 404);
    }
    console.error('Update chat message error:', error);
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

    await prisma.chatMessage.delete({
      where: { id: params.id },
    });

    return createSuccessResponse({ message: 'Message deleted successfully' });
  } catch (error) {
    if (error instanceof Error && error.message.includes('Record to delete not found')) {
      return createErrorResponse('Message not found', 404);
    }
    console.error('Delete chat message error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
