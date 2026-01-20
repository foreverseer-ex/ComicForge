"use client"

import { useState } from "react"
import { useSidebarStore } from "@/lib/stores/sidebar-store"
import { cn } from "@/lib/utils"

export function MainContent({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebarStore()
  const [isHovered, setIsHovered] = useState(false)

  return (
    <main
      className={cn(
        "flex-1 overflow-y-auto transition-all duration-300 h-screen",
        // 当侧边栏折叠时，主内容区域占满整个宽度
        // 当侧边栏展开时，主内容区域有左边距
        isCollapsed ? "ml-16" : "ml-64"
      )}
      onMouseEnter={() => {
        if (isCollapsed) {
          setIsHovered(true)
        }
      }}
      onMouseLeave={() => {
        if (isCollapsed) {
          setIsHovered(false)
        }
      }}
    >
      <div className="container mx-auto p-6">
        {children}
      </div>
    </main>
  )
}
