import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 text-white hover:opacity-90 active:opacity-80",
        destructive:
          "bg-gradient-to-r from-red-500 via-red-600 to-red-700 text-white hover:opacity-90 active:opacity-80",
        outline:
          "border border-input bg-gradient-to-br from-background via-background/95 to-background hover:from-accent/10 hover:via-accent/15 hover:to-accent/10 hover:text-accent-foreground",
        secondary:
          "bg-gradient-to-r from-secondary via-secondary/95 to-secondary text-secondary-foreground hover:opacity-90",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        // 蓝色：新增/操作 - 蓝色渐变
        blue:
          "bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 text-white hover:opacity-90 active:opacity-80",
        // 红色：删除/危险/警告 - 红色到橙红色渐变
        red:
          "bg-gradient-to-r from-red-500 via-red-600 to-orange-600 text-white hover:opacity-90 active:opacity-80",
        // 绿色：完成/更新 - 绿色渐变
        green:
          "bg-gradient-to-r from-green-500 via-green-600 to-emerald-600 text-white hover:opacity-90 active:opacity-80",
        // 黄色：在有3个以上按钮时使用 - 黄色到橙色渐变
        yellow:
          "bg-gradient-to-r from-yellow-500 via-yellow-600 to-orange-500 text-white hover:opacity-90 active:opacity-80",
        // 紫色：AI按钮，比如AI生成参数，任何"魔法"按钮 - 紫色到粉紫色渐变
        purple:
          "bg-gradient-to-r from-purple-500 via-purple-600 to-pink-600 text-white hover:opacity-90 active:opacity-80",
        success:
          "bg-gradient-to-r from-green-500 via-green-600 to-emerald-600 text-white hover:opacity-90 active:opacity-80",
        warning:
          "bg-gradient-to-r from-yellow-500 via-yellow-600 to-orange-500 text-white hover:opacity-90 active:opacity-80",
        info: "bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 text-white hover:opacity-90 active:opacity-80",
        accent:
          "bg-gradient-to-r from-accent via-accent/95 to-accent text-accent-foreground hover:opacity-90",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
        "icon-sm": "size-9",
        "icon-lg": "size-11",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
