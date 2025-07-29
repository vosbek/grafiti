import React, { useEffect, useRef } from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';
// @ts-ignore
import { Network } from 'vis-network';
// @ts-ignore
import { DataSet } from 'vis-data';
import { Relationship } from '../types/api';

interface NetworkGraphProps {
  relationships: Relationship[];
  title?: string;
  height?: number;
}

const NetworkGraph: React.FC<NetworkGraphProps> = ({ 
  relationships, 
  title = "Code Relationship Graph",
  height = 400 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  useEffect(() => {
    if (!containerRef.current || relationships.length === 0) return;

    // Extract unique nodes from relationships
    const nodeMap = new Map<string, any>();
    
    relationships.forEach(rel => {
      if (!nodeMap.has(rel.source)) {
        nodeMap.set(rel.source, {
          id: rel.source,
          label: rel.source,
          color: getNodeColor(rel.source),
          font: { size: 12 }
        });
      }
      
      if (!nodeMap.has(rel.target)) {
        nodeMap.set(rel.target, {
          id: rel.target,
          label: rel.target,
          color: getNodeColor(rel.target),
          font: { size: 12 }
        });
      }
    });

    // Create nodes and edges datasets
    const nodes = new DataSet(Array.from(nodeMap.values()));
    const edges = new DataSet(
      relationships.map((rel, index) => ({
        id: index,
        from: rel.source,
        to: rel.target,
        label: rel.type,
        color: getEdgeColor(rel.type),
        width: Math.max(1, (rel.strength || 0.5) * 5),
        arrows: { to: { enabled: true, scaleFactor: 0.5 } },
        font: { size: 10, align: 'middle' }
      }))
    );

    // Network options
    const options = {
      layout: {
        improvedLayout: true,
        hierarchical: {
          enabled: false,
          direction: 'UD',
          sortMethod: 'directed'
        }
      },
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -8000,
          centralGravity: 0.3,
          springLength: 95,
          springConstant: 0.04,
          damping: 0.09,
          avoidOverlap: 0.1
        },
        stabilization: {
          enabled: true,
          iterations: 100,
          updateInterval: 25
        }
      },
      nodes: {
        shape: 'box',
        margin: { top: 10, right: 10, bottom: 10, left: 10 },
        widthConstraint: {
          maximum: 150
        },
        heightConstraint: {
          minimum: 30
        },
        font: {
          size: 12,
          color: '#333333'
        },
        borderWidth: 2,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.1)',
          size: 5,
          x: 2,
          y: 2
        }
      },
      edges: {
        smooth: {
          enabled: true,
          type: 'dynamic',
          roundness: 0.5
        },
        font: {
          size: 10,
          color: '#666666',
          strokeWidth: 3,
          strokeColor: '#ffffff'
        }
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        selectConnectedEdges: true,
        hover: true,
        tooltipDelay: 200
      }
    };

    // Create network
    networkRef.current = new Network(
      containerRef.current,
      { nodes, edges },
      options
    );

    // Add event listeners
    networkRef.current.on('selectNode', (event) => {
      const nodeId = event.nodes[0];
      if (nodeId) {
        console.log('Selected node:', nodeId);
        // Could emit event or call callback here
      }
    });

    networkRef.current.on('selectEdge', (event) => {
      const edgeId = event.edges[0];
      if (edgeId !== undefined) {
        const edge = relationships[edgeId];
        console.log('Selected edge:', edge);
        // Could show edge details in tooltip or sidebar
      }
    });

    // Cleanup on unmount
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [relationships]);

  const getNodeColor = (nodeName: string): string => {
    // Color nodes based on their type or name patterns
    if (nodeName.includes('Controller')) return '#e3f2fd'; // Light blue
    if (nodeName.includes('Service')) return '#f3e5f5'; // Light purple
    if (nodeName.includes('DAO') || nodeName.includes('Repository')) return '#e8f5e8'; // Light green
    if (nodeName.includes('Model') || nodeName.includes('Entity')) return '#fff3e0'; // Light orange
    if (nodeName.includes('Util') || nodeName.includes('Helper')) return '#fafafa'; // Light gray
    return '#f5f5f5'; // Default light gray
  };

  const getEdgeColor = (relationshipType: string): string => {
    switch (relationshipType.toLowerCase()) {
      case 'extends': return '#4caf50'; // Green
      case 'implements': return '#2196f3'; // Blue
      case 'uses': case 'depends_on': return '#ff9800'; // Orange
      case 'calls': return '#9c27b0'; // Purple
      case 'contains': return '#f44336'; // Red
      default: return '#757575'; // Gray
    }
  };

  if (relationships.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            {title}
          </Typography>
          <Box 
            display="flex" 
            alignItems="center" 
            justifyContent="center" 
            height={height}
            bgcolor="grey.50"
            borderRadius={1}
          >
            <Typography variant="body2" color="text.secondary">
              No relationships to display
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {relationships.length} relationships
          </Typography>
        </Box>
        
        <Box
          ref={containerRef}
          height={height}
          width="100%"
          border="1px solid"
          borderColor="grey.300"
          borderRadius={1}
          bgcolor="white"
        />
        
        <Box mt={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            <strong>Legend:</strong>
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={1}>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Box width={12} height={12} bgcolor="#4caf50" borderRadius="50%" />
              <Typography variant="caption">Extends</Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Box width={12} height={12} bgcolor="#2196f3" borderRadius="50%" />
              <Typography variant="caption">Implements</Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Box width={12} height={12} bgcolor="#ff9800" borderRadius="50%" />
              <Typography variant="caption">Uses/Depends</Typography>
            </Box>
            <Box display="flex" alignItems="center" gap={0.5}>
              <Box width={12} height={12} bgcolor="#9c27b0" borderRadius="50%" />
              <Typography variant="caption">Calls</Typography>
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default NetworkGraph;