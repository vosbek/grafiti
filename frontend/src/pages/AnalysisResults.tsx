import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Divider,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  GetApp as GetAppIcon,
  Visibility as VisibilityIcon,
  TrendingUp as TrendingUpIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import apiService from '../services/api';
import {
  ComprehensiveAnalysisResponse,
  AnalysisFinding,
  Recommendation,
  CodeReference,
  Relationship,
} from '../types/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const AnalysisResults: React.FC = () => {
  const [analysisResults, setAnalysisResults] = useState<ComprehensiveAnalysisResponse[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<ComprehensiveAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedFinding, setSelectedFinding] = useState<AnalysisFinding | null>(null);

  useEffect(() => {
    loadAnalysisResults();
  }, []);

  const loadAnalysisResults = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Mock data - in real implementation, this would come from API
      const mockResults: ComprehensiveAnalysisResponse[] = [
        {
          success: true,
          job_id: 'analysis_001',
          status: 'completed',
          analysis_id: 'comprehensive_001',
          message: 'Analysis completed successfully',
          timestamp: new Date().toISOString(),
          supervisor_summary: 'Comprehensive analysis of 15 Java repositories completed. Found 47 architectural issues, 23 security vulnerabilities, and 156 legacy code patterns requiring modernization.',
          agent_results: {
            architecture_analyzer: {
              agent_name: 'architecture_analyzer',
              status: 'completed',
              findings: [
                {
                  type: 'architecture',
                  name: 'Tight Coupling Detected',
                  description: 'High coupling between controller and DAO layers detected in payment module',
                  impact: 'high',
                  affected_components: ['PaymentController', 'PaymentDAO'],
                  recommendation: 'Introduce service layer to reduce coupling'
                },
                {
                  type: 'architecture',
                  name: 'Missing Interface Segregation',
                  description: 'Large interfaces violating Interface Segregation Principle',
                  impact: 'medium',
                  affected_components: ['UserService', 'ProductService'],
                  recommendation: 'Split large interfaces into smaller, focused ones'
                }
              ],
              execution_time: 45.2,
              confidence_score: 0.89
            },
            security_analyzer: {
              agent_name: 'security_analyzer',
              status: 'completed',
              findings: [
                {
                  type: 'security',
                  name: 'SQL Injection Vulnerability',
                  description: 'Potential SQL injection in user authentication module',
                  impact: 'critical',
                  affected_components: ['UserDAO.authenticate'],
                  recommendation: 'Use parameterized queries or ORM'
                },
                {
                  type: 'security',
                  name: 'Weak Session Management',
                  description: 'Session IDs not regenerated after authentication',
                  impact: 'high',
                  affected_components: ['SessionManager'],
                  recommendation: 'Implement session regeneration on login'
                }
              ],
              execution_time: 38.7,
              confidence_score: 0.94
            }
          },
          synthesized_response: 'The analysis reveals significant technical debt in legacy Struts applications with critical security vulnerabilities requiring immediate attention. Migration to modern frameworks is recommended.',
          code_references: [
            {
              file: 'src/main/java/com/example/dao/UserDAO.java',
              lines: [45, 67],
              relevance_score: 0.95,
              context: 'SQL injection vulnerability in authentication method'
            }
          ],
          relationships: [
            {
              source: 'PaymentController',
              target: 'PaymentDAO',
              type: 'depends_on',
              description: 'Direct dependency causing tight coupling',
              strength: 0.8
            }
          ],
          recommendations: [
            {
              priority: 'critical',
              category: 'security',
              title: 'Immediate Security Remediation',
              description: 'Address SQL injection vulnerabilities in authentication system',
              effort_estimate: '2-3 weeks',
              risk_level: 'critical'
            },
            {
              priority: 'high',
              category: 'architecture',
              title: 'Decouple Architecture Layers',
              description: 'Introduce service layer to reduce coupling between controllers and DAOs',
              effort_estimate: '4-6 weeks',
              risk_level: 'medium'
            }
          ],
          completion_time: new Date().toISOString()
        }
      ];
      
      setAnalysisResults(mockResults);
      if (mockResults.length > 0) {
        setSelectedAnalysis(mockResults[0]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis results');
    } finally {
      setLoading(false);
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'critical': return '#f44336';
      case 'high': return '#ff9800';
      case 'medium': return '#2196f3';
      case 'low': return '#4caf50';
      default: return '#9e9e9e';
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'critical': return <ErrorIcon color="error" />;
      case 'high': return <WarningIcon color="warning" />;
      case 'medium': return <InfoIcon color="info" />;
      case 'low': return <CheckCircleIcon color="success" />;
      default: return <InfoIcon />;
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  // Prepare chart data
  const impactDistribution = selectedAnalysis ? 
    Object.values(selectedAnalysis.agent_results).reduce((acc: any[], result) => {
      result.findings.forEach(finding => {
        const existing = acc.find(item => item.name === finding.impact);
        if (existing) {
          existing.value += 1;
        } else {
          acc.push({ name: finding.impact, value: 1, color: getImpactColor(finding.impact) });
        }
      });
      return acc;
    }, []) : [];

  const agentPerformance = selectedAnalysis ?
    Object.values(selectedAnalysis.agent_results).map(result => ({
      name: result.agent_name.replace('_', ' '),
      findings: result.findings.length,
      time: result.execution_time,
      confidence: (result.confidence_score || 0) * 100
    })) : [];

  const exportResults = () => {
    if (!selectedAnalysis) return;
    
    const dataStr = JSON.stringify(selectedAnalysis, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analysis-${selectedAnalysis.analysis_id}.json`;
    link.click();
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
          Loading analysis results...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Analysis Results</Typography>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<GetAppIcon />}
            onClick={exportResults}
            disabled={!selectedAnalysis}
          >
            Export Results
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {selectedAnalysis && (
        <Grid container spacing={3}>
          {/* Analysis Overview */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Analysis Overview
                </Typography>
                <Typography variant="body1" paragraph>
                  {selectedAnalysis.supervisor_summary}
                </Typography>
                <Box display="flex" gap={2} alignItems="center">
                  <Chip
                    label={`Analysis ID: ${selectedAnalysis.analysis_id}`}
                    variant="outlined"
                    size="small"
                  />
                  <Chip
                    label={`Completed: ${new Date(selectedAnalysis.completion_time || '').toLocaleString()}`}
                    variant="outlined"
                    size="small"
                  />
                  <Chip
                    label={`${Object.keys(selectedAnalysis.agent_results).length} Agents`}
                    color="primary"
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Charts */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Finding Impact Distribution
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={impactDistribution}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {impactDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Agent Performance
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={agentPerformance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <RechartsTooltip />
                    <Bar dataKey="findings" fill="#1976d2" name="Findings" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Detailed Results Tabs */}
          <Grid item xs={12}>
            <Card>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
                  <Tab label="Findings" />
                  <Tab label="Recommendations" />
                  <Tab label="Code References" />
                  <Tab label="Relationships" />
                </Tabs>
              </Box>

              {/* Findings Tab */}
              <TabPanel value={tabValue} index={0}>
                {Object.entries(selectedAnalysis.agent_results).map(([agentName, result]) => (
                  <Accordion key={agentName}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Box display="flex" alignItems="center" gap={2} width="100%">
                        <Typography variant="h6">{agentName.replace('_', ' ').toUpperCase()}</Typography>
                        <Chip
                          label={`${result.findings.length} findings`}
                          size="small"
                          color="primary"
                        />
                        <Chip
                          label={`${result.execution_time.toFixed(1)}s`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={`${((result.confidence_score || 0) * 100).toFixed(0)}% confidence`}
                          size="small"
                          color="success"
                        />
                      </Box>
                    </AccordionSummary>
                    <AccordionDetails>
                      <List>
                        {result.findings.map((finding, index) => (
                          <ListItem
                            key={index}
                            sx={{ 
                              flexDirection: 'column', 
                              alignItems: 'flex-start',
                              border: 1,
                              borderColor: 'grey.200',
                              borderRadius: 1,
                              mb: 2,
                              p: 2
                            }}
                          >
                            <Box display="flex" alignItems="center" gap={1} mb={1} width="100%">
                              {getImpactIcon(finding.impact)}
                              <Typography variant="subtitle1" fontWeight="bold">
                                {finding.name}
                              </Typography>
                              <Chip
                                label={finding.impact.toUpperCase()}
                                size="small"
                                color={getPriorityColor(finding.impact) as any}
                              />
                              <Box flexGrow={1} />
                              <Tooltip title="View Details">
                                <IconButton
                                  size="small"
                                  onClick={() => {
                                    setSelectedFinding(finding);
                                    setDetailDialogOpen(true);
                                  }}
                                >
                                  <VisibilityIcon />
                                </IconButton>
                              </Tooltip>
                            </Box>

                            <Typography variant="body2" color="text.secondary" paragraph>
                              {finding.description}
                            </Typography>

                            {finding.affected_components.length > 0 && (
                              <Box mb={1}>
                                <Typography variant="body2" fontWeight="medium" gutterBottom>
                                  Affected Components:
                                </Typography>
                                <Box display="flex" gap={0.5} flexWrap="wrap">
                                  {finding.affected_components.map((component, idx) => (
                                    <Chip key={idx} label={component} size="small" variant="outlined" />
                                  ))}
                                </Box>
                              </Box>
                            )}

                            {finding.recommendation && (
                              <Alert severity="info" sx={{ width: '100%' }}>
                                <strong>Recommendation:</strong> {finding.recommendation}
                              </Alert>
                            )}
                          </ListItem>
                        ))}
                      </List>
                    </AccordionDetails>
                  </Accordion>
                ))}
              </TabPanel>

              {/* Recommendations Tab */}
              <TabPanel value={tabValue} index={1}>
                <List>
                  {selectedAnalysis.recommendations.map((rec, index) => (
                    <ListItem
                      key={index}
                      sx={{
                        flexDirection: 'column',
                        alignItems: 'flex-start',
                        border: 1,
                        borderColor: 'grey.200',
                        borderRadius: 1,
                        mb: 2,
                        p: 2
                      }}
                    >
                      <Box display="flex" alignItems="center" gap={1} mb={1} width="100%">
                        <Typography variant="h6">{rec.title}</Typography>
                        <Chip
                          label={rec.priority.toUpperCase()}
                          size="small"
                          color={getPriorityColor(rec.priority) as any}
                        />
                        <Chip
                          label={rec.category.toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                      
                      <Typography variant="body1" paragraph>
                        {rec.description}
                      </Typography>
                      
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            <strong>Effort Estimate:</strong> {rec.effort_estimate}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            <strong>Risk Level:</strong> {rec.risk_level}
                          </Typography>
                        </Grid>
                      </Grid>
                    </ListItem>
                  ))}
                </List>
              </TabPanel>

              {/* Code References Tab */}
              <TabPanel value={tabValue} index={2}>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>File</TableCell>
                        <TableCell>Lines</TableCell>
                        <TableCell>Relevance</TableCell>
                        <TableCell>Context</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedAnalysis.code_references.map((ref, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                              {ref.file}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            {ref.lines?.join(', ') || 'N/A'}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={`${(ref.relevance_score * 100).toFixed(0)}%`}
                              size="small"
                              color={ref.relevance_score > 0.8 ? 'success' : 'default'}
                            />
                          </TableCell>
                          <TableCell>{ref.context}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              {/* Relationships Tab */}
              <TabPanel value={tabValue} index={3}>
                <TableContainer component={Paper}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Source</TableCell>
                        <TableCell>Relationship</TableCell>
                        <TableCell>Target</TableCell>
                        <TableCell>Strength</TableCell>
                        <TableCell>Description</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {selectedAnalysis.relationships.map((rel, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Chip label={rel.source} size="small" />
                          </TableCell>
                          <TableCell>
                            <Chip label={rel.type} size="small" color="primary" />
                          </TableCell>
                          <TableCell>
                            <Chip label={rel.target} size="small" />
                          </TableCell>
                          <TableCell>
                            <LinearProgress
                              variant="determinate"
                              value={(rel.strength || 0) * 100}
                              sx={{ width: 60 }}
                            />
                          </TableCell>
                          <TableCell>{rel.description}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Finding Detail Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedFinding?.name}
        </DialogTitle>
        <DialogContent>
          {selectedFinding && (
            <Box>
              <Box display="flex" gap={1} mb={2}>
                <Chip
                  label={selectedFinding.impact.toUpperCase()}
                  color={getPriorityColor(selectedFinding.impact) as any}
                />
                <Chip
                  label={selectedFinding.type.toUpperCase()}
                  variant="outlined"
                />
              </Box>
              
              <Typography variant="body1" paragraph>
                {selectedFinding.description}
              </Typography>
              
              {selectedFinding.affected_components.length > 0 && (
                <Box mb={2}>
                  <Typography variant="h6" gutterBottom>
                    Affected Components
                  </Typography>
                  <Box display="flex" gap={0.5} flexWrap="wrap">
                    {selectedFinding.affected_components.map((component, idx) => (
                      <Chip key={idx} label={component} variant="outlined" />
                    ))}
                  </Box>
                </Box>
              )}
              
              {selectedFinding.recommendation && (
                <Alert severity="info">
                  <Typography variant="h6" gutterBottom>
                    Recommendation
                  </Typography>
                  <Typography variant="body1">
                    {selectedFinding.recommendation}
                  </Typography>
                </Alert>
              )}
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default AnalysisResults;