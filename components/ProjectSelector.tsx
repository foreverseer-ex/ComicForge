"use client"

import { useEffect, useState } from "react"
import { useProjectStore, Project } from "@/lib/stores/project-store"
import { apiClient } from "@/lib/api/client"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Plus, ChevronDown } from "lucide-react"

export function ProjectSelector() {
  const { currentProjectId, projects, setCurrentProject, setProjects } = useProjectStore()
  const [loading, setLoading] = useState(false)
  const currentProject = projects.find((p) => p.id === currentProjectId)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get<{ projects: Project[] }>("/project")
      if (response.success && response.data) {
        setProjects(response.data.projects)
        // 如果没有当前项目，选择第一个
        if (!currentProjectId && response.data.projects.length > 0) {
          setCurrentProject(response.data.projects[0].id)
        }
      }
    } catch (error) {
      console.error("加载项目失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectProject = (projectId: string) => {
    setCurrentProject(projectId)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" className="min-w-[200px] justify-between">
          <span className="truncate">
            {currentProject ? currentProject.title : "选择项目"}
          </span>
          <ChevronDown className="h-4 w-4 ml-2" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-[200px]">
        <DropdownMenuLabel>项目列表</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {projects.map((project) => (
          <DropdownMenuItem
            key={project.id}
            onClick={() => handleSelectProject(project.id)}
            className={currentProjectId === project.id ? "bg-accent" : ""}
          >
            {project.title}
          </DropdownMenuItem>
        ))}
        {projects.length === 0 && (
          <DropdownMenuItem disabled>暂无项目</DropdownMenuItem>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
