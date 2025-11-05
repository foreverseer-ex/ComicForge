// 简单的 Toast 工具函数
let toastContainer: HTMLDivElement | null = null

function createToastContainer() {
  if (toastContainer) return toastContainer
  
  toastContainer = document.createElement('div')
  toastContainer.id = 'toast-container'
  toastContainer.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 8px;
    pointer-events: none;
  `
  document.body.appendChild(toastContainer)
  return toastContainer
}

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'success', duration: number = 3000) {
  const container = createToastContainer()
  
  const toast = document.createElement('div')
  toast.style.cssText = `
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    font-size: 14px;
    max-width: 400px;
    word-wrap: break-word;
    pointer-events: auto;
    animation: slideIn 0.3s ease-out;
  `
  
  // 添加动画样式（如果还没有）
  if (!document.getElementById('toast-animations')) {
    const style = document.createElement('style')
    style.id = 'toast-animations'
    style.textContent = `
      @keyframes slideIn {
        from {
          transform: translateX(100%);
          opacity: 0;
        }
        to {
          transform: translateX(0);
          opacity: 1;
        }
      }
      @keyframes slideOut {
        from {
          transform: translateX(0);
          opacity: 1;
        }
        to {
          transform: translateX(100%);
          opacity: 0;
        }
      }
    `
    document.head.appendChild(style)
  }
  
  toast.textContent = message
  
  container.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease-out'
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast)
      }
    }, 300)
  }, duration)
}

