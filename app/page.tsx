"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ImageDisplay } from "@/components/ImageDisplay"
import { useProjectStore, Project } from "@/lib/stores/project-store"
import { apiClient } from "@/lib/api/client"
import { FileText, ChevronLeft, ChevronRight, Plus, Trash2, ChevronDown, Upload, X } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"

interface ContentLine {
  id: number
  chapter: number
  line: number
  content: string
  imageHash: string | null
}

interface Chapter {
  chapter: number
  lines: ContentLine[]
}

export default function Home() {
  const { currentProjectId, projects, setCurrentProject, setProjects, removeProject, getCurrentProject } = useProjectStore()
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [currentChapter, setCurrentChapter] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    totalLines: 0,
    totalChapters: 0,
    chaptersWithImages: 0,
  })
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [newProjectTitle, setNewProjectTitle] = useState("")
  const [newProjectDesc, setNewProjectDesc] = useState("")
  const [creating, setCreating] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const currentProject = getCurrentProject()

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const response = await apiClient.get<Project[]>("/project")
      if (response.success && response.data) {
        // API 返回的是 Project[] 数组，不是 { projects: Project[] }
        const projectsList = Array.isArray(response.data) ? response.data : []
        setProjects(projectsList)
        // 如果没有当前项目，选择第一个
        if (!currentProjectId && projectsList.length > 0) {
          setCurrentProject(projectsList[0].id)
        }
      }
    } catch (error) {
      console.error("加载项目失败:", error)
    }
  }

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
        const chapterNumbers = response.data.chapters
        if (chapterNumbers.length > 0) {
          setCurrentChapter(chapterNumbers[0])
          await loadChapterContent(chapterNumbers[0])
        }
      }
    } catch (error) {
      console.error("加载章节失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const loadChapterContent = async (chapter: number) => {
    if (!currentProjectId) return

    try {
      const response = await apiClient.get<{ contents: ContentLine[] }>(
        `/content/chapter/${chapter}`,
        { projectId: currentProjectId }
      )

      if (response.success && response.data) {
        setChapters((prev) => {
          const existing = prev.find((c) => c.chapter === chapter)
          if (existing) {
            return prev.map((c) =>
              c.chapter === chapter ? { ...c, lines: response.data!.contents } : c
            )
          }
          return [...prev, { chapter, lines: response.data!.contents }]
        })
      }
    } catch (error) {
      console.error("加载章节内容失败:", error)
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

  const handleCreateProject = async () => {
    if (!newProjectTitle.trim()) return

    setCreating(true)
    try {
      // 先创建项目
      const response = await apiClient.post<Project>("/project", {
        title: newProjectTitle,
        projectPath: `projects/${newProjectTitle}`,
        novelPath: newProjectDesc || undefined,
      })

      if (response.success && response.data) {
        const projectId = response.data.id

        // 如果有上传的文件，则上传文件
        if (uploadFile) {
          try {
            const formData = new FormData()
            formData.append("file", uploadFile)
            formData.append("projectId", projectId)

            await apiClient.post("/content/upload", formData, true)
          } catch (error) {
            console.error("上传文件失败:", error)
            // 即使上传失败，项目已创建，继续执行
          }
        }

        setProjects([...projects, response.data])
        setCurrentProject(projectId)
        setShowCreateDialog(false)
        setNewProjectTitle("")
        setNewProjectDesc("")
        setUploadFile(null)
      }
    } catch (error) {
      console.error("创建项目失败:", error)
    } finally {
      setCreating(false)
    }
  }

  const handleFileSelect = (file: File) => {
    if (file.name.toLowerCase().endsWith('.txt')) {
      setUploadFile(file)
    } else {
      alert('只支持上传 .txt 文件')
    }
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileSelect(file)
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm("确定要删除这个项目吗？此操作不可恢复。")) return

    try {
      const response = await apiClient.delete(`/project/${projectId}`)
      if (response.success) {
        removeProject(projectId)
        // 如果删除的是当前项目，选择第一个项目
        if (currentProjectId === projectId) {
          const remainingProjects = projects.filter((p) => p.id !== projectId)
          if (remainingProjects.length > 0) {
            setCurrentProject(remainingProjects[0].id)
          } else {
            setCurrentProject(null)
          }
        }
        loadProjects()
      }
    } catch (error) {
      console.error("删除项目失败:", error)
    }
  }

  const currentChapterData = chapters.find((c) => c.chapter === currentChapter)

  if (!currentProjectId) {
    return (
      <div className="space-y-6">
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">欢迎使用 ComicForge</h1>
            <p className="mt-2 text-muted-foreground">AI 驱动的漫画创作与可视化工具</p>
          </div>
          <div className="flex gap-2 items-center">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="flex-1 justify-between">
                  <span className="truncate">选择项目</span>
                  <ChevronDown className="h-4 w-4 ml-2 flex-shrink-0" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="min-w-[200px]">
                <DropdownMenuLabel>项目列表</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {projects.map((project) => (
                  <DropdownMenuItem
                    key={project.id}
                    onClick={() => setCurrentProject(project.id)}
                  >
                    {project.title}
                  </DropdownMenuItem>
                ))}
                {projects.length === 0 && (
                  <DropdownMenuItem disabled>暂无项目</DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
            <Button variant="blue" onClick={() => setShowCreateDialog(true)} className="flex-shrink-0">
              <Plus className="h-4 w-4 mr-2" />
              新建项目
            </Button>
          </div>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>新建项目</DialogTitle>
              <DialogDescription>
                创建一个新的项目来管理你的小说内容和图片
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="project-title">项目名称</Label>
                <Input
                  id="project-title"
                  value={newProjectTitle}
                  onChange={(e) => setNewProjectTitle(e.target.value)}
                  placeholder="请输入项目名称"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="project-desc">项目描述（可选）</Label>
                <Input
                  id="project-desc"
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="请输入项目描述"
                />
              </div>
              <div className="space-y-2">
                <Label>上传文件（可选）</Label>
                {uploadFile ? (
                  <div className="flex items-center justify-between p-3 border rounded-md bg-muted/50">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{uploadFile.name}</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setUploadFile(null)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <div
                    className={cn(
                      "border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors",
                      isDragging
                        ? "border-primary bg-primary/5"
                        : "border-muted-foreground/25 hover:border-primary/50"
                    )}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={() => {
                      const input = document.createElement("input")
                      input.type = "file"
                      input.accept = ".txt"
                      input.onchange = (e) => {
                        const file = (e.target as HTMLInputElement).files?.[0]
                        if (file) {
                          handleFileSelect(file)
                        }
                      }
                      input.click()
                    }}
                  >
                    <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      拖拽 TXT 文件到此处或点击选择
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      支持 .txt 格式
                    </p>
                  </div>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setShowCreateDialog(false)
                setNewProjectTitle("")
                setNewProjectDesc("")
                setUploadFile(null)
              }}>
                取消
              </Button>
              <Button variant="blue" onClick={handleCreateProject} disabled={creating || !newProjectTitle.trim()}>
                {creating ? "创建中..." : "创建"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
        {!showCreateDialog && (
          <Card 
            className="cursor-pointer"
            onClick={() => setShowCreateDialog(true)}
          >
            <CardContent className="pt-6">
              <p className="text-center text-muted-foreground">请先选择一个项目或创建新项目</p>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">ComicForge</h1>
          <p className="mt-2 text-muted-foreground">AI 驱动的漫画创作与可视化工具</p>
        </div>
        <div className="flex gap-2 items-center">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className="flex-1 justify-between">
                <span className="truncate">
                  {currentProject ? currentProject.title : "选择项目"}
                </span>
                <ChevronDown className="h-4 w-4 ml-2 flex-shrink-0" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="min-w-[200px]">
              <DropdownMenuLabel>项目列表</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {projects.map((project) => (
                <DropdownMenuItem
                  key={project.id}
                  onClick={() => setCurrentProject(project.id)}
                  className={currentProjectId === project.id ? "bg-accent" : ""}
                  onSelect={(e) => e.preventDefault()}
                >
                  <span className="flex-1">{project.title}</span>
                </DropdownMenuItem>
              ))}
              {projects.length === 0 && (
                <DropdownMenuItem disabled>暂无项目</DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
          <Button variant="blue" onClick={() => setShowCreateDialog(true)} className="flex-shrink-0">
            <Plus className="h-4 w-4 mr-2" />
            新建项目
          </Button>
          {currentProjectId && (
            <Button
              variant="red"
              onClick={() => handleDeleteProject(currentProjectId)}
              className="flex-shrink-0"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              删除项目
            </Button>
          )}
        </div>
      </div>

      {/* 新建项目对话框 */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建项目</DialogTitle>
            <DialogDescription>
              创建一个新的项目来管理你的小说内容和图片
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="project-title-dialog">项目名称</Label>
              <Input
                id="project-title-dialog"
                value={newProjectTitle}
                onChange={(e) => setNewProjectTitle(e.target.value)}
                placeholder="请输入项目名称"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-desc-dialog">项目描述（可选）</Label>
              <Input
                id="project-desc-dialog"
                value={newProjectDesc}
                onChange={(e) => setNewProjectDesc(e.target.value)}
                placeholder="请输入项目描述"
              />
            </div>
            <div className="space-y-2">
              <Label>上传文件（可选）</Label>
              {uploadFile ? (
                <div className="flex items-center justify-between p-3 border rounded-md bg-muted/50">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{uploadFile.name}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setUploadFile(null)}
                    className="h-8 w-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <div
                  className={cn(
                    "border-2 border-dashed rounded-md p-6 text-center cursor-pointer transition-colors",
                    isDragging
                      ? "border-primary bg-primary/5"
                      : "border-muted-foreground/25 hover:border-primary/50"
                  )}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => {
                    const input = document.createElement("input")
                    input.type = "file"
                    input.accept = ".txt"
                    input.onchange = (e) => {
                      const file = (e.target as HTMLInputElement).files?.[0]
                      if (file) {
                        handleFileSelect(file)
                      }
                    }
                    input.click()
                  }}
                >
                  <Upload className="h-8 w-8 mx-auto mb-2 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    拖拽 TXT 文件到此处或点击选择
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    支持 .txt 格式
                  </p>
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false)
              setNewProjectTitle("")
              setNewProjectDesc("")
              setUploadFile(null)
            }}>
              取消
            </Button>
            <Button variant="blue" onClick={handleCreateProject} disabled={creating || !newProjectTitle.trim()}>
              {creating ? "创建中..." : "创建"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 项目信息卡片 */}
      <Card>
        <CardHeader>
          <CardTitle>项目信息</CardTitle>
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

      {/* 小说段落展示 */}
      {currentChapter !== null && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>第 {currentChapter} 章</CardTitle>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const chapterNumbers = chapters.map((c) => c.chapter).sort((a, b) => a - b)
                    const currentIndex = chapterNumbers.indexOf(currentChapter)
                    if (currentIndex > 0) {
                      setCurrentChapter(chapterNumbers[currentIndex - 1])
                      loadChapterContent(chapterNumbers[currentIndex - 1])
                    }
                  }}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const chapterNumbers = chapters.map((c) => c.chapter).sort((a, b) => a - b)
                    const currentIndex = chapterNumbers.indexOf(currentChapter)
                    if (currentIndex < chapterNumbers.length - 1) {
                      setCurrentChapter(chapterNumbers[currentIndex + 1])
                      loadChapterContent(chapterNumbers[currentIndex + 1])
                    }
                  }}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-muted-foreground">加载中...</p>
            ) : currentChapterData && currentChapterData.lines.length > 0 ? (
              <div className="space-y-4">
                {currentChapterData.lines.map((line) => (
                  <div key={line.id} className="border-b pb-4 last:border-0">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <p className="text-sm text-muted-foreground mb-1">
                          第 {line.line} 行
                        </p>
                        <p className="whitespace-pre-wrap">{line.content}</p>
                      </div>
                      {line.imageHash && (
                        <div className="flex-shrink-0">
                          <ImageDisplay
                            hash={line.imageHash}
                            alt={`第 ${line.line} 行图片`}
                            width={150}
                            height={150}
                            className="rounded-lg border"
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">该章节暂无内容</p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
