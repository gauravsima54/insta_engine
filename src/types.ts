export interface Profile {
  id: string;
  first_name: string;
  last_name: string;
  full_name: string;
  username: string;
  email: string;
  bio: string;
  persona: string;
  avatar_url: string;
  local_avatar_path?: string | null;
  location: string;
  timezone: string;
  status: string;
  created_at: string;
  metadata?: {
    locale?: string;
    browser_fingerprint?: string;
    simulated_trust_score?: number;
    tags?: string[];
    [key: string]: any;
  };
}

export interface CodeFile {
  path: string;
  category: string;
  size: number;
  content: string;
}

export interface BackoffStep {
  attempt: number;
  ceiling: number;
  sample_trials: number[];
  average: number;
}

export interface BenchmarkData {
  distribution: string;
  delays: number[];
  min: number;
  max: number;
  mean: number;
  backoff_progression: BackoffStep[];
}

export interface SimulationTaskRecord {
  task_id: string;
  action_type: string;
  profile_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cooldown';
  retry_count: number;
  created_at: string;
  completed_at?: string;
  applied_delay_seconds: number;
  error_message?: string;
  metadata?: Record<string, any>;
}
