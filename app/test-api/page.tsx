"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function TestApiPage() {
  const [token, setToken] = useState("")
  const [result, setResult] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const testLogin = async () => {
    setLoading(true)
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: "admin",
          password: "admin123",
        }),
      })
      const data = await res.json()
      setResult(data)
      if (data.success && data.data?.token) {
        setToken(data.data.token)
      }
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetMe = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetProjects = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/project", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testCreateProject = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/project", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: "测试项目",
          projectPath: "/test/path",
        }),
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetActors = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/actor", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testCreateActor = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/actor", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          projectId: null,
          name: "测试角色",
          desc: "这是一个测试角色",
          color: "#FF0000",
          tags: { "角色定位": "主角" },
          isTemplate: false,
        }),
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetTemplates = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/actor/templates", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testCreateTemplate = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/actor", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          projectId: null,
          name: "白皙少女",
          desc: "用于生成白皙少女角色的参考模板",
          color: "#FFFFFF",
          tags: { "类型": "角色模板" },
          isTemplate: true,
        }),
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testCreateDrawArgs = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/draw-args", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "test-model.safetensors",
          prompt: "a beautiful girl",
          negativePrompt: "bad quality",
          steps: 30,
          cfgScale: 7.0,
          width: 1024,
          height: 1024,
        }),
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testCreateJob = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      // 先创建绘图参数
      const drawArgsRes = await fetch("/api/draw-args", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: "test-model.safetensors",
          prompt: "test prompt",
          steps: 30,
        }),
      })
      const drawArgsData = await drawArgsRes.json()
      
      if (!drawArgsData.success) {
        setResult(drawArgsData)
        return
      }

      // 创建任务
      const res = await fetch("/api/job", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: "测试任务",
          desc: "这是一个测试绘图任务",
          status: "pending",
          source: "single",
          drawArgsId: drawArgsData.data.id,
        }),
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetJobs = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/job", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetChatMessages = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/chat", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testCreateChatMessage = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          index: 0,
          status: "ready",
          messageType: "normal",
          role: "user",
          context: "这是一条测试消息",
        }),
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetModels = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      const res = await fetch("/api/model", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testUploadTxt = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      // 先获取或创建一个项目
      const projectsRes = await fetch("/api/project", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const projectsData = await projectsRes.json()
      
      let projectId: string;
      if (projectsData.success && projectsData.data && projectsData.data.length > 0) {
        projectId = projectsData.data[0].id
      } else {
        // 创建新项目
        const createRes = await fetch("/api/project", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: "测试项目",
            projectPath: "/test/path",
          }),
        })
        const createData = await createRes.json()
        if (!createData.success) {
          setResult(createData)
          return
        }
        projectId = createData.data.id
      }

      // 创建测试 TXT 内容
      const txtContent = `第一章 开始

这是第一章的第一段内容。
这是第一章的第二段内容。

第二章 继续

这是第二章的第一段内容。
这是第二章的第二段内容。

第三章 结束

这是第三章的内容。`

      // 创建 Blob 并上传
      const blob = new Blob([txtContent], { type: 'text/plain' })
      const file = new File([blob], 'test.txt', { type: 'text/plain' })
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('projectId', projectId)

      const res = await fetch("/api/content/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetChapters = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      // 先获取项目 ID
      const projectsRes = await fetch("/api/project", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const projectsData = await projectsRes.json()
      
      if (!projectsData.success || !projectsData.data || projectsData.data.length === 0) {
        setResult({ error: "请先创建项目" })
        return
      }

      const projectId = projectsData.data[0].id

      const res = await fetch(`/api/content/chapters?projectId=${projectId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  const testGetContentStats = async () => {
    if (!token) {
      setResult({ error: "请先登录" })
      return
    }
    setLoading(true)
    try {
      // 先获取项目 ID
      const projectsRes = await fetch("/api/project", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const projectsData = await projectsRes.json()
      
      if (!projectsData.success || !projectsData.data || projectsData.data.length === 0) {
        setResult({ error: "请先创建项目" })
        return
      }

      const projectId = projectsData.data[0].id

      const res = await fetch(`/api/content/stats?projectId=${projectId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const data = await res.json()
      setResult(data)
    } catch (error) {
      setResult({ error: String(error) })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto p-8">
      <Card>
        <CardHeader>
          <CardTitle>API 测试页面</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Token</Label>
            <Input value={token} readOnly placeholder="登录后自动填充" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Button onClick={testLogin} disabled={loading}>
              1. 测试登录
            </Button>
            <Button onClick={testGetMe} disabled={loading || !token}>
              2. 获取当前用户
            </Button>
            <Button onClick={testGetProjects} disabled={loading || !token}>
              3. 获取项目列表
            </Button>
            <Button onClick={testCreateProject} disabled={loading || !token}>
              4. 创建项目
            </Button>
            <Button onClick={testGetActors} disabled={loading || !token}>
              5. 获取角色列表
            </Button>
            <Button onClick={testCreateActor} disabled={loading || !token}>
              6. 创建角色
            </Button>
            <Button onClick={testGetTemplates} disabled={loading || !token}>
              7. 获取模板列表
            </Button>
            <Button onClick={testCreateTemplate} disabled={loading || !token}>
              8. 创建模板
            </Button>
            <Button onClick={testCreateDrawArgs} disabled={loading || !token}>
              9. 创建绘图参数
            </Button>
            <Button onClick={testCreateJob} disabled={loading || !token}>
              10. 创建任务
            </Button>
            <Button onClick={testGetJobs} disabled={loading || !token}>
              11. 获取任务列表
            </Button>
            <Button onClick={testGetChatMessages} disabled={loading || !token}>
              12. 获取聊天消息
            </Button>
            <Button onClick={testCreateChatMessage} disabled={loading || !token}>
              13. 创建聊天消息
            </Button>
            <Button onClick={testGetModels} disabled={loading || !token}>
              14. 获取模型列表
            </Button>
            <Button onClick={testUploadTxt} disabled={loading || !token}>
              15. 上传 TXT 文件
            </Button>
            <Button onClick={testGetChapters} disabled={loading || !token}>
              16. 获取章节列表
            </Button>
            <Button onClick={testGetContentStats} disabled={loading || !token}>
              17. 获取内容统计
            </Button>
          </div>

          {result && (
            <div className="mt-4">
              <Label>结果</Label>
              <pre className="mt-2 p-4 bg-muted rounded-md overflow-auto max-h-96">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
