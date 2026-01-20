"use client"

import { useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"
import { useAuthStore } from "@/lib/stores/auth-store"
import { useSettingsStore } from "@/lib/stores/settings-store"

const PUBLIC_PATHS = ["/login", "/settings", "/test-api"]

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const { isAuthenticated } = useAuthStore()
  const { dev } = useSettingsStore()

  useEffect(() => {
    // 如果未启用强制跳转，不执行检查
    if (!dev.enableAuthRedirect) {
      return
    }

    // 如果当前路径是公开路径，不需要检查
    if (PUBLIC_PATHS.includes(pathname)) {
      return
    }

    // 如果未登录，重定向到登录页
    if (!isAuthenticated) {
      router.push("/login")
    }
  }, [isAuthenticated, pathname, router, dev.enableAuthRedirect])

  // 如果是登录页且已登录，重定向到主页
  useEffect(() => {
    if (pathname === "/login" && isAuthenticated) {
      router.push("/")
    }
  }, [isAuthenticated, pathname, router])

  // 如果是公开路径或已登录，或者未启用强制跳转，显示内容
  if (PUBLIC_PATHS.includes(pathname) || isAuthenticated || !dev.enableAuthRedirect) {
    return <>{children}</>
  }

  // 未登录且不是公开路径，显示加载状态（即将重定向）
  return null
}
