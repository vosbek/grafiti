"""
Semantic search API routes.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from ..models.requests import SemanticSearchRequest, RelationshipSearchRequest
from ..models.responses import (
    SemanticSearchResponse, RelationshipSearchResponse, SearchResult, 
    Relationship, RelationshipPath, StatisticsResponse, Statistics
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    app_request: Request
):
    """
    Perform semantic search across the codebase using CodeBERT embeddings.
    
    Searches for code entities (classes, methods, fields) based on semantic
    similarity to the query using natural language understanding.
    """
    
    try:
        # Get services from application state
        services = getattr(app_request.app.state, 'services', {})
        
        # Validate required services
        required_services = ['codebert', 'graphiti']
        for service_name in required_services:
            if service_name not in services:
                raise HTTPException(
                    status_code=503, 
                    detail=f"Required service '{service_name}' not available"
                )
        
        codebert_service = services['codebert']
        graphiti_service = services['graphiti']
        
        start_time = datetime.now()
        
        # Extract search parameters
        filters = request.filters or {}
        options = request.options or {}
        
        max_results = options.get('max_results', 20)
        similarity_threshold = options.get('similarity_threshold', 0.7)
        include_context = options.get('include_context', False)
        
        # Generate query embedding
        if hasattr(codebert_service, 'generate_embedding'):
            query_embedding = await codebert_service.generate_embedding(request.query)
        else:
            # Fallback for incomplete implementation
            logger.warning("CodeBERT service does not have generate_embedding method")
            query_embedding = None
        
        # Perform semantic search
        search_results = []
        
        if query_embedding is not None and hasattr(codebert_service, 'semantic_search'):
            # Use actual semantic search
            raw_results = await codebert_service.semantic_search(
                query_embedding, 
                max_results=max_results,
                threshold=similarity_threshold,
                filters=filters
            )
            
            # Convert to SearchResult format
            for result in raw_results:
                search_results.append(SearchResult(
                    entity={
                        "id": result.get("id", "unknown"),
                        "type": result.get("type", "unknown"),
                        "name": result.get("name", "unknown"),
                        "signature": result.get("signature", ""),
                        "file_path": result.get("file_path", ""),
                        "line_number": result.get("line_number", 0)
                    },
                    similarity_score=result.get("similarity_score", 0.0),
                    relevance_score=result.get("relevance_score", 0.0),
                    context=result.get("context") if include_context else None,
                    highlights=result.get("highlights", [])
                ))
        else:
            # No CodeBERT service available - return empty results
            search_results = []
        
        # Apply repository filters if specified
        if 'repositories' in filters:
            allowed_repos = set(filters['repositories'])
            search_results = [
                r for r in search_results 
                if any(repo in r.entity.get('file_path', '') for repo in allowed_repos)
            ]
        
        # Apply entity type filters
        if 'entity_types' in filters:
            allowed_types = set(filters['entity_types'])
            search_results = [
                r for r in search_results 
                if r.entity.get('type') in allowed_types
            ]
        
        # Apply framework filters
        if 'frameworks' in filters:
            allowed_frameworks = set(filters['frameworks'])
            search_results = [
                r for r in search_results 
                if any(fw in r.entity.get('signature', '').lower() for fw in allowed_frameworks)
            ]
        
        # Apply complexity filters
        if 'complexity_min' in filters:
            min_complexity = filters['complexity_min']
            search_results = [
                r for r in search_results 
                if r.entity.get('complexity', 0) >= min_complexity
            ]
        
        # Sort by relevance
        search_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit results
        search_results = search_results[:max_results]
        
        # Generate suggestions based on query
        suggestions = _generate_search_suggestions(request.query, search_results)
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return SemanticSearchResponse(
            success=True,
            query=request.query,
            results=search_results,
            total_matches=len(search_results),
            execution_time=execution_time,
            suggestions=suggestions,
            message=f"Found {len(search_results)} matches for '{request.query}'"
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships", response_model=RelationshipSearchResponse)
async def relationship_search(
    request: RelationshipSearchRequest,
    app_request: Request
):
    """
    Find relationships for a specific entity using the knowledge graph.
    
    Traverses the Graphiti knowledge graph to find direct and indirect
    relationships for the specified entity.
    """
    
    try:
        # Get services
        services = getattr(app_request.app.state, 'services', {})
        
        if 'graphiti' not in services:
            raise HTTPException(status_code=503, detail="Graphiti service not available")
        
        graphiti_service = services['graphiti']
        
        # Find relationships
        relationships = {}
        dependency_graph = None
        
        if hasattr(graphiti_service, 'find_relationships'):
            # Use actual Graphiti service
            raw_relationships = await graphiti_service.find_relationships(
                entity=request.entity,
                relationship_types=request.relationship_types,
                direction=request.direction,
                max_depth=request.max_depth,
                include_indirect=request.include_indirect
            )
            
            # Categorize relationships
            for rel in raw_relationships:
                rel_type = rel.get('type', 'unknown')
                if rel_type not in relationships:
                    relationships[rel_type] = []
                
                relationships[rel_type].append(Relationship(
                    source=rel.get('source', ''),
                    target=rel.get('target', ''),
                    type=rel_type,
                    description=rel.get('description', ''),
                    strength=rel.get('strength', 0.5)
                ))
        else:
            # No Graphiti service available - return empty relationships
            relationships = {}
        
        # Generate dependency graph data for visualization
        if relationships:
            dependency_graph = _generate_dependency_graph(request.entity, relationships)
        
        return RelationshipSearchResponse(
            success=True,
            entity=request.entity,
            relationships=relationships,
            dependency_graph=dependency_graph,
            message=f"Found {sum(len(rels) for rels in relationships.values())} relationships for {request.entity}"
        )
        
    except Exception as e:
        logger.error(f"Relationship search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Partial query for suggestions"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions to return"),
    app_request: Request = None
):
    """
    Get search suggestions based on partial query.
    
    Returns suggested completions and related terms based on the knowledge graph.
    """
    
    try:
        services = getattr(app_request.app.state, 'services', {})
        
        # Generate suggestions based on query
        suggestions = []
        
        if 'graphiti' in services:
            graphiti_service = services['graphiti']
            
            # Get entity names for suggestions
            if hasattr(graphiti_service, 'get_entity_names'):
                entity_names = await graphiti_service.get_entity_names()
                
                # Filter based on query
                query_lower = query.lower()
                suggestions = [
                    name for name in entity_names 
                    if query_lower in name.lower()
                ][:limit]
        
        # If no suggestions from Graphiti, generate common programming suggestions
        if not suggestions:
            common_terms = [
                "payment processing", "user authentication", "database connection",
                "session management", "error handling", "validation logic",
                "business rules", "data access", "service layer", "controller",
                "security filter", "configuration", "logging", "exception handling"
            ]
            
            query_lower = query.lower()
            suggestions = [
                term for term in common_terms 
                if query_lower in term.lower()
            ][:limit]
        
        return {
            "suggestions": suggestions,
            "query": query,
            "count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        return {"suggestions": [], "query": query, "count": 0}


@router.get("/statistics", response_model=StatisticsResponse)
async def get_search_statistics(app_request: Request):
    """
    Get search and indexing statistics.
    
    Returns information about indexed entities, embeddings, and search performance.
    """
    
    try:
        services = getattr(app_request.app.state, 'services', {})
        
        statistics = Statistics(
            total_repositories=0,
            total_classes=0,
            total_methods=0,
            total_embeddings=0,
            analysis_jobs_completed=0
        )
        
        # Get repository statistics
        if 'repository' in services:
            repo_service = services['repository']
            if hasattr(repo_service, 'get_cloned_repositories'):
                repos = repo_service.get_cloned_repositories()
                statistics.total_repositories = len(repos)
        
        # Get CodeBERT statistics
        if 'codebert' in services:
            codebert_service = services['codebert']
            if hasattr(codebert_service, 'get_statistics'):
                codebert_stats = codebert_service.get_statistics()
                statistics.total_embeddings = codebert_stats.get('total_embeddings', 0)
        
        # Get Graphiti statistics
        if 'graphiti' in services:
            graphiti_service = services['graphiti']
            # Estimate from stored entities
            statistics.total_classes = len(getattr(graphiti_service, 'java_classes', {}))
            statistics.total_methods = len(getattr(graphiti_service, 'java_methods', {}))
        
        # Estimate completed jobs (would come from job tracking in production)
        statistics.analysis_jobs_completed = len([
            job for job in getattr(app_request.app.state, 'completed_jobs', [])
        ])
        
        return StatisticsResponse(
            success=True,
            statistics=statistics,
            last_updated=datetime.now(),
            message="Statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}")
async def get_entity_details(entity_id: str, app_request: Request):
    """
    Get detailed information about a specific entity.
    
    Returns comprehensive information including code, relationships, and analysis.
    """
    
    try:
        services = getattr(app_request.app.state, 'services', {})
        
        entity_details = {
            "id": entity_id,
            "name": "Unknown Entity",
            "type": "unknown",
            "found": False
        }
        
        # Try to find entity in Graphiti
        if 'graphiti' in services:
            graphiti_service = services['graphiti']
            
            if hasattr(graphiti_service, 'get_entity_by_id'):
                entity = await graphiti_service.get_entity_by_id(entity_id)
                if entity:
                    entity_details.update({
                        "name": entity.get("name", entity_id),
                        "type": entity.get("type", "unknown"),
                        "signature": entity.get("signature", ""),
                        "file_path": entity.get("file_path", ""),
                        "line_number": entity.get("line_number", 0),
                        "complexity": entity.get("complexity", 0),
                        "documentation": entity.get("documentation", ""),
                        "found": True
                    })
        
        if not entity_details["found"]:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
        
        return entity_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity details for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

# Mock functions removed - using real data only


def _generate_dependency_graph(entity: str, relationships: Dict[str, List[Relationship]]) -> Dict[str, Any]:
    """Generate dependency graph data for visualization."""
    
    nodes = []
    edges = []
    
    # Add central entity
    nodes.append({
        "id": entity,
        "label": entity,
        "type": "entity",
        "color": "#ff6b6b"
    })
    
    # Add related entities and connections
    for rel_type, rel_list in relationships.items():
        for rel in rel_list:
            # Add source node if not exists
            if not any(n["id"] == rel.source for n in nodes):
                nodes.append({
                    "id": rel.source,
                    "label": rel.source,
                    "type": "related",
                    "color": "#4ecdc4"
                })
            
            # Add target node if not exists
            if not any(n["id"] == rel.target for n in nodes):
                nodes.append({
                    "id": rel.target,
                    "label": rel.target,
                    "type": "related",
                    "color": "#4ecdc4"
                })
            
            # Add edge
            edges.append({
                "from": rel.source,
                "to": rel.target,
                "label": rel.type,
                "strength": rel.strength or 0.5
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "layout": "hierarchical"
    }


def _generate_search_suggestions(query: str, results: List[SearchResult]) -> List[str]:
    """Generate search suggestions based on query and results."""
    
    suggestions = []
    
    # Extract terms from successful results
    for result in results[:5]:  # Top 5 results
        # Add entity name variations
        entity_name = result.entity.get("name", "")
        if entity_name and entity_name.lower() not in query.lower():
            suggestions.append(f"{query} in {entity_name}")
        
        # Add file path suggestions
        file_path = result.entity.get("file_path", "")
        if file_path:
            package = file_path.split("/")[-2] if "/" in file_path else ""
            if package and package not in query.lower():
                suggestions.append(f"{query} in {package}")
    
    # Add common refinement suggestions
    refinements = [
        f"{query} methods",
        f"{query} classes",
        f"{query} with high complexity",
        f"{query} in controllers",
        f"{query} in services"
    ]
    
    suggestions.extend(refinements)
    
    # Remove duplicates and limit
    unique_suggestions = list(dict.fromkeys(suggestions))
    return unique_suggestions[:8]