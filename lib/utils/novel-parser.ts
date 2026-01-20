/**
 * 小说文件解析工具
 * 
 * 支持 TXT 文件解析，识别章节并提取内容
 */

import fs from 'fs/promises';
import path from 'path';
import iconv from 'iconv-lite';
import { detect } from 'chardet';

// 类型定义（如果 chardet 没有类型定义）
declare module 'chardet' {
  export function detect(buffer: Buffer): string | null;
}

export interface ChapterInfo {
  chapter: number;
  title: string;
  startLine: number;
  endLine: number;
}

export interface ParsedContent {
  chapters: ChapterInfo[];
  lines: Array<{
    chapter: number;
    line: number;
    content: string;
  }>;
  totalLines: number;
  totalChapters: number;
}

/**
 * 检测文件编码
 */
async function detectEncoding(buffer: Buffer): Promise<string> {
  // 尝试使用 chardet 检测
  try {
    const detected = detect(buffer);
    if (detected) {
      const encoding = detected.toLowerCase();
      // 映射常见编码
      const encodingMap: Record<string, string> = {
        'utf-8': 'utf8',
        'utf8': 'utf8',
        'gb2312': 'gb2312',
        'gbk': 'gbk',
        'gb18030': 'gb18030',
        'big5': 'big5',
      };
      const mapped = encodingMap[encoding];
      if (mapped) {
        // 验证编码是否有效
        try {
          iconv.decode(buffer, mapped);
          return mapped;
        } catch {
          // 编码无效，继续尝试
        }
      }
    }
  } catch {
    // chardet 检测失败
  }

  // 按顺序尝试常见编码
  const encodings = ['utf8', 'gbk', 'gb2312', 'gb18030', 'big5'];
  for (const enc of encodings) {
    try {
      const decoded = iconv.decode(buffer, enc);
      // 简单验证：如果解码成功且没有明显的乱码，使用该编码
      if (decoded.length > 0) {
        return enc;
      }
    } catch {
      // 继续尝试下一个编码
    }
  }

  // 默认返回 UTF-8
  return 'utf8';
}

/**
 * 识别章节标题
 */
function detectChapterTitle(line: string, lineNumber: number): { isChapter: boolean; chapterNumber?: number; title?: string } {
  // 去除首尾空白
  const trimmed = line.trim();
  if (!trimmed) {
    return { isChapter: false };
  }

  // 章节识别正则表达式
  const chapterPatterns = [
    // 第X章
    /^第[一二三四五六七八九十百千万\d]+章[：:\s]*(.+)$/,
    // Chapter X
    /^[Cc]hapter\s+(\d+)[：:\s]*(.+)$/i,
    // Chapter X (罗马数字)
    /^[Cc]hapter\s+([IVX]+)[：:\s]*(.+)$/i,
    // 数字开头：1. 或 1-
    /^(\d+)[\.\-][\s]*(.+)$/,
    // 纯数字章节号（单独一行）
    /^(\d+)$/,
    // 中文数字章节
    /^[一二三四五六七八九十百千万]+[、．.][\s]*(.+)$/,
  ];

  for (const pattern of chapterPatterns) {
    const match = trimmed.match(pattern);
    if (match) {
      let chapterNumber: number;
      let title: string = '';

      if (match.length === 2) {
        // 只有章节号，没有标题
        const numStr = match[1];
        chapterNumber = parseChapterNumber(numStr);
        title = `第${numStr}章`;
      } else if (match.length === 3) {
        // 有章节号和标题
        const numStr = match[1];
        chapterNumber = parseChapterNumber(numStr);
        title = match[2].trim() || `第${numStr}章`;
      } else {
        continue;
      }

      if (chapterNumber > 0) {
        return { isChapter: true, chapterNumber, title };
      }
    }
  }

  return { isChapter: false };
}

/**
 * 解析章节号（支持中文数字和阿拉伯数字）
 */
function parseChapterNumber(numStr: string): number {
  // 如果是纯数字
  if (/^\d+$/.test(numStr)) {
    return parseInt(numStr, 10);
  }

  // 中文数字转阿拉伯数字
  const chineseNumbers: Record<string, number> = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '百': 100, '千': 1000, '万': 10000,
  };

  // 简单的中文数字解析（支持 一、二、十、十一、二十等）
  let result = 0;
  let temp = 0;

  for (let i = 0; i < numStr.length; i++) {
    const char = numStr[i];
    if (chineseNumbers[char]) {
      const value = chineseNumbers[char];
      if (value >= 10) {
        if (temp === 0) temp = 1;
        temp *= value;
      } else {
        temp += value;
      }
    } else if (/\d/.test(char)) {
      // 混合了阿拉伯数字
      return parseInt(numStr.replace(/[^\d]/g, ''), 10) || 1;
    }
  }

  result = temp || 1;
  return result > 0 ? result : 1;
}

/**
 * 解析 TXT 文件
 */
export async function parseTxtFile(filePath: string): Promise<ParsedContent> {
  // 读取文件
  const buffer = await fs.readFile(filePath);

  // 检测编码
  const encoding = await detectEncoding(buffer);

  // 解码文本
  let text: string;
  try {
    text = iconv.decode(buffer, encoding);
  } catch (error) {
    // 如果指定编码失败，尝试 UTF-8
    try {
      text = iconv.decode(buffer, 'utf8');
    } catch {
      // 最后尝试 GBK
      text = iconv.decode(buffer, 'gbk');
    }
  }

  // 按行分割
  const lines = text.split(/\r?\n/);

  // 识别章节
  const chapters: ChapterInfo[] = [];
  const contentLines: Array<{ chapter: number; line: number; content: string }> = [];

  let currentChapter = 1;
  let lineNumber = 1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const chapterInfo = detectChapterTitle(line, i + 1);

    if (chapterInfo.isChapter && chapterInfo.chapterNumber) {
      // 发现新章节
      currentChapter = chapterInfo.chapterNumber;

      // 记录章节信息
      chapters.push({
        chapter: currentChapter,
        title: chapterInfo.title || `第${currentChapter}章`,
        startLine: lineNumber,
        endLine: lineNumber, // 暂时，后面会更新
      });

      // 章节标题也作为一行内容
      contentLines.push({
        chapter: currentChapter,
        line: lineNumber,
        content: line.trim(),
      });
      lineNumber++;
    } else {
      // 普通内容行
      const trimmed = line.trim();
      if (trimmed || contentLines.length > 0) {
        // 保留非空行，或者如果已经有内容则保留空行（可能是段落分隔）
        contentLines.push({
          chapter: currentChapter,
          line: lineNumber,
          content: trimmed,
        });
        lineNumber++;
      }
    }
  }

  // 更新章节的结束行号
  for (let i = 0; i < chapters.length; i++) {
    const chapter = chapters[i];
    const nextChapter = chapters[i + 1];
    chapter.endLine = nextChapter ? nextChapter.startLine - 1 : lineNumber - 1;
  }

  // 如果没有识别到章节，将所有内容作为第1章
  if (chapters.length === 0) {
    chapters.push({
      chapter: 1,
      title: '第1章',
      startLine: 1,
      endLine: contentLines.length,
    });
  }

  return {
    chapters,
    lines: contentLines,
    totalLines: contentLines.length,
    totalChapters: chapters.length,
  };
}

/**
 * 从 Buffer 解析 TXT 文件（用于上传的文件）
 */
export async function parseTxtBuffer(buffer: Buffer): Promise<ParsedContent> {
  // 检测编码
  const encoding = await detectEncoding(buffer);

  // 解码文本
  let text: string;
  try {
    text = iconv.decode(buffer, encoding);
  } catch (error) {
    // 如果指定编码失败，尝试 UTF-8
    try {
      text = iconv.decode(buffer, 'utf8');
    } catch {
      // 最后尝试 GBK
      text = iconv.decode(buffer, 'gbk');
    }
  }

  // 按行分割
  const lines = text.split(/\r?\n/);

  // 识别章节
  const chapters: ChapterInfo[] = [];
  const contentLines: Array<{ chapter: number; line: number; content: string }> = [];

  let currentChapter = 1;
  let lineNumber = 1;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const chapterInfo = detectChapterTitle(line, i + 1);

    if (chapterInfo.isChapter && chapterInfo.chapterNumber) {
      // 发现新章节
      currentChapter = chapterInfo.chapterNumber;

      // 记录章节信息
      chapters.push({
        chapter: currentChapter,
        title: chapterInfo.title || `第${currentChapter}章`,
        startLine: lineNumber,
        endLine: lineNumber, // 暂时，后面会更新
      });

      // 章节标题也作为一行内容
      contentLines.push({
        chapter: currentChapter,
        line: lineNumber,
        content: line.trim(),
      });
      lineNumber++;
    } else {
      // 普通内容行
      const trimmed = line.trim();
      if (trimmed || contentLines.length > 0) {
        // 保留非空行，或者如果已经有内容则保留空行（可能是段落分隔）
        contentLines.push({
          chapter: currentChapter,
          line: lineNumber,
          content: trimmed,
        });
        lineNumber++;
      }
    }
  }

  // 更新章节的结束行号
  for (let i = 0; i < chapters.length; i++) {
    const chapter = chapters[i];
    const nextChapter = chapters[i + 1];
    chapter.endLine = nextChapter ? nextChapter.startLine - 1 : lineNumber - 1;
  }

  // 如果没有识别到章节，将所有内容作为第1章
  if (chapters.length === 0) {
    chapters.push({
      chapter: 1,
      title: '第1章',
      startLine: 1,
      endLine: contentLines.length,
    });
  }

  return {
    chapters,
    lines: contentLines,
    totalLines: contentLines.length,
    totalChapters: chapters.length,
  };
}
