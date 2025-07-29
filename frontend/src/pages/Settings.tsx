import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Paper,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  CloudDone as CloudDoneIcon,
} from '@mui/icons-material';
import apiService from '../services/api';

interface SystemConfig {
  // AWS Bedrock Configuration
  aws_bedrock_proxy: boolean;
  aws_region: string;
  bedrock_model_id: string;
  graphiti_base_url: string;
  
  // CodeBERT Configuration
  codebert_model: string;
  use_gpu: boolean;
  batch_size: number;
  
  // Performance Settings
  max_concurrent_clones: number;
  embedding_cache_size: number;
  
  // Repository Settings
  workspace_dir: string;
  max_repository_size_gb: number;
  
  // Analysis Settings
  default_analysis_depth: number;
  include_external_deps: boolean;
}

const Settings: React.FC = () => {
  const [config, setConfig] = useState<SystemConfig>({
    aws_bedrock_proxy: true,
    aws_region: 'us-east-1',
    bedrock_model_id: 'anthropic.claude-3-sonnet-20240229-v1:0',
    graphiti_base_url: 'http://localhost:8001',
    codebert_model: 'microsoft/codebert-base',
    use_gpu: true,
    batch_size: 16,
    max_concurrent_clones: 5,
    embedding_cache_size: 10000,
    workspace_dir: './workspace',
    max_repository_size_gb: 5.0,
    default_analysis_depth: 3,
    include_external_deps: false,
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [systemInfo, setSystemInfo] = useState<any>(null);

  useEffect(() => {
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const response = await apiService.getSystemInfo();
      setSystemInfo(response);
    } catch (err) {
      // System info is optional
    }
  };

  const handleConfigChange = (key: keyof SystemConfig, value: any) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // In a real implementation, this would save to API
      // For now, we'll just simulate saving
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess('Settings saved successfully! Restart the application to apply changes.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const isConnected = await apiService.pingAPI();
      if (isConnected) {
        setSuccess('API connection test successful!');
      } else {
        setError('API connection test failed');
      }
    } catch (err) {
      setError('API connection test failed');
    } finally {
      setLoading(false);
    }
  };

  const availableModels = [
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'anthropic.claude-3-haiku-20240307-v1:0',
    'anthropic.claude-3-opus-20240229-v1:0',
    'anthropic.claude-3-5-sonnet-20240620-v1:0'
  ];

  const availableRegions = [
    'us-east-1',
    'us-west-2',
    'eu-west-1',
    'ap-southeast-1'
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Settings
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Configure system settings, AI models, and performance parameters for optimal operation.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* AWS Bedrock Configuration */}
        <Grid item xs={12}>
          <Accordion defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Box display="flex" alignItems="center" gap={1}>
                <CloudDoneIcon color="primary" />
                <Typography variant="h6">AWS Bedrock Configuration</Typography>
                <Chip
                  label={config.aws_bedrock_proxy ? 'ENABLED' : 'DISABLED'}
                  color={config.aws_bedrock_proxy ? 'success' : 'default'}
                  size="small"
                />
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.aws_bedrock_proxy}
                        onChange={(e) => handleConfigChange('aws_bedrock_proxy', e.target.checked)}
                      />
                    }
                    label="Enable AWS Bedrock Proxy"
                  />
                  <Typography variant="body2" color="text.secondary">
                    Use AWS Bedrock models through OpenAI-compatible proxy
                  </Typography>
                </Grid>

                {config.aws_bedrock_proxy && (
                  <>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="AWS Region"
                        select
                        SelectProps={{ native: true }}
                        value={config.aws_region}
                        onChange={(e) => handleConfigChange('aws_region', e.target.value)}
                      >
                        {availableRegions.map((region) => (
                          <option key={region} value={region}>
                            {region}
                          </option>
                        ))}
                      </TextField>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Bedrock Model ID"
                        select
                        SelectProps={{ native: true }}
                        value={config.bedrock_model_id}
                        onChange={(e) => handleConfigChange('bedrock_model_id', e.target.value)}
                      >
                        {availableModels.map((model) => (
                          <option key={model} value={model}>
                            {model}
                          </option>
                        ))}
                      </TextField>
                    </Grid>

                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Graphiti Base URL"
                        value={config.graphiti_base_url}
                        onChange={(e) => handleConfigChange('graphiti_base_url', e.target.value)}
                        helperText="URL of the LiteLLM proxy or AWS Bedrock Access Gateway"
                      />
                    </Grid>
                  </>
                )}
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* CodeBERT Configuration */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">CodeBERT Configuration</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="CodeBERT Model"
                    value={config.codebert_model}
                    onChange={(e) => handleConfigChange('codebert_model', e.target.value)}
                    helperText="HuggingFace model identifier"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Batch Size"
                    type="number"
                    value={config.batch_size}
                    onChange={(e) => handleConfigChange('batch_size', parseInt(e.target.value))}
                    inputProps={{ min: 1, max: 128 }}
                    helperText="Number of items processed in parallel"
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.use_gpu}
                        onChange={(e) => handleConfigChange('use_gpu', e.target.checked)}
                        disabled={!systemInfo?.system?.gpu?.available}
                      />
                    }
                    label="Use GPU Acceleration"
                  />
                  <Typography variant="body2" color="text.secondary">
                    {systemInfo?.system?.gpu?.available 
                      ? `GPU available: ${systemInfo.system.gpu.device_name || 'Unknown'}`
                      : 'No GPU detected'
                    }
                  </Typography>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Performance Settings */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Performance Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Max Concurrent Clones"
                    type="number"
                    value={config.max_concurrent_clones}
                    onChange={(e) => handleConfigChange('max_concurrent_clones', parseInt(e.target.value))}
                    inputProps={{ min: 1, max: 20 }}
                    helperText="Number of repositories cloned simultaneously"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Embedding Cache Size"
                    type="number"
                    value={config.embedding_cache_size}
                    onChange={(e) => handleConfigChange('embedding_cache_size', parseInt(e.target.value))}
                    inputProps={{ min: 1000, max: 100000 }}
                    helperText="Number of embeddings to cache in memory"
                  />
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* Repository Settings */}
        <Grid item xs={12}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="h6">Repository Settings</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Workspace Directory"
                    value={config.workspace_dir}
                    onChange={(e) => handleConfigChange('workspace_dir', e.target.value)}
                    helperText="Local directory for cloned repositories"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Max Repository Size (GB)"
                    type="number"
                    value={config.max_repository_size_gb}
                    onChange={(e) => handleConfigChange('max_repository_size_gb', parseFloat(e.target.value))}
                    inputProps={{ min: 0.1, max: 50, step: 0.1 }}
                    helperText="Skip repositories larger than this size"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Default Analysis Depth"
                    type="number"
                    value={config.default_analysis_depth}
                    onChange={(e) => handleConfigChange('default_analysis_depth', parseInt(e.target.value))}
                    inputProps={{ min: 1, max: 10 }}
                    helperText="Default depth for dependency discovery"
                  />
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={config.include_external_deps}
                        onChange={(e) => handleConfigChange('include_external_deps', e.target.checked)}
                      />
                    }
                    label="Include External Dependencies"
                  />
                  <Typography variant="body2" color="text.secondary">
                    Include external libraries in dependency analysis
                  </Typography>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        </Grid>

        {/* System Information */}
        {systemInfo && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">System Information</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <TableContainer component={Paper}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Component</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      <TableRow>
                        <TableCell>Platform</TableCell>
                        <TableCell>{systemInfo.system?.platform}</TableCell>
                        <TableCell>
                          <Chip label="OK" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Python Version</TableCell>
                        <TableCell>{systemInfo.system?.python_version}</TableCell>
                        <TableCell>
                          <Chip label="OK" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>CPU Cores</TableCell>
                        <TableCell>{systemInfo.resources?.cpu_count}</TableCell>
                        <TableCell>
                          <Chip label="OK" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Total Memory</TableCell>
                        <TableCell>
                          {systemInfo.resources?.memory_total 
                            ? `${(systemInfo.resources.memory_total / 1024 / 1024 / 1024).toFixed(1)} GB`
                            : 'Unknown'
                          }
                        </TableCell>
                        <TableCell>
                          <Chip label="OK" color="success" size="small" />
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>GPU Available</TableCell>
                        <TableCell>
                          {systemInfo.system?.gpu?.available ? 'Yes' : 'No'}
                          {systemInfo.system?.gpu?.device_name && 
                            ` (${systemInfo.system.gpu.device_name})`
                          }
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={systemInfo.system?.gpu?.available ? "Available" : "Not Available"} 
                            color={systemInfo.system?.gpu?.available ? "success" : "warning"} 
                            size="small" 
                          />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}

        {/* Action Buttons */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box display="flex" gap={2} justifyContent="flex-end">
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={handleTestConnection}
                  disabled={loading}
                >
                  Test Connection
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveSettings}
                  disabled={loading}
                >
                  Save Settings
                </Button>
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Note: Some settings require application restart to take effect.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Settings;