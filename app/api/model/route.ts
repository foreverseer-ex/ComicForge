/**
 * 模型元数据管理 API
 * GET /api/model - 获取模型列表
 * POST /api/model - 创建模型元数据
 */

import { NextRequest } from 'next/server';
import { prisma } from '@/lib/db/prisma';
import { getAuthUser, createAuthErrorResponse } from '@/lib/auth/middleware';
import { createSuccessResponse, createErrorResponse } from '@/lib/utils/response';
import { stringifyJson, parseJsonOrNull } from '@/lib/utils/json';
import { z } from 'zod';

const createModelMetaSchema = z.object({
  filename: z.string().min(1),
  name: z.string().min(1),
  version: z.string().min(1),
  desc: z.string().optional().nullable(),
  modelId: z.number().int(),
  type: z.enum(['checkpoint', 'lora']),
  ecosystem: z.string().min(1),
  baseModel: z.string().optional().nullable(),
  sha256: z.string().length(64), // SHA-256 哈希值应该是 64 个字符
  trainedWords: z.array(z.string()).optional().nullable(),
  url: z.string().url().optional().nullable(),
  webPageUrl: z.string().url().optional().nullable(),
  preference: z.string().optional().nullable(),
});

export async function GET(request: NextRequest) {
  try {
    const user = await getAuthUser(request);
    if (!user) {
      return createAuthErrorResponse('Unauthorized');
    }

    const { searchParams } = new URL(request.url);
    const modelId = searchParams.get('modelId');
    const type = searchParams.get('type');
    const ecosystem = searchParams.get('ecosystem');
    const limit = parseInt(searchParams.get('limit') || '100');
    const offset = parseInt(searchParams.get('offset') || '0');

    const where: any = {};

    if (modelId) {
      where.modelId = parseInt(modelId);
    }

    if (type) {
      where.type = type;
    }

    if (ecosystem) {
      where.ecosystem = ecosystem;
    }

    const [models, total] = await Promise.all([
      prisma.modelMeta.findMany({
        where,
        include: {
          exampleJobs: {
            where: {
              status: 'completed',
            },
            take: 5, // 只返回最近的 5 个示例
            orderBy: {
              createdAt: 'desc',
            },
          },
        },
        orderBy: {
          createdAt: 'desc',
        },
        take: limit,
        skip: offset,
      }),
      prisma.modelMeta.count({ where }),
    ]);

    // 解析 JSON 字段
    const results = models.map(model => ({
      ...model,
      trainedWords: parseJsonOrNull<string[]>(model.trainedWords, []),
      exampleJobs: model.exampleJobs.map(job => ({
        ...job,
        results: parseJsonOrNull<string[]>(job.results, []),
      })),
    }));

    return createSuccessResponse({
      models: results,
      total,
      limit,
      offset,
    });
  } catch (error) {
    console.error('Get models error:', error);
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
    const validated = createModelMetaSchema.parse(body);

    const modelMeta = await prisma.modelMeta.create({
      data: {
        filename: validated.filename,
        name: validated.name,
        version: validated.version,
        desc: validated.desc,
        modelId: validated.modelId,
        type: validated.type,
        ecosystem: validated.ecosystem,
        baseModel: validated.baseModel,
        sha256: validated.sha256,
        trainedWords: validated.trainedWords ? stringifyJson(validated.trainedWords) : null,
        url: validated.url,
        webPageUrl: validated.webPageUrl,
        preference: validated.preference,
      },
    });

    // 返回时解析 trainedWords
    const result = {
      ...modelMeta,
      trainedWords: parseJsonOrNull<string[]>(modelMeta.trainedWords, []),
    };

    return createSuccessResponse(result);
  } catch (error) {
    if (error instanceof z.ZodError) {
      return createErrorResponse(error.errors[0].message, 400);
    }
    console.error('Create model meta error:', error);
    return createErrorResponse('Internal server error', 500);
  }
}
