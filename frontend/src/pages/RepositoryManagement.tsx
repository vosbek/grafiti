import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  IconButton,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Analytics as AnalyticsIcon,
  GetApp as GetAppIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import apiService from '../services/api';
import {
  RepositoryInfo,
  RepositoryDiscoveryRequest,
  RepositoryCloneRequest,
  JobResponse,
} from '../types/api';

interface JobTracker {
  jobId: string;
  type: 'discovery' | 'clone';
  status: string;
  progress?: number;
  message?: string;
}

const RepositoryManagement: React.FC = () => {
  const [repositories, setRepositories] = useState<RepositoryInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [discoveryDialogOpen, setDiscoveryDialogOpen] = useState(false);
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false);
  const [activeJobs, setActiveJobs] = useState<JobTracker[]>([]);
  
  // Discovery form
  const [discoveryUrl, setDiscoveryUrl] = useState('');
  const [maxDepth, setMaxDepth] = useState(3);
  const [includeExternal, setIncludeExternal] = useState(false);
  
  // Clone form
  const [cloneUrls, setCloneUrls] = useState('');
  const [concurrentClones, setConcurrentClones] = useState(5);
  
  // Filter/pagination
  const [statusFilter, setStatusFilter] = useState('');
  const [frameworkFilter, setFrameworkFilter] = useState('');

  useEffect(() => {
    loadRepositories();
    
    // Refresh repositories every 30 seconds
    const interval = setInterval(loadRepositories, 30000);
    return () => clearInterval(interval);
  }, [statusFilter, frameworkFilter]);

  useEffect(() => {
    // Poll active jobs
    if (activeJobs.length > 0) {
      const jobInterval = setInterval(updateJobStatuses, 5000);
      return () => clearInterval(jobInterval);
    }
  }, [activeJobs]);

  const loadRepositories = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiService.getRepositories(
        statusFilter || undefined,
        frameworkFilter || undefined,
        100, // limit
        0    // offset
      );
      
      setRepositories(response.repositories);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load repositories');
    } finally {
      setLoading(false);
    }
  };

  const updateJobStatuses = async () => {
    const updatedJobs = await Promise.all(
      activeJobs.map(async (job) => {
        try {
          const status = await apiService.getJobStatus(job.jobId);
          return {
            ...job,
            status: status.status,
            message: status.message,
          };
        } catch (error) {
          return {
            ...job,
            status: 'failed',
            message: 'Failed to get job status',
          };
        }
      })
    );

    // Remove completed jobs after 10 seconds
    const activeUpdatedJobs = updatedJobs.filter((job) => {
      if (job.status === 'completed' || job.status === 'failed') {
        setTimeout(() => {
          setActiveJobs((prev) => prev.filter((j) => j.jobId !== job.jobId));
          loadRepositories(); // Refresh repository list
        }, 10000);
      }
      return true;
    });

    setActiveJobs(activeUpdatedJobs);
  };

  const handleDiscoverRepositories = async () => {
    if (!discoveryUrl.trim()) return;

    try {
      const request: RepositoryDiscoveryRequest = {
        repository_url: discoveryUrl.trim(),
        max_depth: maxDepth,
        include_external: includeExternal,
      };

      const response = await apiService.discoverRepositories(request);
      
      // Add job to tracking
      setActiveJobs((prev) => [
        ...prev,
        {
          jobId: response.job_id,
          type: 'discovery',
          status: response.status,
          message: response.message,
        },
      ]);

      setDiscoveryDialogOpen(false);
      setDiscoveryUrl('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start repository discovery');
    }
  };

  const handleCloneRepositories = async () => {
    if (!cloneUrls.trim()) return;

    try {
      const urls = cloneUrls
        .split('\n')
        .map((url) => url.trim())
        .filter((url) => url);

      const request: RepositoryCloneRequest = {
        repositories: urls.map((url) => ({ url, branch: 'main', priority: 'medium' })),
        concurrent_clones: concurrentClones,
      };

      const response = await apiService.cloneRepositories(request);
      
      // Add job to tracking
      setActiveJobs((prev) => [
        ...prev,
        {
          jobId: response.job_id,
          type: 'clone',
          status: response.status,
          message: response.message,
        },
      ]);

      setCloneDialogOpen(false);
      setCloneUrls('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start repository cloning');
    }
  };

  const cancelJob = async (jobId: string) => {
    try {
      await apiService.cancelJob(jobId);
      setActiveJobs((prev) => prev.filter((job) => job.jobId !== jobId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel job');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'in_progress': case 'started': return 'info';
      case 'failed': return 'error';
      case 'pending': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={3}>
        <Typography variant="h4">Repository Management</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="contained"
            startIcon={<SearchIcon />}
            onClick={() => setDiscoveryDialogOpen(true)}
          >
            Discover Repositories
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setCloneDialogOpen(true)}
          >
            Clone Repositories
          </Button>
          <IconButton onClick={loadRepositories} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Active Jobs */}
      {activeJobs.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Active Jobs
            </Typography>
            {activeJobs.map((job) => (
              <Box key={job.jobId} display="flex" alignItems="center" gap={2} mb={2}>
                <Chip
                  label={`${job.type.toUpperCase()}: ${job.status.toUpperCase()}`}
                  color={getStatusColor(job.status) as any}
                  size="small"
                />
                <Typography variant="body2" sx={{ flexGrow: 1 }}>
                  {job.message || job.jobId}
                </Typography>
                {(job.status === 'pending' || job.status === 'started' || job.status === 'in_progress') && (
                  <IconButton size="small" onClick={() => cancelJob(job.jobId)}>
                    <CancelIcon />
                  </IconButton>
                )}
              </Box>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Filter by Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="failed">Failed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Filter by Framework</InputLabel>
                <Select
                  value={frameworkFilter}
                  label="Filter by Framework"
                  onChange={(e) => setFrameworkFilter(e.target.value)}
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="java">Java</MenuItem>
                  <MenuItem value="struts">Struts</MenuItem>
                  <MenuItem value="spring">Spring</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Typography variant="body2" color="text.secondary">
                Total: {repositories.length} repositories
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Repository List */}
      {loading ? (
        <LinearProgress />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Repository</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Frameworks</TableCell>
                <TableCell>Statistics</TableCell>
                <TableCell>Last Analyzed</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {repositories.map((repo) => (
                <TableRow key={repo.id}>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">{repo.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {repo.url}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={repo.status.toUpperCase()}
                      color={getStatusColor(repo.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {repo.frameworks.map((framework) => (
                        <Chip key={framework} label={framework} size="small" variant="outlined" />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {repo.statistics.java_files} files, {repo.statistics.classes} classes,{' '}
                      {repo.statistics.methods} methods
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {repo.last_analyzed
                        ? new Date(repo.last_analyzed).toLocaleDateString()
                        : 'Never'}
                    </Typography>
                    {repo.analysis_duration && (
                      <Typography variant="caption" color="text.secondary">
                        ({repo.analysis_duration}s)
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="View Details">
                        <IconButton size="small">
                          <InfoIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Analyze">
                        <IconButton size="small">
                          <AnalyticsIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Export">
                        <IconButton size="small">
                          <GetAppIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Discovery Dialog */}
      <Dialog open={discoveryDialogOpen} onClose={() => setDiscoveryDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Discover Repositories</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Repository URL"
            type="url"
            fullWidth
            variant="outlined"
            value={discoveryUrl}
            onChange={(e) => setDiscoveryUrl(e.target.value)}
            placeholder="https://github.company.net/org/main-repo.git"
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Maximum Depth"
            type="number"
            fullWidth
            variant="outlined"
            value={maxDepth}
            onChange={(e) => setMaxDepth(parseInt(e.target.value) || 3)}
            inputProps={{ min: 1, max: 10 }}
            sx={{ mb: 2 }}
          />
          <Typography variant="body2" color="text.secondary">
            This will analyze build files (Maven, Gradle, Ant) to discover dependent repositories automatically.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDiscoveryDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDiscoverRepositories} variant="contained" disabled={!discoveryUrl.trim()}>
            Start Discovery
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clone Dialog */}
      <Dialog open={cloneDialogOpen} onClose={() => setCloneDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Clone Repositories</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Repository URLs"
            multiline
            rows={6}
            fullWidth
            variant="outlined"
            value={cloneUrls}
            onChange={(e) => setCloneUrls(e.target.value)}
            placeholder="https://github.company.net/org/repo1.git&#10;https://github.company.net/org/repo2.git&#10;..."
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Concurrent Clones"
            type="number"
            fullWidth
            variant="outlined"
            value={concurrentClones}
            onChange={(e) => setConcurrentClones(parseInt(e.target.value) || 5)}
            inputProps={{ min: 1, max: 20 }}
            sx={{ mb: 2 }}
          />
          <Typography variant="body2" color="text.secondary">
            Enter one repository URL per line. All repositories will be cloned concurrently for analysis.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloneDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCloneRepositories} variant="contained" disabled={!cloneUrls.trim()}>
            Start Cloning
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RepositoryManagement;