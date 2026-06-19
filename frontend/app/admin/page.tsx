'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { uploadXml, getImports, getImportStatus, getStats } from '@/lib/api'
import type { ImportLog, Stats } from '@/types'
import Header from '@/components/Header'
import { UploadCloud, RefreshCw, CheckCircle, XCircle, Clock, FileText, BarChart3, DollarSign } from 'lucide-react'
import { formatDate } from '@/lib/utils'

export default function AdminPage() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadProgressMap, setUploadProgressMap] = useState<Record<string, number>>({})
  const [activeImports, setActiveImports] = useState<Map<number, ImportLog>>(new Map())
  const [imports, setImports] = useState<ImportLog[]>([])
  const [importsLoading, setImportsLoading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)
  const pollingRef = useRef<NodeJS.Timeout | null>(null)

  const loadImports = useCallback(async () => {
    setImportsLoading(true)
    try {
      const data = await getImports()
      setImports(data)
    } catch {
      // silently ignore
    } finally {
      setImportsLoading(false)
    }
  }, [])

  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    try {
      const data = await getStats()
      setStats(data)
    } catch {
      // silently ignore
    } finally {
      setStatsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadImports()
    loadStats()
  }, [loadImports, loadStats])

  // Polling статуса активных импортов
  useEffect(() => {
    if (activeImports.size === 0) return
    
    const poll = async () => {
      Array.from(activeImports.keys()).forEach(async (importId) => {
        try {
          const status = await getImportStatus(importId)
          setActiveImports(prev => new Map(prev).set(importId, status))
          
          if (status.status === 'completed' || status.status === 'error') {
            setActiveImports(prev => {
              const newMap = new Map(prev)
              newMap.delete(importId)
              return newMap
            })
            loadImports()
            loadStats()
          }
        } catch {
          // ignore
        }
      })
    }
    
    pollingRef.current = setInterval(poll, 3000)
    poll()
    
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [activeImports, loadImports, loadStats])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const validFiles = acceptedFiles.filter(f => {
      const name = f.name.toLowerCase()
      return name.endsWith('.xml') || name.endsWith('.zip')
    })
    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles])
      setUploadError(null)
    }
    if (validFiles.length !== acceptedFiles.length) {
      setUploadError('Неподдерживаемый формат. Допустимы только .xml и .zip')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: false,
  })

  const handleUpload = async () => {
    if (files.length === 0) return
    setUploading(true)
    setUploadProgress(0)
    setUploadError(null)

    try {
      const uploadedIds: number[] = []
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const res = await uploadXml(file, (pct) => {
          setUploadProgressMap(prev => ({ ...prev, [file.name]: pct }))
          const total = Object.values({ ...uploadProgressMap, [file.name]: pct }).reduce((a, b) => a + b, 0)
          setUploadProgress(Math.round(total / files.length))
        })
        uploadedIds.push(res.import_id)
      }
      setFiles([])
      uploadedIds.forEach(id => {
        setActiveImports(prev => new Map(prev).set(id, { 
          id, 
          filename: '', 
          uploaded_at: new Date().toISOString(), 
          records_total: 0, 
          records_inserted: 0, 
          records_updated: 0, 
          status: 'processing', 
          error_message: null 
        }))
      })
      loadStats()
    } catch (e: any) {
      setUploadError(e?.response?.data?.detail || 'Ошибка при загрузке файла')
    } finally {
      setUploading(false)
      setUploadProgress(0)
      setUploadProgressMap({})
    }
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const statusIcon = (status: string) => {
    if (status === 'completed') return <CheckCircle className="w-4 h-4 text-green-500" />
    if (status === 'error') return <XCircle className="w-4 h-4 text-red-500" />
    return <Clock className="w-4 h-4 text-yellow-500 animate-spin" />
  }

  const statusLabel = (status: string) => {
    if (status === 'completed') return <span className="text-green-700 font-medium">Завершено</span>
    if (status === 'error') return <span className="text-red-700 font-medium">Ошибка</span>
    return <span className="text-yellow-700 font-medium">Обрабатывается...</span>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Администрирование</h1>

        {/* Статистика */}
        {stats && (
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Всего в реестре</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total_entities.toLocaleString('ru-RU')}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <BarChart3 className="w-6 h-6 text-blue-600" />
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">ИП</p>
                  <p className="text-3xl font-bold text-blue-600">{stats.total_ip.toLocaleString('ru-RU')}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-xl font-bold text-blue-600">ИП</span>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Юрлица</p>
                  <p className="text-3xl font-bold text-purple-600">{stats.total_org.toLocaleString('ru-RU')}</p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-xl font-bold text-purple-600">ЮЛ</span>
                </div>
              </div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Записей о налогах</p>
                  <p className="text-3xl font-bold text-amber-600">{stats.total_tax_records.toLocaleString('ru-RU')}</p>
                </div>
                <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <DollarSign className="w-6 h-6 text-amber-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Загрузка файлов */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-blue-600" />
            Загрузка XML файлов реестра МСП
          </h2>

          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
              ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50'}`}
          >
            <input {...getInputProps()} />
            <UploadCloud className={`w-12 h-12 mx-auto mb-3 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />
            {isDragActive ? (
              <p className="text-blue-600 font-medium">Отпустите файлы для загрузки</p>
            ) : (
              <>
                <p className="text-gray-600 font-medium mb-1">Перетащите XML или ZIP файлы или кликните для выбора</p>
                <p className="text-sm text-gray-400">Поддерживаются файлы реестра МСП ФНС России (*.xml) и ZIP-архивы с ними. Можно загружать несколько файлов одновременно</p>
              </>
            )}
          </div>

          {files.length > 0 && (
            <div className="mt-4 space-y-2">
              {files.map((file, idx) => (
                <div key={`${file.name}-${idx}`} className="flex items-center justify-between bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
                  <div className="flex items-center gap-2 text-sm text-blue-800 min-w-0">
                    <FileText className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate font-medium">{file.name}</span>
                    <span className="text-blue-500 flex-shrink-0">({(file.size / 1024 / 1024).toFixed(1)} МБ)</span>
                  </div>
                  <button
                    onClick={() => removeFile(idx)}
                    disabled={uploading}
                    className="ml-4 px-3 py-1 rounded text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 disabled:opacity-50 flex-shrink-0"
                  >
                    ✕
                  </button>
                </div>
              ))}
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full px-5 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? `Загрузка... ${uploadProgress}%` : `Загрузить ${files.length} файл${files.length > 1 ? 'ов' : ''}`}
              </button>
            </div>
          )}

          {uploading && (
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Передача файлов...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-200"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {uploadError && (
            <div className="mt-4 flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
              <XCircle className="w-4 h-4 flex-shrink-0" />
              {uploadError}
            </div>
          )}

          {activeImports.size > 0 && (
            <div className="mt-4 space-y-2">
              {Array.from(activeImports.values()).map((imp) => (
                <div key={imp.id} className={`rounded-lg px-4 py-3 text-sm border ${
                  imp.status === 'completed' ? 'bg-green-50 border-green-200 text-green-800' :
                  imp.status === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
                  'bg-yellow-50 border-yellow-200 text-yellow-800'
                }`}>
                  <div className="flex items-center gap-2 font-medium mb-1">
                    {statusIcon(imp.status)}
                    {statusLabel(imp.status)}
                    <span className="text-xs opacity-75">ID: {imp.id}</span>
                  </div>
                  {imp.status === 'completed' && (
                    <p>Обработано: {imp.records_total.toLocaleString('ru-RU')} записей
                      &nbsp;(вставлено: {imp.records_inserted.toLocaleString('ru-RU')},
                      &nbsp;обновлено: {imp.records_updated.toLocaleString('ru-RU')})</p>
                  )}
                  {imp.status === 'error' && imp.error_message && (
                    <p>{imp.error_message}</p>
                  )}
                  {imp.status === 'processing' && (
                    <p>Идёт импорт данных в базу. Это может занять несколько минут...</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* История загрузок */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">История загрузок</h2>
            <button
              onClick={loadImports}
              disabled={importsLoading}
              className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-blue-600 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${importsLoading ? 'animate-spin' : ''}`} />
              Обновить
            </button>
          </div>

          {imports.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-8">Загрузок ещё не было</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Файл</th>
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Тип</th>
                    <th className="text-left py-2 pr-4 text-gray-500 font-medium">Дата</th>
                    <th className="text-right py-2 pr-4 text-gray-500 font-medium">Всего</th>
                    <th className="text-right py-2 pr-4 text-gray-500 font-medium">Вставлено</th>
                    <th className="text-right py-2 pr-4 text-gray-500 font-medium">Обновлено</th>
                    <th className="text-left py-2 text-gray-500 font-medium">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {imports.map((imp) => (
                    <tr key={imp.id} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2.5 pr-4 text-gray-700 max-w-xs truncate" title={imp.filename}>
                        {imp.filename}
                      </td>
                      <td className="py-2.5 pr-4 text-gray-500">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          imp.type === 'tax' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                        }`}>
                          {imp.type === 'tax' ? 'Налоги' : 'МСП'}
                        </span>
                      </td>
                      <td className="py-2.5 pr-4 text-gray-600 whitespace-nowrap">
                        {new Date(imp.uploaded_at).toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-2.5 pr-4 text-right text-gray-700">{imp.records_total.toLocaleString('ru-RU')}</td>
                      <td className="py-2.5 pr-4 text-right text-green-700">{imp.records_inserted.toLocaleString('ru-RU')}</td>
                      <td className="py-2.5 pr-4 text-right text-blue-700">{imp.records_updated.toLocaleString('ru-RU')}</td>
                      <td className="py-2.5">
                        <div className="flex items-center gap-1.5">
                          {statusIcon(imp.status)}
                          {statusLabel(imp.status)}
                        </div>
                        {imp.status === 'error' && imp.error_message && (
                          <div className="text-xs text-red-500 mt-0.5 max-w-xs truncate" title={imp.error_message}>
                            {imp.error_message}
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
