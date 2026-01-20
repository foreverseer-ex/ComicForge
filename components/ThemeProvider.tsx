"use client"

import { useEffect, useState } from "react"
import { useThemeStore } from "@/lib/stores/theme-store"

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { theme, setResolvedTheme } = useThemeStore()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted) return

    const root = window.document.documentElement
    root.classList.remove("light", "dark")

    let resolvedTheme: "light" | "dark"

    if (theme === "system") {
      // 跟随系统：自动检测系统主题
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      resolvedTheme = systemTheme
    } else {
      // 手动设置：使用用户选择的主题
      resolvedTheme = theme
    }

    root.classList.add(resolvedTheme)
    setResolvedTheme(resolvedTheme)

    // 监听系统主题变化（仅在跟随系统模式下）
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)")
    const handleChange = (e: MediaQueryListEvent) => {
      if (theme === "system") {
        const newTheme = e.matches ? "dark" : "light"
        root.classList.remove("light", "dark")
        root.classList.add(newTheme)
        setResolvedTheme(newTheme)
      }
    }

    mediaQuery.addEventListener("change", handleChange)
    return () => mediaQuery.removeEventListener("change", handleChange)
  }, [theme, setResolvedTheme, mounted])

  // 防止 hydration 不匹配
  if (!mounted) {
    return <>{children}</>
  }

  return <>{children}</>
}
