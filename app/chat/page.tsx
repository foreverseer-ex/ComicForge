"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useProjectStore } from "@/lib/stores/project-store"
import { apiClient } from "@/lib/api/client"
import { MessageSquare, Send } from "lucide-react"
import { cn } from "@/lib/utils"
import { parseJsonOrNull } from "@/lib/utils/json"

interface ChatMessage {
  id: string
  role: string
  context: string
  status: string
  tools: string | null
  suggests: string | null
  createdAt: string
}

export default function ChatPage() {
  const { currentProjectId } = useProjectStore()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (currentProjectId) {
      loadMessages()
    }
  }, [currentProjectId])

  const loadMessages = async () => {
    if (!currentProjectId) return

    try {
      const response = await apiClient.get<{ messages: ChatMessage[] }>("/chat", {
        projectId: currentProjectId,
      })

      if (response.success && response.data) {
        setMessages(response.data.messages)
      }
    } catch (error) {
      console.error("加载消息失败:", error)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || !currentProjectId || loading) return

    const userMessage = input
    setInput("")
    setLoading(true)

    // 添加用户消息到列表
    const tempUserMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      context: userMessage,
      status: "ready",
      tools: null,
      suggests: null,
      createdAt: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, tempUserMessage])

    try {
      const response = await apiClient.post<{ message: ChatMessage }>("/chat", {
        projectId: currentProjectId,
        role: "user",
        context: userMessage,
        index: messages.length,
      })

      if (response.success && response.data) {
        setMessages((prev) => [...prev, response.data!.message])
      }
    } catch (error) {
      console.error("发送消息失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const getSuggests = (suggests: string | null): string[] => {
    if (!suggests) return []
    return parseJsonOrNull<string[]>(suggests) || []
  }

  return (
    <div className="h-[calc(100vh-12rem)] flex flex-col">
      <div className="mb-6 flex-shrink-0">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <MessageSquare className="h-8 w-8" />
          聊天对话
        </h1>
        <p className="mt-2 text-muted-foreground">与 AI 助手对话，管理项目和内容</p>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden min-h-0">
        <div className="flex-1 overflow-y-auto space-y-4 px-2">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-center text-muted-foreground">暂无消息</p>
            </div>
          ) : (
            messages.map((message) => {
              const suggests = getSuggests(message.suggests)

              return (
                <div
                  key={message.id}
                  className={cn(
                    "flex my-2",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] rounded-lg p-3 text-sm",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    )}
                  >
                    <p className="whitespace-pre-wrap">{message.context}</p>
                    {suggests.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {suggests.map((suggest, index) => (
                          <Button
                            key={index}
                            variant="outline"
                            size="sm"
                            onClick={() => setInput(suggest)}
                            className="text-xs"
                          >
                            {suggest}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>
        <div className="flex gap-2 flex-shrink-0 p-4">
          <Input
            type="text"
            placeholder="输入消息..."
            className="flex-1"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
          />
          <Button onClick={handleSend} disabled={loading || !input.trim()}>
            <Send className="h-4 w-4 mr-2" />
            发送
          </Button>
        </div>
      </div>
    </div>
  )
}
