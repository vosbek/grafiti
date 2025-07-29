import axios, { AxiosInstance, AxiosResponse } from 'axios';
import {
  HealthCheckResponse,
  RepositoryListResponse,
  RepositoryDiscoveryRequest,
  RepositoryDiscoveryResponse,
  RepositoryCloneRequest,
  RepositoryCloneResponse,
  SemanticSearchRequest,
  SemanticSearchResponse,
  AgentListResponse,
  AgentExecutionRequest,
  AgentExecutionResponse,
  ComprehensiveAnalysisRequest,
  ComprehensiveAnalysisResponse,
  StatisticsResponse,
  JobResponse,
} from '../types/api';

class ApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        
        // Handle common error scenarios
        if (error.response?.status === 503) {
          throw new Error('Service temporarily unavailable. Please check if all services are running.');
        } else if (error.response?.status === 500) {
          throw new Error('Internal server error. Please check the application logs.');
        } else if (error.code === 'ECONNREFUSED') {
          throw new Error('Cannot connect to the API server. Please ensure the backend is running on http://localhost:8000');
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Health and System
  async getHealth(detailed: boolean = false): Promise<HealthCheckResponse> {
    const endpoint = detailed ? '/api/v1/health/detailed' : '/api/v1/health';
    const response: AxiosResponse<HealthCheckResponse> = await this.client.get(endpoint);
    return response.data;
  }

  async getSystemInfo(): Promise<any> {
    const response = await this.client.get('/system/info');
    return response.data;
  }

  async getStatistics(): Promise<StatisticsResponse> {
    const response: AxiosResponse<StatisticsResponse> = await this.client.get('/api/v1/search/statistics');
    return response.data;
  }

  // Repository Management
  async getRepositories(
    status?: string,
    framework?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<RepositoryListResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (framework) params.append('framework', framework);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response: AxiosResponse<RepositoryListResponse> = await this.client.get(
      `/api/v1/repositories?${params.toString()}`
    );
    return response.data;
  }

  async discoverRepositories(request: RepositoryDiscoveryRequest): Promise<RepositoryDiscoveryResponse> {
    const response: AxiosResponse<RepositoryDiscoveryResponse> = await this.client.post(
      '/api/v1/repositories/discover',
      request
    );
    return response.data;
  }

  async cloneRepositories(request: RepositoryCloneRequest): Promise<RepositoryCloneResponse> {
    const response: AxiosResponse<RepositoryCloneResponse> = await this.client.post(
      '/api/v1/repositories/clone',
      request
    );
    return response.data;
  }

  async getJobStatus(jobId: string): Promise<JobResponse> {
    const response: AxiosResponse<JobResponse> = await this.client.get(
      `/api/v1/repositories/jobs/${jobId}/status`
    );
    return response.data;
  }

  async cancelJob(jobId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.delete(`/api/v1/repositories/jobs/${jobId}`);
    return response.data;
  }

  // Semantic Search
  async semanticSearch(request: SemanticSearchRequest): Promise<SemanticSearchResponse> {
    const response: AxiosResponse<SemanticSearchResponse> = await this.client.post(
      '/api/v1/search/semantic',
      request
    );
    return response.data;
  }

  async getSearchSuggestions(query: string, limit: number = 10): Promise<{ suggestions: string[] }> {
    const response = await this.client.get(
      `/api/v1/search/suggestions?query=${encodeURIComponent(query)}&limit=${limit}`
    );
    return response.data;
  }

  // Agent Management
  async getAgents(framework?: string, capability?: string): Promise<AgentListResponse> {
    const params = new URLSearchParams();
    if (framework) params.append('framework', framework);
    if (capability) params.append('capability', capability);

    const response: AxiosResponse<AgentListResponse> = await this.client.get(
      `/api/v1/agents?${params.toString()}`
    );
    return response.data;
  }

  async getAgentDetails(agentName: string): Promise<any> {
    const response = await this.client.get(`/api/v1/agents/${agentName}`);
    return response.data;
  }

  async executeAgent(agentName: string, request: AgentExecutionRequest): Promise<AgentExecutionResponse> {
    const response: AxiosResponse<AgentExecutionResponse> = await this.client.post(
      `/api/v1/agents/${agentName}/execute`,
      request
    );
    return response.data;
  }

  async getAgentJobStatus(jobId: string): Promise<AgentExecutionResponse> {
    const response: AxiosResponse<AgentExecutionResponse> = await this.client.get(
      `/api/v1/agents/jobs/${jobId}/status`
    );
    return response.data;
  }

  async cancelAgentJob(jobId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.delete(`/api/v1/agents/jobs/${jobId}`);
    return response.data;
  }

  async executeBatchAgents(
    agents: string[],
    repositories: string[],
    parameters?: Record<string, any>
  ): Promise<{ executions: Array<{ agent_name: string; job_id: string; status_url: string }> }> {
    const response = await this.client.post('/api/v1/agents/batch-execute', {
      agents,
      repositories,
      parameters,
    });
    return response.data;
  }

  async getAgentPerformanceMetrics(): Promise<any> {
    const response = await this.client.get('/api/v1/agents/performance/metrics');
    return response.data;
  }

  // Comprehensive Analysis
  async startComprehensiveAnalysis(request: ComprehensiveAnalysisRequest): Promise<ComprehensiveAnalysisResponse> {
    const response: AxiosResponse<ComprehensiveAnalysisResponse> = await this.client.post(
      '/api/v1/analysis/comprehensive',
      request
    );
    return response.data;
  }

  async getAnalysisStatus(jobId: string): Promise<ComprehensiveAnalysisResponse> {
    const response: AxiosResponse<ComprehensiveAnalysisResponse> = await this.client.get(
      `/api/v1/analysis/jobs/${jobId}/status`
    );
    return response.data;
  }

  async getAnalysisResults(analysisId: string): Promise<ComprehensiveAnalysisResponse> {
    const response: AxiosResponse<ComprehensiveAnalysisResponse> = await this.client.get(
      `/api/v1/analysis/results/${analysisId}`
    );
    return response.data;
  }

  async cancelAnalysis(jobId: string): Promise<{ success: boolean; message: string }> {
    const response = await this.client.delete(`/api/v1/analysis/jobs/${jobId}`);
    return response.data;
  }

  // Utility methods
  async pingAPI(): Promise<boolean> {
    try {
      await this.client.get('/');
      return true;
    } catch (error) {
      return false;
    }
  }

  // Export functionality
  async exportAnalysisResults(analysisId: string, format: 'json' | 'csv' | 'pdf' = 'json'): Promise<Blob> {
    const response = await this.client.get(`/api/v1/analysis/results/${analysisId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  async exportRepositoryData(repositoryId: string, format: 'json' | 'csv' = 'json'): Promise<Blob> {
    const response = await this.client.get(`/api/v1/repositories/${repositoryId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;