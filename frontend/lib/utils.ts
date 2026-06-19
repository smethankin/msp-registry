import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  const [year, month, day] = dateStr.split('-')
  return `${day}.${month}.${year}`
}

export function getMspCategoryLabel(cat: number | null): string {
  const labels: Record<number, string> = {
    1: 'Микропредприятие',
    2: 'Малое предприятие',
    3: 'Среднее предприятие',
  }
  return cat ? labels[cat] ?? '—' : '—'
}

export function getMspTypeLabel(type: number | null): string {
  const labels: Record<number, string> = {
    1: 'Юридическое лицо',
    2: 'ИП',
    3: 'Крестьянское (фермерское) хозяйство',
  }
  return type ? labels[type] ?? '—' : '—'
}
