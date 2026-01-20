"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ImageDisplay } from "@/components/ImageDisplay"
import { apiClient } from "@/lib/api/client"
import { Box, CheckCircle, Clock, XCircle, RefreshCw } from "lucide-react"
import { parseJsonOrNull } from "@/lib/utils/json"

interface Job {
  id: string
  name: string | null
  desc: string | null
  status: string
  source: string
  results: string
  createdAt: string
  completedAt: string | null
}

export default function TaskPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string | null>(null)

  useEffect(() => {
    loadJobs()
    // 每3秒刷新一次进行中的任务
    const interval = setInterval(() => {
      if (jobs.some((job) => job.status === "running" || job.status === "pending")) {
        loadJobs()
      }
    }, 3000)
    return () => clearInterval(interval)
  }, [statusFilter])

  const loadJobs = async () => {
    setLoading(true)
    try {
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter

      const response = await apiClient.get<{ jobs: Job[] }>("/job", params)

      if (response.success && response.data) {
        setJobs(response.data.jobs)
      }
    } catch (error) {
      console.error("加载任务失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case "running":
      case "pending":
        return <Clock className="h-5 w-5 text-yellow-500" />
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "completed":
        return "已完成"
      case "running":
        return "进行中"
      case "pending":
        return "等待中"
      case "failed":
        return "失败"
      default:
        return "未知"
    }
  }

  const getResults = (results: string): string[] => {
    return parseJsonOrNull<string[]>(results) || []
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Box className="h-8 w-8" />
            任务管理
          </h1>
          <p className="mt-2 text-muted-foreground">查看和管理绘图任务</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={loadJobs}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>

      {/* 状态筛选 */}
      <div className="flex gap-2">
        <Button
          variant={statusFilter === null ? "default" : "outline"}
          onClick={() => setStatusFilter(null)}
        >
          全部
        </Button>
        <Button
          variant={statusFilter === "pending" ? "default" : "outline"}
          onClick={() => setStatusFilter(statusFilter === "pending" ? null : "pending")}
        >
          等待中
        </Button>
        <Button
          variant={statusFilter === "running" ? "default" : "outline"}
          onClick={() => setStatusFilter(statusFilter === "running" ? null : "running")}
        >
          进行中
        </Button>
        <Button
          variant={statusFilter === "completed" ? "default" : "outline"}
          onClick={() => setStatusFilter(statusFilter === "completed" ? null : "completed")}
        >
          已完成
        </Button>
        <Button
          variant={statusFilter === "failed" ? "default" : "outline"}
          onClick={() => setStatusFilter(statusFilter === "failed" ? null : "failed")}
        >
          失败
        </Button>
      </div>

      {loading ? (
        <p className="text-muted-foreground">加载中...</p>
      ) : jobs.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-center text-muted-foreground">暂无任务</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {jobs.map((job) => {
            const results = getResults(job.results)
            const firstResult = results[0]

            return (
              <Card key={job.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(job.status)}
                      <CardTitle className="text-lg">
                        {job.name || `任务 ${job.id.slice(0, 8)}`}
                      </CardTitle>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {getStatusText(job.status)}
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  {job.desc && (
                    <p className="text-sm text-muted-foreground mb-3">{job.desc}</p>
                  )}
                  {firstResult && (
                    <div className="mb-3">
                      <ImageDisplay
                        hash={firstResult}
                        alt={job.name || "任务结果"}
                        width={200}
                        height={200}
                        className="rounded-lg border"
                      />
                    </div>
                  )}
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>来源: {job.source}</span>
                    <span>创建时间: {new Date(job.createdAt).toLocaleString()}</span>
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
