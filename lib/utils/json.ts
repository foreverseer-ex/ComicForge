/**
 * JSON 序列化/反序列化工具函数
 * 
 * 用于处理 SQLite 中存储的 JSON 字符串
 */

/**
 * 安全地将值序列化为 JSON 字符串
 */
export function stringifyJson(value: any): string {
  if (value === null || value === undefined) {
    return '';
  }
  try {
    return JSON.stringify(value);
  } catch {
    return '';
  }
}

/**
 * 安全地将 JSON 字符串反序列化为值
 */
export function parseJson<T = any>(value: string | null | undefined, defaultValue: T): T {
  if (!value || value === '') {
    return defaultValue;
  }
  try {
    return JSON.parse(value) as T;
  } catch {
    return defaultValue;
  }
}

/**
 * 解析 JSON 字符串，如果失败返回 null
 */
export function parseJsonOrNull<T = any>(value: string | null | undefined): T | null {
  if (!value || value === '') {
    return null;
  }
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
}
