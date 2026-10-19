import React, { useEffect, useState } from 'react'
import {
  Activity,
  CheckCircle2,
  Clock,
  Cpu,
  HardDrive,
  RefreshCw,
  Server,
  Shield,
  Terminal,
  XCircle,
} from 'lucide-react'
import { fetchAuditLogs, fetchContainers, fetchHostStats } from './api'
import type { AuditLog, ContainerInfo, HostStats } from './types'

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const parts: string[] = []
  if (days > 0) parts.push(`${days}d`)
  if (hours > 0 || days > 0) parts.push(`${hours}h`)
  parts.push(`${minutes}m`)
  return parts.join(' ') || '0m'
}

function formatTimestamp(isoString: string): string {
  try {
    const date = new Date(isoString)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return isoString
  }
}

function getProgressColor(percent: number): string {
  if (percent >= 85) return 'bg-red-500'
  if (percent >= 65) return 'bg-amber-500'
  return 'bg-emerald-500'
}

export function App(): React.JSX.Element {
  const [stats, setStats] = useState<HostStats | null>(null)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [containers, setContainers] = useState<ContainerInfo[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [error, setError] = useState<string | null>(null)

  const loadData = async (isSilent: boolean = false) => {
    if (!isSilent) setIsLoading(true)
    setError(null)
    try {
      const [statsData, logsData, containersData] = await Promise.all([
        fetchHostStats(),
        fetchAuditLogs(50),
        fetchContainers().catch(() => []),
      ])
      setStats(statsData)
      setLogs(logsData)
      setContainers(containersData)
      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to update dashboard data:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      if (!isSilent) setIsLoading(false)
    }
  }

  useEffect(() => {
    loadData(false)
    // Auto refresh every 5 seconds as required
    const interval = setInterval(() => {
      loadData(true)
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const runningContainers = containers.filter((c) => c.status.toLowerCase().includes('up') || c.status.toLowerCase().includes('running')).length

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 p-4 md:p-8 flex flex-col gap-6 selection:bg-cyan-500 selection:text-white">
      {/* Top Navbar */}
      <header className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800/80 pb-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 shadow-lg shadow-cyan-500/20 text-white">
            <Server className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">Homelab Control Center</h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Live
              </span>
            </div>
            <p className="text-xs md:text-sm text-slate-400">Host telemetry & ChatOps audit dashboard</p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
          {stats && (
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span>Uptime: {formatUptime(stats.uptime_seconds)}</span>
            </div>
          )}

          <button
            onClick={() => loadData(false)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700/80 text-slate-200 text-xs md:text-sm font-medium border border-slate-700 transition active:scale-95 cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-cyan-400' : ''}`} />
            <span>Обновить</span>
          </button>
        </div>
      </header>

      {/* Error alert banner */}
      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <XCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>Ошибка синхронизации с Core API: {error}</span>
          </div>
          <button
            onClick={() => loadData(false)}
            className="text-xs underline hover:text-white transition"
          >
            Повторить
          </button>
        </div>
      )}

      {/* Top 3 Metric Cards: CPU, RAM, Disk */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CPU Card */}
        <div className="rounded-2xl bg-slate-900/90 border border-slate-800/80 p-5 shadow-xl backdrop-blur-sm transition hover:border-slate-700/80">
          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                <Cpu className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium text-slate-300">CPU Usage</span>
            </div>
            <span className="text-2xl font-bold font-mono text-white">
              {stats ? `${stats.cpu_percent}%` : '--'}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full transition-all duration-500 ${stats ? getProgressColor(stats.cpu_percent) : 'bg-slate-700'}`}
              style={{ width: `${Math.min(stats?.cpu_percent || 0, 100)}%` }}
            />
          </div>
          <div className="mt-3 flex justify-between text-xs text-slate-400">
            <span>Процессор хоста</span>
            <span>{stats?.cpu_percent && stats.cpu_percent > 80 ? 'Высокая нагрузка' : 'В норме'}</span>
          </div>
        </div>

        {/* RAM Card */}
        <div className="rounded-2xl bg-slate-900/90 border border-slate-800/80 p-5 shadow-xl backdrop-blur-sm transition hover:border-slate-700/80">
          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Activity className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium text-slate-300">RAM Memory</span>
            </div>
            <span className="text-2xl font-bold font-mono text-white">
              {stats ? `${stats.memory_percent}%` : '--'}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full transition-all duration-500 ${stats ? getProgressColor(stats.memory_percent) : 'bg-slate-700'}`}
              style={{ width: `${Math.min(stats?.memory_percent || 0, 100)}%` }}
            />
          </div>
          <div className="mt-3 flex justify-between text-xs text-slate-400">
            <span>Использовано</span>
            <span className="font-mono text-slate-300">
              {stats ? `${stats.memory_used_gb} GB / ${stats.memory_total_gb} GB` : '--'}
            </span>
          </div>
        </div>

        {/* Disk Card */}
        <div className="rounded-2xl bg-slate-900/90 border border-slate-800/80 p-5 shadow-xl backdrop-blur-sm transition hover:border-slate-700/80">
          <div className="flex items-center justify-between pb-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20">
                <HardDrive className="w-5 h-5" />
              </div>
              <span className="text-sm font-medium text-slate-300">Disk Storage</span>
            </div>
            <span className="text-2xl font-bold font-mono text-white">
              {stats ? `${stats.disk_percent}%` : '--'}
            </span>
          </div>
          <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden mt-2">
            <div
              className={`h-full transition-all duration-500 ${stats ? getProgressColor(stats.disk_percent) : 'bg-slate-700'}`}
              style={{ width: `${Math.min(stats?.disk_percent || 0, 100)}%` }}
            />
          </div>
          <div className="mt-3 flex justify-between text-xs text-slate-400">
            <span>Свободно: {stats ? `${stats.disk_free_gb} GB` : '--'}</span>
            <span className="font-mono text-slate-300">
              {stats ? `Всего: ${stats.disk_total_gb} GB` : '--'}
            </span>
          </div>
        </div>
      </section>

      {/* Containers Summary bar */}
      <section className="rounded-2xl bg-slate-900/60 border border-slate-800/80 p-4 flex flex-wrap items-center justify-between gap-3 text-xs md:text-sm">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-cyan-400" />
          <span className="font-semibold text-slate-200">Docker Контейнеры:</span>
          <span className="text-slate-400">
            Всего: <b className="text-white">{containers.length}</b>, Запущено: <b className="text-emerald-400">{runningContainers}</b>
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {containers.map((c) => (
            <span
              key={c.id}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono border ${
                c.status.toLowerCase().includes('up') || c.status.toLowerCase().includes('running')
                  ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                  : 'bg-rose-500/10 text-rose-300 border-rose-500/20'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  c.status.toLowerCase().includes('up') || c.status.toLowerCase().includes('running')
                    ? 'bg-emerald-400'
                    : 'bg-rose-400'
                }`}
              />
              {c.name}
            </span>
          ))}
        </div>
      </section>

      {/* Bottom Block: Audit Logs Table */}
      <section className="rounded-2xl bg-slate-900/90 border border-slate-800/80 shadow-2xl overflow-hidden flex flex-col flex-1">
        <div className="p-4 md:p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Shield className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-base md:text-lg font-semibold text-white">Журнал аудита действий (Audit Logs)</h2>
              <p className="text-xs text-slate-400">История выполнения команд из Telegram Bot и Web Dashboard</p>
            </div>
          </div>
          <span className="text-xs text-slate-400">
            Обновлено: {lastUpdated.toLocaleTimeString()}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs md:text-sm border-collapse">
            <thead>
              <tr className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                <th className="py-3 px-4 font-medium">Время</th>
                <th className="py-3 px-4 font-medium">Действие</th>
                <th className="py-3 px-4 font-medium">Цель</th>
                <th className="py-3 px-4 font-medium">Инициатор</th>
                <th className="py-3 px-4 font-medium">Статус</th>
                <th className="py-3 px-4 font-medium">Детали</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-sans">
                    Записей аудита пока нет. Отправьте команду в боте (например, <code>/containers</code> и перезапуск).
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">
                      {formatTimestamp(log.timestamp)}
                    </td>
                    <td className="py-3 px-4 font-medium text-cyan-300 whitespace-nowrap">
                      {log.action}
                    </td>
                    <td className="py-3 px-4 text-slate-200 whitespace-nowrap">
                      {log.target.length > 20 ? log.target.slice(0, 12) : log.target}
                    </td>
                    <td className="py-3 px-4 text-slate-300 whitespace-nowrap font-sans">
                      {log.triggered_by}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {log.status === 'success' ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-sans">
                          <CheckCircle2 className="w-3 h-3" />
                          success
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-rose-500/10 text-rose-400 border border-rose-500/20 font-sans">
                          <XCircle className="w-3 h-3" />
                          error
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-sans truncate max-w-xs">
                      {log.details || '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

export default App
