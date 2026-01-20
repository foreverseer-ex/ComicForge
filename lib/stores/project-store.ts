import { create } from "zustand"
import { persist } from "zustand/middleware"

export interface Project {
  id: string
  title: string
  novelPath?: string | null
  projectPath: string
  totalLines: number
  totalChapters: number
  currentLine: number
  currentChapter: number
  createdAt: string
  updatedAt: string
}

interface ProjectState {
  currentProjectId: string | null
  projects: Project[]
  setCurrentProject: (projectId: string | null) => void
  setProjects: (projects: Project[]) => void
  addProject: (project: Project) => void
  updateProject: (project: Project) => void
  removeProject: (projectId: string) => void
  getCurrentProject: () => Project | null
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      currentProjectId: null,
      projects: [],
      setCurrentProject: (projectId) =>
        set({ currentProjectId: projectId }),
      setProjects: (projects) =>
        set({ projects }),
      addProject: (project) =>
        set((state) => ({
          projects: [...state.projects, project],
        })),
      updateProject: (project) =>
        set((state) => ({
          projects: state.projects.map((p) =>
            p.id === project.id ? project : p
          ),
        })),
      removeProject: (projectId) =>
        set((state) => ({
          projects: state.projects.filter((p) => p.id !== projectId),
          currentProjectId:
            state.currentProjectId === projectId ? null : state.currentProjectId,
        })),
      getCurrentProject: () => {
        const state = get()
        return (
          state.projects.find((p) => p.id === state.currentProjectId) || null
        )
      },
    }),
    {
      name: "project-storage",
    }
  )
)
