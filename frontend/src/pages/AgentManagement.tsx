import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  ListItemText,
  Alert,
  LinearProgress,
  List,
  ListItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  ExpandMore as ExpandMoreIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
  Assessment as AssessmentIcon,
} from '@mui/icons-material';
import apiService from '../services/api';
import {
  AgentInfo,
  AgentExecutionRequest,
  AgentExecutionResponse,
  AgentResult,
  AnalysisFinding,
} from '../types/api';

interface RunningJob {
  jobId: string;
  agentName: string;
  status: string;
  startTime: Date;
}

const AgentManagement: React.FC = () => {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executeDialogOpen, setExecuteDialogOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentInfo | null>(null);
  const [runningJobs, setRunningJobs] = useState<RunningJob[]>([]);
  const [completedResults, setCompletedResults] = useState<Record<string, AgentResult>>({});

  // Execution form state
  const [selectedRepositories, setSelectedRepositories] = useState<string[]>([]);
  const [executionParameters, setExecutionParameters] = useState<string>('{}');

  // Get repositories from API
  const [availableRepositories, setAvailableRepositories] = useState<string[]>([]);

  useEffect(() => {
    loadAgents();
    loadRepositories();
    
    // Refresh data every 30 seconds
    const interval = setInterval(() => {
      loadAgents();
      updateRunningJobs();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadRepositories = async () => {
    try {
      const response = await apiService.getRepositories();
      const repoNames = response.repositories.map(repo => repo.name);
      setAvailableRepositories(repoNames);
    } catch (err) {
      console.error('Failed to load repositories:', err);
      // Fallback to empty array if repositories can't be loaded
      setAvailableRepositories([]);
    }
  };

  useEffect(() => {
    // Poll running jobs more frequently
    if (runningJobs.length > 0) {
      const jobInterval = setInterval(updateRunningJobs, 5000);
      return () => clearInterval(jobInterval);
    }
  }, [runningJobs]);

  const loadAgents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiService.getAgents();
      setAgents(response.agents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  };

  const updateRunningJobs = async () => {
    const updatedJobs = await Promise.all(
      runningJobs.map(async (job) => {
        try {
          const status = await apiService.getAgentJobStatus(job.jobId);
          
          if (status.status === 'completed' && status.result) {
            // Move to completed results
            setCompletedResults(prev => ({
              ...prev,
              [job.jobId]: status.result!
            }));
            
            // Remove from running jobs after a delay
            setTimeout(() => {
              setRunningJobs(prev => prev.filter(j => j.jobId !== job.jobId));
            }, 10000);
          }
          
          return {
            ...job,
            status: status.status,
          };
        } catch (error) {
          return {
            ...job,
            status: 'failed',
          };
        }
      })
    );

    setRunningJobs(updatedJobs);
  };

  const handleExecuteAgent = async () => {
    if (!selectedAgent || selectedRepositories.length === 0) return;

    try {
      let parameters: Record<string, any> = {};
      try {
        parameters = JSON.parse(executionParameters);
      } catch (e) {
        setError('Invalid JSON in parameters');
        return;
      }

      const request: AgentExecutionRequest = {
        agent_name: selectedAgent.name,
        repositories: selectedRepositories,
        parameters,
        context: {
          execution_time: new Date().toISOString(),
          user_initiated: true,
        },
      };

      const response = await apiService.executeAgent(selectedAgent.name, request);
      
      // Add to running jobs
      setRunningJobs(prev => [
        ...prev,
        {
          jobId: response.job_id,
          agentName: selectedAgent.name,
          status: response.status,
          startTime: new Date(),
        },
      ]);

      setExecuteDialogOpen(false);
      setSelectedRepositories([]);
      setExecutionParameters('{}');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute agent');
    }
  };

  const cancelJob = async (jobId: string) => {
    try {
      await apiService.cancelAgentJob(jobId);
      setRunningJobs(prev => prev.filter(job => job.jobId !== jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'success';
      case 'running': return 'info';
      case 'busy': return 'warning';
      case 'error': case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const formatSuccessRate = (rate: number) => {
    return `${(rate * 100).toFixed(1)}%`;
  };

  if (loading && agents.length === 0) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
          Loading AI agents...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">AI Agent Management</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<AssessmentIcon />}
            onClick={() => window.open('/api/v1/agents/performance/metrics')}
          >
            Performance Metrics
          </Button>
          <IconButton onClick={loadAgents} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Manage and execute specialized AI agents for comprehensive Java code analysis. 
        Each agent focuses on specific aspects like architecture, security, or legacy framework detection.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Running Jobs */}
      {runningJobs.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Running Jobs ({runningJobs.length})
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Agent</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Started</TableCell>
                    <TableCell>Duration</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {runningJobs.map((job) => (
                    <TableRow key={job.jobId}>
                      <TableCell>{job.agentName}</TableCell>
                      <TableCell>
                        <Chip
                          label={job.status.toUpperCase()}
                          color={getStatusColor(job.status) as any}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{job.startTime.toLocaleTimeString()}</TableCell>
                      <TableCell>
                        {Math.floor((Date.now() - job.startTime.getTime()) / 1000)}s
                      </TableCell>
                      <TableCell>
                        {(job.status === 'started' || job.status === 'in_progress') && (
                          <IconButton size="small" onClick={() => cancelJob(job.jobId)}>
                            <StopIcon />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}

      {/* Completed Results */}
      {Object.keys(completedResults).length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Results
            </Typography>
            {Object.entries(completedResults).map(([jobId, result]) => (
              <Accordion key={jobId}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box display="flex" alignItems="center" gap={2} width="100%">
                    <Typography>{result.agent_name}</Typography>
                    <Chip
                      label={`${result.findings.length} findings`}
                      size="small"
                      color="info"
                    />
                    <Chip
                      label={`${result.execution_time.toFixed(1)}s`}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <List>
                    {result.findings.map((finding, index) => (
                      <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                        <Box display="flex" alignItems="center" gap={1} mb={1}>
                          <Typography variant="subtitle2">{finding.name}</Typography>
                          <Chip
                            label={finding.impact.toUpperCase()}
                            size="small"
                            color={getImpactColor(finding.impact) as any}
                          />
                        </Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {finding.description}
                        </Typography>
                        {finding.recommendation && (
                          <Typography variant="body2" color="primary.main">
                            💡 {finding.recommendation}
                          </Typography>
                        )}
                      </ListItem>
                    ))}
                  </List>
                </AccordionDetails>
              </Accordion>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Available Agents */}
      <Grid container spacing={3}>
        {agents.map((agent) => (
          <Grid item xs={12} md={6} lg={4} key={agent.name}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box display="flex" alignItems="center" gap={1} mb={2}>
                  <PsychologyIcon color="primary" />
                  <Typography variant="h6">{agent.name}</Typography>
                  <Chip
                    label={agent.status.toUpperCase()}
                    color={getStatusColor(agent.status) as any}
                    size="small"
                  />
                </Box>

                <Typography variant="body2" color="text.secondary" paragraph>
                  {agent.description}
                </Typography>

                <Typography variant="body2" fontWeight="medium" gutterBottom>
                  Capabilities:
                </Typography>
                <List dense>
                  {agent.capabilities.slice(0, 3).map((capability, index) => (
                    <ListItem key={index} sx={{ py: 0.5, px: 0 }}>
                      <ListItemText 
                        primary={`• ${capability}`}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                  {agent.capabilities.length > 3 && (
                    <ListItem sx={{ py: 0, px: 0 }}>
                      <ListItemText 
                        primary={`... and ${agent.capabilities.length - 3} more`}
                        primaryTypographyProps={{ variant: 'body2', fontStyle: 'italic' }}
                      />
                    </ListItem>
                  )}
                </List>

                <Box mt={2}>
                  <Typography variant="body2" color="text.secondary">
                    Supported Frameworks:
                  </Typography>
                  <Box display="flex" gap={0.5} flexWrap="wrap" mt={0.5}>
                    {agent.frameworks.map((framework) => (
                      <Chip
                        key={framework}
                        label={framework}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </Box>

                <Box mt={2} display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Success Rate: <strong>{formatSuccessRate(agent.success_rate)}</strong>
                  </Typography>
                  {agent.last_execution && (
                    <Typography variant="body2" color="text.secondary">
                      Last: {new Date(agent.last_execution).toLocaleDateString()}
                    </Typography>
                  )}
                </Box>
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  startIcon={<PlayArrowIcon />}
                  onClick={() => {
                    setSelectedAgent(agent);
                    setExecuteDialogOpen(true);
                  }}
                  disabled={agent.status !== 'available'}
                >
                  Execute
                </Button>
                <Tooltip title="View Details">
                  <IconButton size="small" onClick={() => window.open(`/api/v1/agents/${agent.name}`)}>
                    <InfoIcon />
                  </IconButton>
                </Tooltip>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Execute Agent Dialog */}
      <Dialog open={executeDialogOpen} onClose={() => setExecuteDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Execute Agent: {selectedAgent?.name}
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            {selectedAgent?.description}
          </Typography>

          <FormControl fullWidth margin="normal">
            <InputLabel>Repositories</InputLabel>
            <Select
              multiple
              value={selectedRepositories}
              onChange={(e) => setSelectedRepositories(e.target.value as string[])}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {availableRepositories.map((repo) => (
                <MenuItem key={repo} value={repo}>
                  <Checkbox checked={selectedRepositories.indexOf(repo) > -1} />
                  <ListItemText primary={repo} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            margin="normal"
            label="Parameters (JSON)"
            multiline
            rows={4}
            fullWidth
            value={executionParameters}
            onChange={(e) => setExecutionParameters(e.target.value)}
            placeholder='{"timeout": 300, "detailed_analysis": true}'
            helperText="Additional parameters for agent execution in JSON format"
          />

          {selectedAgent && (
            <Box mt={2}>
              <Typography variant="body2" fontWeight="medium" gutterBottom>
                Supported Frameworks:
              </Typography>
              <Box display="flex" gap={0.5} flexWrap="wrap">
                {selectedAgent.frameworks.map((framework) => (
                  <Chip key={framework} label={framework} size="small" variant="outlined" />
                ))}
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExecuteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleExecuteAgent}
            variant="contained"
            disabled={selectedRepositories.length === 0}
            startIcon={<PlayArrowIcon />}
          >
            Execute Agent
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentManagement;