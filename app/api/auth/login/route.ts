/**
 * 用户登录 API
 * POST /api/auth/login
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { verifyPassword } from '@/lib/auth/password';
import { generateToken } from '@/lib/auth/jwt';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { z } from 'zod';

const loginSchema = z.object({
  username: z.string(),
  password: z.string(),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validated = loginSchema.parse(body);

    // 查找用户
    const user = await prisma.user.findUnique({
      where: { username: validated.username },
    });

    if (!user) {
      return createErrorResponse('Invalid username or password', 401);
    }

    // 验证密码
    const isValid = await verifyPassword(validated.password, user.password);
    if (!isValid) {
      return createErrorResponse('Invalid username or password', 401);
    }

    // 生成 Token
    const token = await generateToken({
      userId: user.id,
      username: user.username,
      isAdmin: user.isAdmin,
    });

    return createSuccessResponse({
      token,
      user: {
        id: user.id,
        username: user.username,
        isAdmin: user.isAdmin,
      },
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Login error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
