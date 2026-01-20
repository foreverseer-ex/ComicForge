"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { 
  Home, 
  MessageSquare, 
  Users, 
  Brain, 
  FileText, 
  Box, 
  Settings, 
  HelpCircle,
  LogIn
} from "lucide-react"

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

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold text-gray-900 dark:text-white">
                ComicForge
              </span>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={cn(
                      "inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors",
                      isActive
                        ? "border-indigo-500 text-gray-900 dark:text-white"
                        : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                    )}
                  >
                    <Icon className="mr-2 h-4 w-4" />
                    {item.name}
                  </Link>
                )
              })}
            </div>
          </div>
          <div className="flex items-center">
            <Link
              href="/login"
              className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            >
              <LogIn className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}
