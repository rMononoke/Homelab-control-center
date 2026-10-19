import type { AuditLog, ContainerInfo, HostStats } from './types'

const API_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export async function fetchHostStats(): Promise<HostStats> {
  const res = await fetch(`${API_BASE}/v1/status`)
  if (!res.ok) {
    throw new Error(`Failed to load host stats: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchAuditLogs(limit: number = 50): Promise<AuditLog[]> {
  const res = await fetch(`${API_BASE}/v1/audit?limit=${limit}`)
  if (!res.ok) {
    throw new Error(`Failed to load audit logs: ${res.statusText}`)
  }
  return res.json()
}

export async function fetchContainers(): Promise<ContainerInfo[]> {
  const res = await fetch(`${API_BASE}/v1/containers`)
  if (!res.ok) {
    throw new Error(`Failed to load containers: ${res.statusText}`)
  }
  return res.json()
}

export async function restartContainer(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/v1/containers/${encodeURIComponent(id)}/restart?triggered_by=web_dashboard`, {
    method: 'POST',
  })
  if (!res.ok) {
    throw new Error(`Failed to restart container: ${res.statusText}`)
  }
}
