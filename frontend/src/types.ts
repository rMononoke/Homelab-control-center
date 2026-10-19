export interface HostStats {
  cpu_percent: number;
  memory_percent: number;
  memory_used_gb: number;
  memory_total_gb: number;
  disk_percent: number;
  disk_free_gb: number;
  disk_total_gb: number;
  uptime_seconds: number;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  action: string;
  target: string;
  status: string;
  triggered_by: string;
  details: string | null;
}

export interface ContainerInfo {
  id: string;
  short_id: string;
  name: string;
  status: string;
  image: string;
  state: string;
}
