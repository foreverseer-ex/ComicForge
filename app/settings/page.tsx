"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Switch } from "@/components/ui/switch"
import { ThemeToggle } from "@/components/ThemeToggle"
import { Settings, Bug, Eye, EyeOff } from "lucide-react"
import { useSettingsStore } from "@/lib/stores/settings-store"
import { usePrivacyStore } from "@/lib/stores/privacy-store"
import { apiClient } from "@/lib/api/client"

interface SettingsConfig {
  llm?: {
    provider?: string
    api_key?: string
    base_url?: string
    model?: string
    temperature?: number
    timeout?: number
    developer_mode?: boolean
  }
  draw?: {
    backend?: string
  }
  sd_forge?: {
    base_url?: string
    home?: string
    timeout?: number
    generate_timeout?: number
  }
  civitai?: {
    api_token?: string
    timeout?: number
    max_concurrency?: number
    parallel_workers?: number
    draw_timeout?: number
  }
  frontend?: {
    image_cache_size?: number
  }
  ui?: {
    ecosystem_filter?: string | null
    base_model_filter?: string | null
    privacy_mode?: boolean
  }
  ratelimit?: {
    enabled?: boolean
    global_per_minute?: number
    login_per_minute?: number
    burst?: number
  }
  controlnet?: {
    weight?: number
    resize_mode?: string
    preprocessor_resolution?: number
    guidance_start?: number
    guidance_end?: number
    control_mode?: string
    pixel_perfect?: boolean
    lowvram?: boolean
  }
}

export default function SettingsPage() {
  const { dev, setEnableAuthRedirect } = useSettingsStore()
  const { privacyMode, setPrivacyMode } = usePrivacyStore()
  const [config, setConfig] = useState<SettingsConfig>({})
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    setLoading(true)
    try {
      // TODO: 调用设置API获取配置
      // const response = await apiClient.get<SettingsConfig>("/settings")
      // if (response.success && response.data) {
      //   setConfig(response.data)
      // }
    } catch (error) {
      console.error("加载设置失败:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async (section: keyof SettingsConfig) => {
    setSaving(true)
    try {
      // TODO: 调用设置API保存配置
      // await apiClient.put("/settings", { [section]: config[section] })
    } catch (error) {
      console.error("保存设置失败:", error)
    } finally {
      setSaving(false)
    }
  }

  const updateConfig = (section: keyof SettingsConfig, key: string, value: any) => {
    setConfig((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value,
      },
    }))
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Settings className="h-8 w-8" />
          设置
        </h1>
        <p className="mt-2 text-muted-foreground">管理应用设置和配置</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* 外观设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>外观设置</CardTitle>
            <CardDescription>自定义应用的外观和主题</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>主题</Label>
                <p className="text-sm text-muted-foreground">
                  点击按钮在浅色和暗黑模式之间切换
                </p>
              </div>
              <ThemeToggle />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>隐私模式</Label>
                <p className="text-sm text-muted-foreground">
                  隐藏图片预览，适用于公共场合
                </p>
              </div>
              <Switch
                checked={privacyMode}
                onCheckedChange={setPrivacyMode}
              />
            </div>
          </CardContent>
        </Card>

        {/* LLM 设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>LLM 设置</CardTitle>
            <CardDescription>配置大语言模型 API</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="llm-provider">提供商</Label>
              <Input
                id="llm-provider"
                type="text"
                placeholder="xai, openai, ollama, anthropic, google"
                value={config.llm?.provider || ""}
                onChange={(e) => updateConfig("llm", "provider", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="llm-base-url">API 端点</Label>
              <Input
                id="llm-base-url"
                type="text"
                placeholder="https://api.x.ai/v1"
                value={config.llm?.base_url || ""}
                onChange={(e) => updateConfig("llm", "base_url", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="llm-api-key">API Key</Label>
              <Input
                id="llm-api-key"
                type="password"
                placeholder="sk-..."
                value={config.llm?.api_key || ""}
                onChange={(e) => updateConfig("llm", "api_key", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="llm-model">模型名称</Label>
              <Input
                id="llm-model"
                type="text"
                placeholder="grok-4-fast-reasoning"
                value={config.llm?.model || ""}
                onChange={(e) => updateConfig("llm", "model", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="llm-temperature">Temperature</Label>
                <Input
                  id="llm-temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  placeholder="0.7"
                  value={config.llm?.temperature || ""}
                  onChange={(e) => updateConfig("llm", "temperature", parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="llm-timeout">超时时间（秒）</Label>
                <Input
                  id="llm-timeout"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="60"
                  value={config.llm?.timeout || ""}
                  onChange={(e) => updateConfig("llm", "timeout", parseInt(e.target.value))}
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="llm-developer-mode">开发者模式</Label>
                <p className="text-sm text-muted-foreground">
                  突破模型限制，支持自定义系统提示词
                </p>
              </div>
              <Switch
                id="llm-developer-mode"
                checked={config.llm?.developer_mode || false}
                onCheckedChange={(checked) => updateConfig("llm", "developer_mode", checked)}
              />
            </div>
            <Button onClick={() => handleSave("llm")} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </CardContent>
        </Card>

        {/* 绘图设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>绘图设置</CardTitle>
            <CardDescription>配置绘图后端</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="draw-backend">后端</Label>
              <Input
                id="draw-backend"
                type="text"
                placeholder="civitai 或 sd_forge"
                value={config.draw?.backend || ""}
                onChange={(e) => updateConfig("draw", "backend", e.target.value)}
              />
            </div>
            <Button onClick={() => handleSave("draw")} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </CardContent>
        </Card>

        {/* SD-Forge 设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>SD-Forge 设置</CardTitle>
            <CardDescription>配置 Stable Diffusion WebUI</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="sd-forge-base-url">WebUI 地址</Label>
              <Input
                id="sd-forge-base-url"
                type="text"
                placeholder="http://127.0.0.1:7860"
                value={config.sd_forge?.base_url || ""}
                onChange={(e) => updateConfig("sd_forge", "base_url", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="sd-forge-home">SD-Forge 路径</Label>
              <Input
                id="sd-forge-home"
                type="text"
                placeholder="C:\\path\\to\\sd-webui-forge"
                value={config.sd_forge?.home || ""}
                onChange={(e) => updateConfig("sd_forge", "home", e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="sd-forge-timeout">超时时间（秒）</Label>
                <Input
                  id="sd-forge-timeout"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="30"
                  value={config.sd_forge?.timeout || ""}
                  onChange={(e) => updateConfig("sd_forge", "timeout", parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="sd-forge-generate-timeout">生成超时（秒）</Label>
                <Input
                  id="sd-forge-generate-timeout"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="300"
                  value={config.sd_forge?.generate_timeout || ""}
                  onChange={(e) => updateConfig("sd_forge", "generate_timeout", parseFloat(e.target.value))}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => handleSave("sd_forge")} disabled={saving}>
                {saving ? "保存中..." : "保存设置"}
              </Button>
              <Button variant="outline">测试连接</Button>
            </div>
          </CardContent>
        </Card>

        {/* Civitai 设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>Civitai 设置</CardTitle>
            <CardDescription>配置 Civitai API</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="civitai-api-token">API Token（可选）</Label>
              <Input
                id="civitai-api-token"
                type="password"
                placeholder="optional-token"
                value={config.civitai?.api_token || ""}
                onChange={(e) => updateConfig("civitai", "api_token", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="civitai-timeout">超时时间（秒）</Label>
              <Input
                id="civitai-timeout"
                type="number"
                step="1"
                min="1"
                placeholder="30"
                value={config.civitai?.timeout || ""}
                onChange={(e) => updateConfig("civitai", "timeout", parseFloat(e.target.value))}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="civitai-max-concurrency">最大并发数</Label>
                <Input
                  id="civitai-max-concurrency"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="3"
                  value={config.civitai?.max_concurrency || ""}
                  onChange={(e) => updateConfig("civitai", "max_concurrency", parseInt(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="civitai-parallel-workers">并行工作线程</Label>
                <Input
                  id="civitai-parallel-workers"
                  type="number"
                  step="1"
                  min="1"
                  placeholder="4"
                  value={config.civitai?.parallel_workers || ""}
                  onChange={(e) => updateConfig("civitai", "parallel_workers", parseInt(e.target.value))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="civitai-draw-timeout">绘图超时（秒）</Label>
              <Input
                id="civitai-draw-timeout"
                type="number"
                step="1"
                min="60"
                placeholder="600"
                value={config.civitai?.draw_timeout || ""}
                onChange={(e) => updateConfig("civitai", "draw_timeout", parseInt(e.target.value))}
              />
            </div>
            <Button onClick={() => handleSave("civitai")} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </CardContent>
        </Card>

        {/* 前端设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>前端设置</CardTitle>
            <CardDescription>配置前端行为</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="frontend-image-cache-size">图片缓存数量</Label>
              <Input
                id="frontend-image-cache-size"
                type="number"
                step="1"
                min="10"
                max="1000"
                placeholder="100"
                value={config.frontend?.image_cache_size || ""}
                onChange={(e) => updateConfig("frontend", "image_cache_size", parseInt(e.target.value))}
              />
              <p className="text-sm text-muted-foreground">
                范围：10-1000，默认100
              </p>
            </div>
            <Button onClick={() => handleSave("frontend")} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </CardContent>
        </Card>

        {/* UI 设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>UI 设置</CardTitle>
            <CardDescription>配置界面显示选项</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="ui-ecosystem-filter">生态系统筛选</Label>
              <Input
                id="ui-ecosystem-filter"
                type="text"
                placeholder="sdxl, pony, illustrious (留空表示不过滤)"
                value={config.ui?.ecosystem_filter || ""}
                onChange={(e) => updateConfig("ui", "ecosystem_filter", e.target.value || null)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ui-base-model-filter">基础模型筛选</Label>
              <Input
                id="ui-base-model-filter"
                type="text"
                placeholder="留空表示不过滤"
                value={config.ui?.base_model_filter || ""}
                onChange={(e) => updateConfig("ui", "base_model_filter", e.target.value || null)}
              />
            </div>
            <Button onClick={() => handleSave("ui")} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </CardContent>
        </Card>

        {/* 限流设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>限流设置</CardTitle>
            <CardDescription>配置 API 请求限流</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="ratelimit-enabled">启用限流</Label>
                <p className="text-sm text-muted-foreground">
                  启用全局和登录限流保护
                </p>
              </div>
              <Switch
                id="ratelimit-enabled"
                checked={config.ratelimit?.enabled || false}
                onCheckedChange={(checked) => updateConfig("ratelimit", "enabled", checked)}
              />
            </div>
            {config.ratelimit?.enabled && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="ratelimit-global">全局限流（每分钟）</Label>
                  <Input
                    id="ratelimit-global"
                    type="number"
                    step="1"
                    min="1"
                    placeholder="1000"
                    value={config.ratelimit?.global_per_minute || ""}
                    onChange={(e) => updateConfig("ratelimit", "global_per_minute", parseInt(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ratelimit-login">登录限流（每分钟）</Label>
                  <Input
                    id="ratelimit-login"
                    type="number"
                    step="1"
                    min="1"
                    placeholder="60"
                    value={config.ratelimit?.login_per_minute || ""}
                    onChange={(e) => updateConfig("ratelimit", "login_per_minute", parseInt(e.target.value))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="ratelimit-burst">突发请求数</Label>
                  <Input
                    id="ratelimit-burst"
                    type="number"
                    step="1"
                    min="1"
                    placeholder="200"
                    value={config.ratelimit?.burst || ""}
                    onChange={(e) => updateConfig("ratelimit", "burst", parseInt(e.target.value))}
                  />
                </div>
              </>
            )}
            <Button onClick={() => handleSave("ratelimit")} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </CardContent>
        </Card>

        {/* ControlNet 配置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle>ControlNet 配置</CardTitle>
            <CardDescription>配置 ControlNet 默认参数</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="controlnet-weight">权重</Label>
              <Input
                id="controlnet-weight"
                type="number"
                step="0.1"
                min="0"
                max="2"
                placeholder="1.0"
                value={config.controlnet?.weight || ""}
                onChange={(e) => updateConfig("controlnet", "weight", parseFloat(e.target.value))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="controlnet-resize-mode">缩放模式</Label>
              <Input
                id="controlnet-resize-mode"
                type="text"
                placeholder="Just Resize, Crop and Resize, Resize and Fill"
                value={config.controlnet?.resize_mode || ""}
                onChange={(e) => updateConfig("controlnet", "resize_mode", e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="controlnet-preprocessor-resolution">预处理分辨率</Label>
              <Input
                id="controlnet-preprocessor-resolution"
                type="number"
                step="64"
                min="64"
                placeholder="512"
                value={config.controlnet?.preprocessor_resolution || ""}
                onChange={(e) => updateConfig("controlnet", "preprocessor_resolution", parseInt(e.target.value))}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="controlnet-guidance-start">引导开始步数</Label>
                <Input
                  id="controlnet-guidance-start"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  placeholder="0.0"
                  value={config.controlnet?.guidance_start || ""}
                  onChange={(e) => updateConfig("controlnet", "guidance_start", parseFloat(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="controlnet-guidance-end">引导结束步数</Label>
                <Input
                  id="controlnet-guidance-end"
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  placeholder="1.0"
                  value={config.controlnet?.guidance_end || ""}
                  onChange={(e) => updateConfig("controlnet", "guidance_end", parseFloat(e.target.value))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="controlnet-control-mode">控制模式</Label>
              <Input
                id="controlnet-control-mode"
                type="text"
                placeholder="Balanced, My prompt is more important, ControlNet is more important"
                value={config.controlnet?.control_mode || ""}
                onChange={(e) => updateConfig("controlnet", "control_mode", e.target.value)}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="controlnet-pixel-perfect">像素完美</Label>
                <p className="text-sm text-muted-foreground">
                  启用像素完美模式
                </p>
              </div>
              <Switch
                id="controlnet-pixel-perfect"
                checked={config.controlnet?.pixel_perfect || false}
                onCheckedChange={(checked) => updateConfig("controlnet", "pixel_perfect", checked)}
              />
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="controlnet-lowvram">低显存模式</Label>
                <p className="text-sm text-muted-foreground">
                  启用低显存模式以节省显存
                </p>
              </div>
              <Switch
                id="controlnet-lowvram"
                checked={config.controlnet?.lowvram || false}
                onCheckedChange={(checked) => updateConfig("controlnet", "lowvram", checked)}
              />
            </div>
            <Button onClick={() => handleSave("controlnet")} disabled={saving}>
              {saving ? "保存中..." : "保存设置"}
            </Button>
          </CardContent>
        </Card>

        {/* 调试设置 */}
        <Card interactive={false}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bug className="h-5 w-5" />
              调试设置
            </CardTitle>
            <CardDescription>开发调试相关配置</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="auth-redirect">未登录强制跳转</Label>
                <p className="text-sm text-muted-foreground">
                  启用后，未登录用户访问受保护页面时将自动跳转到登录页
                </p>
              </div>
              <Switch
                id="auth-redirect"
                checked={dev.enableAuthRedirect}
                onCheckedChange={setEnableAuthRedirect}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
