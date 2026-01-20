/**
 * 认证中间件
 */

import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from './jwt';

export interface AuthRequest extends NextRequest {
  user?: {
    userId: string;
    username: string;
    isAdmin: boolean;
  };
}

/**
 * 从请求中提取并验证 JWT Token
 */
export async function getAuthUser(
  request: NextRequest
): Promise<{ userId: string; username: string; isAdmin: boolean } | null> {
  const authHeader = request.headers.get('authorization');
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null;
  }

  const token = authHeader.substring(7);
  const payload = await verifyToken(token);

  if (!payload) {
    return null;
  }

  return {
    userId: payload.userId,
    username: payload.username,
    isAdmin: payload.isAdmin,
  };
}

/**
 * 创建认证错误响应
 */
export function createAuthErrorResponse(message: string = 'Unauthorized') {
  return NextResponse.json(
    { error: message },
    { status: 401 }
  );
}
