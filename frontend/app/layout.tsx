import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Реестр МСП — Поиск ИП и организаций',
  description: 'Поиск по единому реестру субъектов малого и среднего предпринимательства',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <body className="min-h-screen bg-gray-50 font-sans antialiased">
        {children}
      </body>
    </html>
  )
}
