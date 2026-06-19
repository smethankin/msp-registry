import Link from 'next/link'

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-2xl font-bold text-primary-600">Реестр МСП</span>
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/"
              className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              Поиск
            </Link>
            <Link
              href="/admin"
              className="text-gray-700 hover:text-primary-600 font-medium transition-colors"
            >
              Администрирование
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}
