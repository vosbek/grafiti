import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemText,
  Button,
} from '@mui/material';
import {
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import apiService from '../services/api';
import { HealthCheckResponse, StatisticsResponse } from '../types/api';

interface SystemMetric {
  title: string;
  value: string | number;
  icon: React.ReactElement;
  color: 'primary' | 'secondary' | 'success' | 'error' | 'warning';
}

const Dashboard: React.FC = () => {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [statistics, setStatistics] = useState<StatisticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [healthData, statsData] = await Promise.all([
        apiService.getHealth(true),
        apiService.getStatistics().catch(() => null), // Don't fail if statistics are unavailable
      ]);

      setHealth(healthData);
      setStatistics(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon color="success" />;
      case 'degraded': return <WarningIcon color="warning" />;
      case 'unhealthy': return <ErrorIcon color="error" />;
      default: return <ComputerIcon />;
    }
  };

  const systemMetrics: SystemMetric[] = health?.system ? [
    {
      title: 'CPU Cores',
      value: health.system.cpu.cpu_count,
      icon: <ComputerIcon />,
      color: 'primary',
    },
    {
      title: 'CPU Usage',
      value: `${health.system.cpu.cpu_percent}%`,
      icon: <SpeedIcon />,
      color: health.system.cpu.cpu_percent > 80 ? 'error' : 'primary',
    },
    {
      title: 'Memory Usage',
      value: `${health.system.memory.percent}%`,
      icon: <MemoryIcon />,
      color: health.system.memory.percent > 85 ? 'error' : 'primary',
    },
    {
      title: 'GPU Available',
      value: health.system.gpu.available ? 'Yes' : 'No',
      icon: <StorageIcon />,
      color: health.system.gpu.available ? 'success' : 'warning',
    },
  ] : [];

  if (loading && !health) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
          Loading dashboard data...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Dashboard
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} action={
          <Button color="inherit" size="small" onClick={loadDashboardData}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* System Status */}
        <Grid item xs={12} md={6} lg={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                {getStatusIcon(health?.status || 'unknown')}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  System Status
                </Typography>
              </Box>
              <Chip
                label={health?.status?.toUpperCase() || 'UNKNOWN'}
                color={getStatusColor(health?.status || 'unknown') as any}
                variant="filled"
                sx={{ mb: 2 }}
              />
              <Typography variant="body2" color="text.secondary">
                Last updated: {health?.timestamp ? new Date(health.timestamp).toLocaleString() : 'Never'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Services Status */}
        <Grid item xs={12} md={6} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Services Status
              </Typography>
              <List dense>
                {health?.services && Object.entries(health.services).map(([service, status]) => (
                  <ListItem key={service} sx={{ px: 0 }}>
                    <ListItemText
                      primary={service}
                      secondary={
                        <Chip
                          label={status.toUpperCase()}
                          size="small"
                          color={getStatusColor(status) as any}
                          variant="outlined"
                        />
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* System Metrics */}
        <Grid item xs={12} md={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Resources
              </Typography>
              <Grid container spacing={2}>
                {systemMetrics.map((metric, index) => (
                  <Grid item xs={6} key={index}>
                    <Box display="flex" alignItems="center" mb={1}>
                      {metric.icon}
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {metric.title}
                      </Typography>
                    </Box>
                    <Typography variant="h6" color={`${metric.color}.main`}>
                      {metric.value}
                    </Typography>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Statistics */}
        {statistics && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Analysis Statistics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Total Repositories
                    </Typography>
                    <Typography variant="h4">
                      {statistics.statistics.total_repositories}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Java Classes
                    </Typography>
                    <Typography variant="h4">
                      {statistics.statistics.total_classes.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Methods Analyzed
                    </Typography>
                    <Typography variant="h4">
                      {statistics.statistics.total_methods.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Embeddings Generated
                    </Typography>
                    <Typography variant="h4">
                      {statistics.statistics.total_embeddings.toLocaleString()}
                    </Typography>
                  </Grid>
                </Grid>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Last updated: {new Date(statistics.last_updated).toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button
                  variant="contained"
                  fullWidth
                  onClick={() => window.location.href = '/repositories'}
                >
                  Manage Repositories
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => window.location.href = '/search'}
                >
                  Semantic Search
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => window.location.href = '/agents'}
                >
                  Run AI Analysis
                </Button>
                <Button
                  variant="outlined"
                  fullWidth
                  onClick={() => window.location.href = '/analysis'}
                >
                  View Results
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* AWS Bedrock Status (if configured) */}
        {health?.services?.graphiti && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  AI Services Configuration
                </Typography>
                <Box display="flex" alignItems="center" gap={2}>
                  <Chip
                    label="Graphiti Knowledge Graph"
                    color={getStatusColor(health.services.graphiti) as any}
                    icon={getStatusIcon(health.services.graphiti)}
                  />
                  <Chip
                    label="CodeBERT Embeddings"
                    color={getStatusColor(health.services.codebert || 'unknown') as any}
                    icon={getStatusIcon(health.services.codebert || 'unknown')}
                  />
                  <Chip
                    label="Repository Service"
                    color={getStatusColor(health.services.repository || 'unknown') as any}
                    icon={getStatusIcon(health.services.repository || 'unknown')}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  All AI services are operational and ready for enterprise code analysis.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default Dashboard;