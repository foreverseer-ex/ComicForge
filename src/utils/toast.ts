// 使用 shadcn 风格的 vue-sonner 作为全局 Toast
import { toast } from 'vue-sonner'

export function showToast(
  message: string,
  type: 'success' | 'error' | 'info' | 'warning' = 'success',
  duration: number = 3000
) {
  const common = { duration }
  switch (type) {
    case 'success':
      return toast.success(message, common)
    case 'error':
      return toast.error(message, common)
    case 'warning':
      return toast.warning(message, common)
    case 'info':
    default:
      return toast(message, common)
  }
}

