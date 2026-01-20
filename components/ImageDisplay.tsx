"use client"

import { useState, useEffect } from "react"
import Image from "next/image"

interface ImageDisplayProps {
  hash: string | null | undefined
  alt?: string
  className?: string
  width?: number
  height?: number
}

export function ImageDisplay({ hash, alt = "", className = "", width = 200, height = 200 }: ImageDisplayProps) {
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [error, setError] = useState(false)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    if (!hash) {
      setImageUrl(null)
      return
    }

    const loadImage = async () => {
      try {
        const url = `/api/file/image/${hash}`
        setImageUrl(url)
        setError(false)
      } catch (err) {
        if (retryCount < 3) {
          setRetryCount((prev) => prev + 1)
          setTimeout(() => loadImage(), 1000 * (retryCount + 1))
        } else {
          setError(true)
        }
      }
    }

    loadImage()
  }, [hash, retryCount])

  if (!hash) {
    return null
  }

  if (error) {
    return (
      <div
        className={`bg-muted flex items-center justify-center text-muted-foreground ${className}`}
        style={{ width, height }}
      >
        加载失败
      </div>
    )
  }

  if (!imageUrl) {
    return (
      <div
        className={`bg-muted animate-pulse flex items-center justify-center ${className}`}
        style={{ width, height }}
      >
        加载中...
      </div>
    )
  }

  return (
    <img
      src={imageUrl}
      alt={alt}
      className={className}
      width={width}
      height={height}
      style={{ objectFit: "cover" }}
      onError={() => {
        if (retryCount < 3) {
          setRetryCount((prev) => prev + 1)
          setTimeout(() => {
            setImageUrl(`/api/file/image/${hash}?retry=${retryCount + 1}`)
          }, 1000 * (retryCount + 1))
        } else {
          setError(true)
        }
      }}
    />
  )
}
