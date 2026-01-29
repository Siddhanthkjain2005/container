import type { Metadata, Viewport } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "MiniContainer | Enterprise Container Management",
  description: "Professional container orchestration and monitoring dashboard with real-time metrics, analytics, and resource management.",
}

export const viewport: Viewport = {
  themeColor: "#050810",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen">{children}</body>
    </html>
  )
}
