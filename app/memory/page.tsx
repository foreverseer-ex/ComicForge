"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ProjectSelector } from "@/components/ProjectSelector"
import { useProjectStore } from "@/lib/stores/project-store"
import { apiClient } from "@/lib/api/client"
import { Brain, Plus } from "lucide-react"

interface Memory {
  id: string
  key: string
  value: string
  projectId: string
}

export default function MemoryPage() {
  const { currentProjectId } = useProjectStore()
  const [memories, setMemories] = useState<Memory[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (currentProjectId) {
      loadMemories()
    }
  }, [currentProjectId])

  const loadMemories = async () => {
    if (!currentProjectId) return

    setLoading(true)
    try {
      const response = await apiClient.get<{ memories: Memory[] }>("/memory", {
        projectId: currentProjectId,
      })

      if (response.success && response.data) {
        setMemories(response.data.memories)
      }
    } catch (error) {
      console.error("加载记忆失败:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-8 w-8" />
            记忆管理
          </h1>
          <p className="mt-2 text-muted-foreground">管理 AI 助手的记忆和上下文信息</p>
        </div>
        <div className="flex gap-2">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            添加记忆
          </Button>
        </div>
      </div>

      {loading ? (
        <p className="text-muted-foreground">加载中...</p>
      ) : memories.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              {currentProjectId ? "暂无记忆，请先添加" : "请先选择一个项目"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {memories.map((memory) => (
            <Card key={memory.id}>
              <CardHeader>
                <CardTitle className="text-lg">{memory.key}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-base whitespace-pre-wrap">{memory.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
