// API Types for CodeAnalysis MultiAgent MVP

export interface BaseResponse {
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface HealthCheckResponse extends BaseResponse {
  status: 'healthy' | 'unhealthy' | 'degraded' | 'unknown';
  services: Record<string, string>;
  system?: {
    cpu: { cpu_count: number; cpu_percent: number };
    memory: { total: number; available: number; percent: number };
    gpu: { available: boolean; device_count?: number };
  };
  metrics?: Record<string, any>;
}

export interface RepositoryInfo {
  id: string;
  name: string;
  url: string;
  local_path: string;
  status: string;
  frameworks: string[];
  statistics: {
    java_files: number;
    classes: number;
    methods: number;
    struts_actions?: number;
    corba_interfaces?: number;
  };
  last_analyzed?: string;
  analysis_duration?: number;
}

export interface RepositoryListResponse extends BaseResponse {
  repositories: RepositoryInfo[];
  total: number;
  has_more: boolean;
}

export type JobStatus = 'pending' | 'started' | 'in_progress' | 'completed' | 'failed' | 'cancelled';

export interface JobResponse extends BaseResponse {
  job_id: string;
  status: JobStatus;
  progress_url?: string;
  estimated_completion?: string;
}

export interface RepositoryDiscoveryRequest {
  repository_url: string;
  max_depth?: number;
  include_external?: boolean;
  analysis_config?: Record<string, any>;
}

export interface RepositoryDiscoveryResponse extends JobResponse {
  discovered_repositories: string[];
  dependency_graph?: Record<string, string[]>;
}

export interface RepositoryCloneRequest {
  repositories: Array<{
    url: string;
    branch?: string;
    priority?: 'low' | 'medium' | 'high';
  }>;
  concurrent_clones?: number;
  workspace_name?: string;
}

export interface RepositoryCloneResponse extends JobResponse {
  total_repositories: number;
  cloned_repositories: number;
  failed_repositories: string[];
}

export interface SemanticSearchRequest {
  query: string;
  filters?: {
    repositories?: string[];
    entity_types?: string[];
    frameworks?: string[];
    complexity_min?: number;
  };
  options?: {
    max_results?: number;
    similarity_threshold?: number;
    include_context?: boolean;
  };
}

export interface SearchResult {
  entity: {
    id: string;
    type: string;
    name: string;
    signature: string;
    file_path: string;
    line_number: number;
    complexity?: number;
  };
  similarity_score: number;
  relevance_score: number;
  context?: Record<string, any>;
  highlights: string[];
}

export interface SemanticSearchResponse extends BaseResponse {
  query: string;
  results: SearchResult[];
  total_matches: number;
  execution_time: number;
  suggestions: string[];
}

export interface AgentInfo {
  name: string;
  description: string;
  capabilities: string[];
  frameworks: string[];
  status: string;
  last_execution?: string;
  success_rate: number;
}

export interface AgentListResponse extends BaseResponse {
  agents: AgentInfo[];
}

export interface AgentExecutionRequest {
  agent_name: string;
  repositories: string[];
  parameters?: Record<string, any>;
  context?: Record<string, any>;
}

export interface AnalysisFinding {
  type: string;
  name: string;
  description: string;
  impact: 'low' | 'medium' | 'high' | 'critical';
  affected_components: string[];
  recommendation?: string;
}

export interface AgentResult {
  agent_name: string;
  status: JobStatus;
  findings: AnalysisFinding[];
  execution_time: number;
  confidence_score?: number;
}

export interface AgentExecutionResponse extends JobResponse {
  agent_name: string;
  result?: AgentResult;
}

export interface ComprehensiveAnalysisRequest {
  repositories: string[];
  analysis_type: 'full' | 'architecture' | 'legacy_frameworks' | 'business_rules' | 'migration' | 'security';
  agents?: string[];
  query: string;
  context?: Record<string, any>;
}

export interface CodeReference {
  file: string;
  lines?: number[];
  relevance_score: number;
  context: string;
}

export interface Relationship {
  source: string;
  target: string;
  type: string;
  description: string;
  strength?: number;
}

export interface Recommendation {
  priority: string;
  category: string;
  title: string;
  description: string;
  effort_estimate?: string;
  risk_level: string;
}

export interface ComprehensiveAnalysisResponse extends JobResponse {
  analysis_id: string;
  supervisor_plan?: Record<string, any>;
  supervisor_summary?: string;
  agent_results: Record<string, AgentResult>;
  synthesized_response?: string;
  code_references: CodeReference[];
  relationships: Relationship[];
  recommendations: Recommendation[];
  completion_time?: string;
}

export interface Statistics {
  total_repositories: number;
  total_classes: number;
  total_methods: number;
  total_embeddings: number;
  analysis_jobs_completed: number;
}

export interface StatisticsResponse extends BaseResponse {
  statistics: Statistics;
  last_updated: string;
}