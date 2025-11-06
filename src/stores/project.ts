import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export interface Project {
  project_id: string
  title: string
  total_lines: number
  total_chapters: number
  current_line: number
  current_chapter: number
  novel_path?: string
  project_path: string
  created_at: string
  updated_at: string
}

export const useProjectStore = defineStore('project', () => {
  // 当前选中的项目ID
  const selectedProjectId = ref<string>('')
  
  // 项目列表
  const projects = ref<Project[]>([])
  
  // 当前项目详情
  const currentProject = ref<Project | null>(null)
  
  // 计算属性：当前选中的项目
  const selectedProject = computed(() => {
    return projects.value.find(p => p.project_id === selectedProjectId.value) || null
  })
  
  // 加载项目列表
  const loadProjects = async () => {
    try {
      const data = await api.get('/project/all', {
        params: { limit: 100, offset: 0 }
      })
      projects.value = Array.isArray(data) ? data : []
      
      // 如果当前选择的项目不在列表中，清空选择
      if (selectedProjectId.value && !selectedProject.value) {
        selectedProjectId.value = ''
        currentProject.value = null
      }
      
      // 尝试恢复上次选择的项目
      if (!selectedProjectId.value && projects.value.length > 0) {
        const savedProjectId = localStorage.getItem('currentProjectId')
        if (savedProjectId && projects.value.find(p => p.project_id === savedProjectId)) {
          setSelectedProjectId(savedProjectId)
        } else {
          // 如果没有保存的项目，选中第一个
          setSelectedProjectId(projects.value[0].project_id)
        }
      }
    } catch (error) {
      console.error('加载项目列表失败:', error)
      projects.value = []
    }
  }
  
  // 设置选中的项目ID
  const setSelectedProjectId = (projectId: string) => {
    selectedProjectId.value = projectId
    if (projectId) {
      localStorage.setItem('currentProjectId', projectId)
      loadCurrentProject()
    } else {
      localStorage.removeItem('currentProjectId')
      currentProject.value = null
    }
  }
  
  // 加载当前项目详情
  const loadCurrentProject = async () => {
    if (!selectedProjectId.value) {
      currentProject.value = null
      return
    }
    
    try {
      currentProject.value = await api.get(`/project/${selectedProjectId.value}`)
    } catch (error) {
      console.error('加载项目详情失败:', error)
      currentProject.value = null
    }
  }
  
  // 初始化：从 localStorage 恢复项目ID
  const init = () => {
    const savedProjectId = localStorage.getItem('currentProjectId')
    if (savedProjectId) {
      selectedProjectId.value = savedProjectId
    }
  }
  
  return {
    selectedProjectId,
    projects,
    currentProject,
    selectedProject,
    loadProjects,
    setSelectedProjectId,
    loadCurrentProject,
    init
  }
})

