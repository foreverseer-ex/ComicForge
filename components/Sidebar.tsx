"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { cn } from "@/lib/utils"
import { useSidebarStore } from "@/lib/stores/sidebar-store"
import { useAuthStore } from "@/lib/stores/auth-store"
import { 
  Home, 
  MessageSquare, 
  Users, 
  Brain, 
  FileText, 
  Box, 
  Settings, 
  HelpCircle,
  LogIn,
  LogOut,
  ChevronLeft,
  ChevronRight
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const navigation = [
  { name: "主页", href: "/", icon: Home },
  { name: "聊天", href: "/chat", icon: MessageSquare },
  { name: "角色", href: "/actor", icon: Users },
  { name: "记忆", href: "/memory", icon: Brain },
  { name: "内容", href: "/content", icon: FileText },
  { name: "模型", href: "/model", icon: Box },
  { name: "任务", href: "/task", icon: Box },
  { name: "设置", href: "/settings", icon: Settings },
  { name: "帮助", href: "/help", icon: HelpCircle },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { isCollapsed, toggleSidebar } = useSidebarStore()
  const { isAuthenticated, user, logout } = useAuthStore()
  const [isHovered, setIsHovered] = useState(false)

  const handleLogout = () => {
    logout()
    router.push("/login")
  }

  return (
    <>
      {/* 包装容器：包含触发区域和侧边栏 */}
      <div
        className="fixed top-0 left-0 bottom-0 z-50 overflow-hidden"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* 悬停触发区域（左侧边缘，透明，用于触发显示） */}
        <div className="w-4 absolute top-0 left-0 bottom-0 z-10" />
        
        {/* 侧边栏 */}
        <div
          className={cn(
            "fixed top-0 left-0 bottom-0 flex h-screen flex-col border-r border-primary/50 bg-gradient-to-b from-card/95 via-primary/5 to-accent/5 backdrop-blur-md transition-all duration-300 ease-in-out",
            isCollapsed && !isHovered ? "translate-x-[-calc(100%-4rem)]" : "translate-x-0",
            isCollapsed && isHovered ? "w-16" : isCollapsed ? "w-16" : "w-64"
          )}
          style={{
            willChange: 'transform',
          }}
        >
      <div className={cn(
        "flex h-16 items-center border-b border-primary/50 bg-gradient-to-r from-primary/8 via-purple-500/5 to-accent/8 transition-all duration-300",
        isCollapsed ? "justify-center px-2" : "justify-between px-4"
      )}>
        {!isCollapsed && (
          <span className="text-xl font-bold">ComicForge</span>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="h-8 w-8"
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          const linkContent = (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-300",
                isActive
                  ? "bg-gradient-to-r from-primary/40 via-purple-500/30 to-accent/35 text-primary border-2 border-primary/60 border-accent/40"
                  : "text-muted-foreground bg-transparent border-2 border-transparent hover:bg-gradient-to-r hover:from-primary/25 hover:via-accent/18 hover:to-info/20 hover:text-primary hover:border-primary/40 hover:border-accent/30 active:bg-gradient-to-r active:from-primary/35 active:via-accent/25 active:to-info/28 active:border-primary/50",
                isCollapsed && "justify-center"
              )}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!isCollapsed && <span>{item.name}</span>}
            </Link>
          )

          if (isCollapsed) {
            return (
              <TooltipProvider key={item.name}>
                <Tooltip>
                  <TooltipTrigger asChild>
                    {linkContent}
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>{item.name}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )
          }

          return linkContent
        })}
      </nav>
      <div className="border-t p-4 space-y-2">
        {isAuthenticated ? (
          <>
            {!isCollapsed && (
              <div className="px-3 py-2 text-xs text-muted-foreground">
                {user?.username}
              </div>
            )}
            {isCollapsed ? (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={handleLogout}
                      className="w-full"
                    >
                      <LogOut className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>登出</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <Button
                variant="ghost"
                onClick={handleLogout}
                className="w-full justify-start"
              >
                <LogOut className="h-5 w-5 mr-2" />
                <span>登出</span>
              </Button>
            )}
          </>
        ) : (
          <>
            {isCollapsed ? (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Link
                      href="/login"
                      className="flex items-center justify-center rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground bg-transparent border border-transparent hover:bg-gradient-to-r hover:from-primary/25 hover:via-accent/18 hover:to-info/20 hover:text-primary hover:border-primary/40 hover:border-accent/30 transition-all duration-300"
                    >
                      <LogIn className="h-5 w-5 flex-shrink-0" />
                    </Link>
                  </TooltipTrigger>
                  <TooltipContent side="right">
                    <p>登录</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            ) : (
              <Link
                href="/login"
                className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground bg-transparent border border-transparent hover:bg-gradient-to-r hover:from-primary/25 hover:via-accent/18 hover:to-info/20 hover:text-primary hover:border-primary/40 hover:border-accent/30 transition-all duration-300"
              >
                <LogIn className="h-5 w-5 flex-shrink-0" />
                <span>登录</span>
              </Link>
            )}
          </>
        )}
      </div>
        </div>
      </div>
    </>
  )
}
