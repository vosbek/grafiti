import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
  Autocomplete,
  Divider,
  Paper,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  Class as ClassIcon,
  Functions as FunctionsIcon,
  FileCopy as FileCopyIcon,
  GetApp as GetAppIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import apiService from '../services/api';
import { SemanticSearchRequest, SemanticSearchResponse, SearchResult } from '../types/api';

const SemanticSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [executionTime, setExecutionTime] = useState<number>(0);
  const [totalMatches, setTotalMatches] = useState<number>(0);

  // Filter options
  const [selectedRepositories, setSelectedRepositories] = useState<string[]>([]);
  const [selectedEntityTypes, setSelectedEntityTypes] = useState<string[]>([]);
  const [selectedFrameworks, setSelectedFrameworks] = useState<string[]>([]);
  const [complexityMin, setComplexityMin] = useState<number>(0);
  const [maxResults, setMaxResults] = useState<number>(20);
  const [similarityThreshold, setSimilarityThreshold] = useState<number>(0.7);
  const [includeContext, setIncludeContext] = useState<boolean>(true);

  // Available options (these would typically come from API)
  const entityTypes = ['class', 'method', 'field', 'interface', 'enum'];
  const frameworks = ['java', 'struts', 'spring', 'corba', 'ejb'];
  const repositories = ['repo1', 'repo2', 'repo3']; // This would come from API

  useEffect(() => {
    // Load search suggestions as user types
    if (query.length >= 3) {
      loadSuggestions();
    }
  }, [query]);

  const loadSuggestions = async () => {
    try {
      const response = await apiService.getSearchSuggestions(query, 5);
      setSuggestions(response.suggestions);
    } catch (err) {
      // Suggestions are optional, don't show error
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);

      const searchRequest: SemanticSearchRequest = {
        query: query.trim(),
        filters: {
          repositories: selectedRepositories.length > 0 ? selectedRepositories : undefined,
          entity_types: selectedEntityTypes.length > 0 ? selectedEntityTypes : undefined,
          frameworks: selectedFrameworks.length > 0 ? selectedFrameworks : undefined,
          complexity_min: complexityMin > 0 ? complexityMin : undefined,
        },
        options: {
          max_results: maxResults,
          similarity_threshold: similarityThreshold,
          include_context: includeContext,
        },
      };

      const response = await apiService.semanticSearch(searchRequest);
      setResults(response.results);
      setExecutionTime(response.execution_time);
      setTotalMatches(response.total_matches);
      setSuggestions(response.suggestions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSearch();
    }
  };

  const getEntityIcon = (type: string) => {
    switch (type) {
      case 'class': return <ClassIcon fontSize="small" />;
      case 'method': return <FunctionsIcon fontSize="small" />;
      case 'field': return <CodeIcon fontSize="small" />;
      default: return <FileCopyIcon fontSize="small" />;
    }
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.9) return 'success';
    if (score >= 0.7) return 'info';
    if (score >= 0.5) return 'warning';
    return 'default';
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const exportResults = () => {
    const dataStr = JSON.stringify(results, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `search-results-${Date.now()}.json`;
    link.click();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Semantic Code Search
      </Typography>

      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Search your codebase using natural language. Find classes, methods, and business logic 
        using semantic understanding powered by CodeBERT.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Search Interface */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Box display="flex" gap={2} mb={2}>
                <TextField
                  fullWidth
                  label="Search Query"
                  variant="outlined"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="e.g., 'payment processing logic', 'user authentication methods', 'struts action classes'"
                  multiline
                  maxRows={3}
                />
                <Button
                  variant="contained"
                  onClick={handleSearch}
                  disabled={!query.trim() || loading}
                  startIcon={<SearchIcon />}
                  sx={{ minWidth: 120 }}
                >
                  Search
                </Button>
              </Box>

              {/* Search Suggestions */}
              {suggestions.length > 0 && (
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Suggestions:
                  </Typography>
                  <Box display="flex" gap={1} flexWrap="wrap">
                    {suggestions.map((suggestion, index) => (
                      <Chip
                        key={index}
                        label={suggestion}
                        size="small"
                        onClick={() => setQuery(suggestion)}
                        clickable
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {loading && <LinearProgress sx={{ mb: 2 }} />}

              {/* Search Results Summary */}
              {results.length > 0 && (
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Found {totalMatches} matches in {executionTime.toFixed(2)}s
                  </Typography>
                  <Box>
                    <Tooltip title="Export Results">
                      <IconButton size="small" onClick={exportResults}>
                        <GetAppIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Refresh Search">
                      <IconButton size="small" onClick={handleSearch}>
                        <RefreshIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Search Results */}
          {results.length > 0 && (
            <Box mt={3}>
              {results.map((result, index) => (
                <Card key={index} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getEntityIcon(result.entity.type)}
                        <Typography variant="h6">{result.entity.name}</Typography>
                        <Chip
                          label={result.entity.type.toUpperCase()}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                      <Box display="flex" gap={1}>
                        <Chip
                          label={`${(result.similarity_score * 100).toFixed(0)}%`}
                          size="small"
                          color={getRelevanceColor(result.similarity_score) as any}
                        />
                        <Tooltip title="Copy signature to clipboard">
                          <IconButton 
                            size="small" 
                            onClick={() => copyToClipboard(result.entity.signature)}
                          >
                            <FileCopyIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {result.entity.file_path}:{result.entity.line_number}
                    </Typography>

                    <Paper sx={{ p: 2, bgcolor: 'grey.50', mb: 2 }}>
                      <Typography variant="body2" component="pre" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                        {result.entity.signature}
                      </Typography>
                    </Paper>

                    {result.highlights.length > 0 && (
                      <Box>
                        <Typography variant="body2" fontWeight="medium" gutterBottom>
                          Highlights:
                        </Typography>
                        <List dense>
                          {result.highlights.map((highlight, idx) => (
                            <ListItem key={idx} sx={{ py: 0 }}>
                              <ListItemText 
                                primary={highlight}
                                primaryTypographyProps={{ variant: 'body2' }}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    )}

                    {result.context && includeContext && (
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                          <Typography variant="body2">View Context</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <pre style={{ fontSize: '0.8rem', overflow: 'auto' }}>
                            {JSON.stringify(result.context, null, 2)}
                          </pre>
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </Grid>

        {/* Filters */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Search Filters
              </Typography>

              <Box mb={3}>
                <Autocomplete
                  multiple
                  options={repositories}
                  value={selectedRepositories}
                  onChange={(_, newValue) => setSelectedRepositories(newValue)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Repositories"
                      size="small"
                      helperText="Filter by specific repositories"
                    />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => {
                      const { key, ...chipProps } = getTagProps({ index });
                      return <Chip key={key} label={option} size="small" {...chipProps} />;
                    })
                  }
                />
              </Box>

              <Box mb={3}>
                <Autocomplete
                  multiple
                  options={entityTypes}
                  value={selectedEntityTypes}
                  onChange={(_, newValue) => setSelectedEntityTypes(newValue)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Entity Types"
                      size="small"
                      helperText="Filter by code entity types"
                    />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => {
                      const { key, ...chipProps } = getTagProps({ index });
                      return <Chip key={key} label={option} size="small" {...chipProps} />;
                    })
                  }
                />
              </Box>

              <Box mb={3}>
                <Autocomplete
                  multiple
                  options={frameworks}
                  value={selectedFrameworks}
                  onChange={(_, newValue) => setSelectedFrameworks(newValue)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Frameworks"
                      size="small"
                      helperText="Filter by framework usage"
                    />
                  )}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => {
                      const { key, ...chipProps } = getTagProps({ index });
                      return <Chip key={key} label={option} size="small" {...chipProps} />;
                    })
                  }
                />
              </Box>

              <Divider sx={{ my: 2 }} />

              <Typography variant="body2" gutterBottom>
                Complexity Minimum: {complexityMin}
              </Typography>
              <Slider
                value={complexityMin}
                onChange={(_, newValue) => setComplexityMin(newValue as number)}
                min={0}
                max={10}
                step={0.5}
                marks
                size="small"
                sx={{ mb: 3 }}
              />

              <Typography variant="body2" gutterBottom>
                Max Results: {maxResults}
              </Typography>
              <Slider
                value={maxResults}
                onChange={(_, newValue) => setMaxResults(newValue as number)}
                min={5}
                max={100}
                step={5}
                marks={[
                  { value: 5, label: '5' },
                  { value: 20, label: '20' },
                  { value: 50, label: '50' },
                  { value: 100, label: '100' },
                ]}
                size="small"
                sx={{ mb: 3 }}
              />

              <Typography variant="body2" gutterBottom>
                Similarity Threshold: {(similarityThreshold * 100).toFixed(0)}%
              </Typography>
              <Slider
                value={similarityThreshold}
                onChange={(_, newValue) => setSimilarityThreshold(newValue as number)}
                min={0.3}
                max={1.0}
                step={0.05}
                marks={[
                  { value: 0.3, label: '30%' },
                  { value: 0.7, label: '70%' },
                  { value: 1.0, label: '100%' },
                ]}
                size="small"
                sx={{ mb: 3 }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={includeContext}
                    onChange={(e) => setIncludeContext(e.target.checked)}
                  />
                }
                label="Include Context"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SemanticSearch;