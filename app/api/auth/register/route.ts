/**
 * 用户注册 API
 * POST /api/auth/register
 * 
 * 仅管理员可以注册新用户
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { hashPassword } from '@/lib/auth/password';
import { generateToken } from '@/lib/auth/jwt';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { z } from 'zod';

const registerSchema = z.object({
  username: z.string().min(3).max(50),
  password: z.string().min(6),
  isAdmin: z.boolean().optional().default(false),
});

export async function POST(request: NextRequest) {
  try {
    // 检查当前用户是否为管理员
    const currentUser = await getAuthUser(request);
    if (!currentUser || !currentUser.isAdmin) {
      return createAuthErrorResponse('Only admin can register new users');
    }

    const body = await request.json();
    const validated = registerSchema.parse(body);

    // 检查用户名是否已存在
    const existingUser = await prisma.user.findUnique({
      where: { username: validated.username },
    });

    if (existingUser) {
      return createErrorResponse('Username already exists', 409);
    }

    // 创建用户
    const hashedPassword = await hashPassword(validated.password);
    const user = await prisma.user.create({
      data: {
        username: validated.username,
        password: hashedPassword,
        isAdmin: validated.isAdmin,
      },
      select: {
        id: true,
        username: true,
        isAdmin: true,
        createdAt: true,
      },
    });

    return createSuccessResponse(user);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Register error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
