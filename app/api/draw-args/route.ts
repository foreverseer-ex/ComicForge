/**
 * 绘图参数管理 API
 * GET /api/draw-args - 获取绘图参数列表
 * POST /api/draw-args - 创建绘图参数
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const createDrawArgsSchema = z.object({
  model: z.string().min(1),
  prompt: z.string().min(1),
  negativePrompt: z.string().optional().nullable(),
  steps: z.number().int().min(1).max(150).optional().default(30),
  cfgScale: z.number().min(0).max(20).optional().default(7.0),
  sampler: z.string().optional().nullable(),
  seed: z.number().int().optional().nullable(),
  width: z.number().int().min(64).max(4096).optional().default(1024),
  height: z.number().int().min(64).max(4096).optional().default(1024),
  clipSkip: z.number().int().min(0).max(12).optional().nullable(),
  vae: z.string().optional().nullable(),
  loras: z.record(z.any()).optional().nullable(),
});

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const { searchParams } = new URL(request.url);
    const model = searchParams.get('model');
    const sampler = searchParams.get('sampler');

    const where: any = {};

    if (model) {
      where.model = model;
    }

    if (sampler) {
      where.sampler = sampler;
    }

    const drawArgs = await prisma.drawArgs.findMany({
      where,
      orderBy: {
        createdAt: 'desc',
      },
      take: 100, // 限制返回数量
    });

    // 解析 JSON 字段
    const results = drawArgs.map(args => ({
      ...args,
      loras: parseJsonOrNull(args.loras),
    }));

    return createSuccessResponse(results);
  } catch (error) {
    console.error('Get draw args error:', error);
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
    const validated = createDrawArgsSchema.parse(body);

    const drawArgs = await prisma.drawArgs.create({
      data: {
        model: validated.model,
        prompt: validated.prompt,
        negativePrompt: validated.negativePrompt,
        steps: validated.steps,
        cfgScale: validated.cfgScale,
        sampler: validated.sampler,
        seed: validated.seed,
        width: validated.width,
        height: validated.height,
        clipSkip: validated.clipSkip,
        vae: validated.vae,
        loras: validated.loras ? stringifyJson(validated.loras) : null,
      },
    });

    // 返回时解析 loras
    const result = {
      ...drawArgs,
      loras: parseJsonOrNull(drawArgs.loras),
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create draw args error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
