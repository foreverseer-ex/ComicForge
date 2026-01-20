"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ProjectSelector } from "@/components/ProjectSelector"
import { ImageDisplay } from "@/components/ImageDisplay"
import { useProjectStore } from "@/lib/stores/project-store"
import { apiClient } from "@/lib/api/client"
import { Users, Plus } from "lucide-react"
import { parseJsonOrNull } from "@/lib/utils/json"

interface Actor {
  id: string
  name: string
  desc: string
  color: string
  tags: string | null
  isTemplate: boolean
  projectId: string | null
}

export default function ActorPage() {
  const { currentProjectId } = useProjectStore()
  const [actors, setActors] = useState<Actor[]>([])
  const [templates, setTemplates] = useState<Actor[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadActors()
    loadTemplates()
  }, [currentProjectId])

  const loadActors = async () => {
    if (!currentProjectId) {
      setActors([])
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.get<{ actors: Actor[] }>("/actor", {
        projectId: currentProjectId,
      })

      if (response.success && response.data) {
        setActors(response.data.actors)
      }
    } catch (error) {
      console.error("加载角色失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const loadTemplates = async () => {
    try {
      const response = await apiClient.get<Actor[]>("/actor/templates")

      if (response.success && response.data) {
        const templatesList = Array.isArray(response.data) ? response.data : []
        setTemplates(templatesList)
      }
    } catch (error) {
      console.error("加载模板失败:", error)
    }
  }

  const getActorExamples = (actorId: string): string[] => {
    // 这里应该从 Job 表中查询 source = 'actor_example' 且 actorId 匹配的任务
    // 暂时返回空数组
    return []
  }

  const getTags = (tags: string | null): string[] => {
    if (!tags) return []
    const parsed = parseJsonOrNull<Record<string, string[]>>(tags)
    if (!parsed) return []
    return Object.values(parsed).flat()
  }

  const renderActorCard = (actor: Actor) => {
    const tags = getTags(actor.tags)
    const examples = getActorExamples(actor.id)
    const firstExample = examples[0]

    return (
      <Card key={actor.id}>
        <CardHeader>
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: actor.color }}
            />
            <CardTitle>{actor.name}</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {actor.desc}
          </p>
          {firstExample && (
            <div className="mb-3">
              <ImageDisplay
                hash={firstExample}
                alt={actor.name}
                width={200}
                height={150}
                className="rounded-lg border w-full"
              />
            </div>
          )}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 text-xs bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="h-8 w-8" />
            角色管理
          </h1>
          <p className="mt-2 text-muted-foreground">管理你的角色设定和特征</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          创建角色
        </Button>
      </div>

      {/* 角色分栏 */}
      <div className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold mb-4">角色</h2>
          {loading ? (
            <p className="text-muted-foreground">加载中...</p>
          ) : !currentProjectId ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">请先选择一个项目</p>
              </CardContent>
            </Card>
          ) : actors.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">暂无角色，请先创建</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {actors.map(renderActorCard)}
            </div>
          )}
        </div>

        {/* 模板分栏 */}
        <div>
          <h2 className="text-xl font-semibold mb-4">模板</h2>
          {templates.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">暂无模板</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {templates.map(renderActorCard)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
