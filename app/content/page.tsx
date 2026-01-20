"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ProjectSelector } from "@/components/ProjectSelector"
import { useProjectStore } from "@/lib/stores/project-store"
import { apiClient } from "@/lib/api/client"
import { FileText, Upload } from "lucide-react"

interface Chapter {
  chapter: number
  lineCount?: number
}

export default function ContentPage() {
  const { currentProjectId } = useProjectStore()
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    totalLines: 0,
    totalChapters: 0,
    chaptersWithImages: 0,
  })

  useEffect(() => {
    if (currentProjectId) {
      loadChapters()
      loadStats()
    }
  }, [currentProjectId])

  const loadChapters = async () => {
    if (!currentProjectId) return

    setLoading(true)
    try {
      const response = await apiClient.get<{ chapters: number[] }>("/content/chapters", {
        projectId: currentProjectId,
      })

      if (response.success && response.data) {
        setChapters(
          response.data.chapters.map((ch) => ({
            chapter: ch,
          }))
        )
      }
    } catch (error) {
      console.error("加载章节失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    if (!currentProjectId) return

    try {
      const response = await apiClient.get<{
        totalLines: number
        totalChapters: number
        chaptersWithImages: number
      }>("/content/stats", {
        projectId: currentProjectId,
      })

      if (response.success && response.data) {
        setStats(response.data)
      }
    } catch (error) {
      console.error("加载统计信息失败:", error)
    }
  }

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file || !currentProjectId) return

    const formData = new FormData()
    formData.append("file", file)
    formData.append("projectId", currentProjectId)

    try {
      const response = await apiClient.post("/content/upload", formData, true)
      if (response.success) {
        loadChapters()
        loadStats()
      }
    } catch (error) {
      console.error("上传失败:", error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FileText className="h-8 w-8" />
            内容管理
          </h1>
          <p className="mt-2 text-muted-foreground">管理你的小说内容和章节</p>
        </div>
        <div className="flex gap-2">
          <label>
            <Button asChild>
              <span>
                <Upload className="h-4 w-4 mr-2" />
                上传文件
              </span>
            </Button>
            <input
              type="file"
              accept=".txt"
              className="hidden"
              onChange={handleUpload}
            />
          </label>
        </div>
      </div>

      {/* 统计信息 */}
      <Card>
        <CardHeader>
          <CardTitle>统计信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">总行数</p>
              <p className="text-2xl font-bold">{stats.totalLines}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">总章节数</p>
              <p className="text-2xl font-bold">{stats.totalChapters}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">有图片的章节</p>
              <p className="text-2xl font-bold">{stats.chaptersWithImages}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 章节列表 */}
      {loading ? (
        <p className="text-muted-foreground">加载中...</p>
      ) : chapters.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">
              {currentProjectId ? "暂无章节，请先上传文件" : "请先选择一个项目"}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {chapters.map((chapter) => (
            <Card key={chapter.chapter}>
              <CardHeader>
                <CardTitle>第 {chapter.chapter} 章</CardTitle>
              </CardHeader>
              <CardContent>
                <Button variant="outline" size="sm">
                  查看内容
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
