/**
 * 确认对话框工具函数
 * 
 * 提供一个统一的接口来显示确认对话框，避免使用浏览器原生 confirm()
 */

export interface ConfirmDialogOptions {
  title?: string
  message: string
  type?: 'default' | 'danger'
  items?: string[]
  warningText?: string
  confirmText?: string
  cancelText?: string
  titleColor?: string
}

export interface ConfirmDialogRef {
  show: boolean
  title: string
  message: string
  type: 'default' | 'danger'
  items: string[]
  warningText: string
  confirmText: string
  cancelText: string
  titleColor?: string
  onConfirm: () => void | Promise<void>
}

/**
 * 创建确认对话框配置
 * 
 * @param options 对话框选项
 * @param onConfirm 确认回调函数
 * @returns 确认对话框配置对象
 */
export function createConfirmDialog(
  options: ConfirmDialogOptions,
  onConfirm: () => void | Promise<void>
): ConfirmDialogRef {
  return {
    show: true,
    title: options.title || '确认',
    message: options.message,
    type: options.type || 'default',
    items: options.items || [],
    warningText: options.warningText || '',
    confirmText: options.confirmText || '确定',
    cancelText: options.cancelText || '取消',
    titleColor: options.titleColor,
    onConfirm
  }
}

