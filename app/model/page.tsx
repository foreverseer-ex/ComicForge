"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ImageDisplay } from "@/components/ImageDisplay"
import { apiClient } from "@/lib/api/client"
import { Box } from "lucide-react"
import { parseJsonOrNull } from "@/lib/utils/json"

interface ModelMeta {
  versionId: number
  filename: string
  name: string
  version: string
  desc: string | null
  type: string
  ecosystem: string
  baseModel: string | null
}

interface Job {
  id: string
  results: string
}

export default function ModelPage() {
  const [models, setModels] = useState<ModelMeta[]>([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState<{
    type?: string
    ecosystem?: string
  }>({})

  useEffect(() => {
    loadModels()
  }, [filter])

  const loadModels = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (filter.type) params.type = filter.type
      if (filter.ecosystem) params.ecosystem = filter.ecosystem

      const response = await apiClient.get<{ models: ModelMeta[] }>("/model", params)

      if (response.success && response.data) {
        setModels(response.data.models)
      }
    } catch (error) {
      console.error("加载模型失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const getModelExample = (modelId: number): string | null => {
    // 这里应该从 Job 表中查询 source = 'model_example' 且 modelMetaId 匹配的任务
    // 暂时返回 null
    return null
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Box className="h-8 w-8" />
          模型管理
        </h1>
        <p className="mt-2 text-muted-foreground">管理 Stable Diffusion 模型和 LoRA</p>
      </div>

      {/* 筛选 */}
      <div className="flex gap-2">
        <Button
          variant={filter.type === "checkpoint" ? "default" : "outline"}
          onClick={() =>
            setFilter((prev) => ({
              ...prev,
              type: prev.type === "checkpoint" ? undefined : "checkpoint",
            }))
          }
        >
          Checkpoint
        </Button>
        <Button
          variant={filter.type === "lora" ? "default" : "outline"}
          onClick={() =>
            setFilter((prev) => ({
              ...prev,
              type: prev.type === "lora" ? undefined : "lora",
            }))
          }
        >
          LoRA
        </Button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">加载中...</p>
      ) : models.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">暂无模型</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {models.map((model) => {
            const example = getModelExample(model.versionId)

            return (
              <Card key={model.versionId}>
                <CardHeader>
                  <CardTitle>{model.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">类型:</span>
                      <span>{model.type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">生态系统:</span>
                      <span>{model.ecosystem}</span>
                    </div>
                    {model.baseModel && (
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">基础模型:</span>
                        <span>{model.baseModel}</span>
                      </div>
                    )}
                    {example && (
                      <div className="mt-2">
                        <ImageDisplay
                          hash={example}
                          alt={model.name}
                          width={200}
                          height={150}
                          className="rounded-lg border w-full"
                        />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
