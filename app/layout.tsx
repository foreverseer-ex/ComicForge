import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthGuard } from "@/components/AuthGuard";
import { MainContent } from "@/components/MainContent";

export const metadata: Metadata = {
  title: "ComicForge",
  description: "AI 驱动的漫画创作与可视化工具",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen">
        <ThemeProvider>
          <AuthGuard>
            <Sidebar />
            <MainContent>
              {children}
            </MainContent>
          </AuthGuard>
        </ThemeProvider>
      </body>
    </html>
  );
}
