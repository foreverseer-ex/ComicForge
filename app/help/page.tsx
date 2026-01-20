import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { HelpCircle } from "lucide-react"

export default function HelpPage() {
  const helpSections = [
    {
      title: "快速开始",
      content: "创建项目 -> 添加角色 -> 上传内容 -> 开始创作",
    },
    {
      title: "工具说明",
      content: "AI 助手提供了 39 个工具函数，可以帮助你管理项目、角色、记忆等内容。",
    },
    {
      title: "常见问题",
      content: "如果遇到问题，请查看文档或联系支持。",
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <HelpCircle className="h-8 w-8" />
          帮助文档
        </h1>
        <p className="mt-2 text-muted-foreground">
          获取使用帮助和文档
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {helpSections.map((section, index) => (
          <Card key={index}>
            <CardHeader>
              <CardTitle>{section.title}</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                {section.content}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
