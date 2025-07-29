"""
Graphiti Knowledge Graph Service

Manages the temporal knowledge graph for Java enterprise applications
with custom entities for Struts, CORBA, and business rule tracking.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path

from graphiti_core import Graphiti
from graphiti_core.embedder import EmbedderClient
import numpy as np

from .java_parser_service import JavaClass, JavaMethod, JavaField
from .codebert_service import CodeBERTService, CodeEmbedding

logger = logging.getLogger(__name__)


class CodeBERTEmbedder(EmbedderClient):
    """Custom Graphiti embedder using CodeBERT."""
    
    def __init__(self, codebert_service: CodeBERTService):
        self.codebert_service = codebert_service
        self.dimension = 768  # CodeBERT embedding dimension
    
    async def embed(self, text: str) -> List[float]:
        """Embed text using CodeBERT."""
        
        embedding = await self.codebert_service.generate_embedding(
            text, 
            code_type="entity_description"
        )
        return embedding.embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts using CodeBERT."""
        
        code_snippets = [(text, "entity_description", f"entity_{i}") 
                        for i, text in enumerate(texts)]
        
        embeddings = await self.codebert_service.generate_batch_embeddings(code_snippets)
        return [emb.embedding for emb in embeddings]


# Custom Entity Definitions for Java Code Analysis

class JavaClassEntity:
    """Represents a Java class, interface, or enum in the knowledge graph."""
    
    def __init__(
        self,
        name: str,
        qualified_name: str,
        package: str,
        class_type: str,
        file_path: str,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.qualified_name = qualified_name
        self.package = package
        self.class_type = class_type  # class, interface, enum
        self.file_path = file_path
        self.extends_class: Optional[str] = None
        self.implements_interfaces: List[str] = []
        self.annotations: List[str] = []
        self.is_struts_action: bool = False
        self.is_corba_servant: bool = False
        self.complexity_score: float = 0.0
        self.last_modified: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for storage."""
        
        return {
            **super().to_dict(),
            "qualified_name": self.qualified_name,
            "package": self.package,
            "class_type": self.class_type,
            "file_path": self.file_path,
            "extends_class": self.extends_class,
            "implements_interfaces": self.implements_interfaces,
            "annotations": self.annotations,
            "is_struts_action": self.is_struts_action,
            "is_corba_servant": self.is_corba_servant,
            "complexity_score": self.complexity_score,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None
        }


class JavaMethodEntity:
    """Represents a Java method in the knowledge graph."""
    
    def __init__(
        self,
        name: str,
        qualified_name: str,
        owner_class: str,
        return_type: str,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.qualified_name = qualified_name
        self.owner_class = owner_class
        self.return_type = return_type
        self.parameters: List[Dict[str, str]] = []
        self.throws_exceptions: List[str] = []
        self.annotations: List[str] = []
        self.line_number: int = 0
        self.cyclomatic_complexity: int = 0
        self.is_struts_action: bool = False
        self.is_corba_method: bool = False
        self.calls_methods: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for storage."""
        
        return {
            **super().to_dict(),
            "qualified_name": self.qualified_name,
            "owner_class": self.owner_class,
            "return_type": self.return_type,
            "parameters": self.parameters,
            "throws_exceptions": self.throws_exceptions,
            "annotations": self.annotations,
            "line_number": self.line_number,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "is_struts_action": self.is_struts_action,
            "is_corba_method": self.is_corba_method,
            "calls_methods": self.calls_methods
        }


class BusinessRuleEntity:
    """Represents a business rule extracted from code."""
    
    def __init__(
        self,
        name: str,
        description: str,
        rule_type: str,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.description = description
        self.rule_type = rule_type  # validation, calculation, workflow, constraint
        self.source_methods: List[str] = []
        self.affected_entities: List[str] = []
        self.conditions: List[str] = []
        self.actions: List[str] = []
        self.priority: str = "medium"  # low, medium, high, critical
        self.domain: str = ""  # business domain
        self.compliance_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for storage."""
        
        return {
            **super().to_dict(),
            "description": self.description,
            "rule_type": self.rule_type,
            "source_methods": self.source_methods,
            "affected_entities": self.affected_entities,
            "conditions": self.conditions,
            "actions": self.actions,
            "priority": self.priority,
            "domain": self.domain,
            "compliance_required": self.compliance_required
        }


class StrutsActionEntity:
    """Represents a Struts action mapping."""
    
    def __init__(
        self,
        name: str,
        path: str,
        action_class: str,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.path = path
        self.action_class = action_class
        self.form_bean: Optional[str] = None
        self.forwards: Dict[str, str] = {}
        self.input_page: Optional[str] = None
        self.validation_enabled: bool = False
        self.scope: str = "request"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for storage."""
        
        return {
            **super().to_dict(),
            "path": self.path,
            "action_class": self.action_class,
            "form_bean": self.form_bean,
            "forwards": self.forwards,
            "input_page": self.input_page,
            "validation_enabled": self.validation_enabled,
            "scope": self.scope
        }


class CORBAInterfaceEntity:
    """Represents a CORBA interface definition."""
    
    def __init__(
        self,
        name: str,
        module: str,
        **kwargs
    ):
        super().__init__(name=name, **kwargs)
        self.module = module
        self.operations: List[Dict[str, Any]] = []
        self.attributes: List[Dict[str, Any]] = []
        self.inherits_interfaces: List[str] = []
        self.servant_classes: List[str] = []
        self.client_classes: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for storage."""
        
        return {
            **super().to_dict(),
            "module": self.module,
            "operations": self.operations,
            "attributes": self.attributes,
            "inherits_interfaces": self.inherits_interfaces,
            "servant_classes": self.servant_classes,
            "client_classes": self.client_classes
        }


class GraphitiService:
    """Service for managing the Graphiti knowledge graph with AWS Bedrock support."""
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        codebert_service: Optional[CodeBERTService] = None,
        # LLM Configuration for Graphiti
        llm_provider: str = "openai",
        llm_model: str = "gpt-4",
        llm_api_key: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        # AWS Bedrock specific configuration
        aws_bedrock_proxy: bool = False,
        bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        aws_region: str = "us-east-1"
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.codebert_service = codebert_service
        
        # LLM Configuration
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key
        self.llm_base_url = llm_base_url
        
        # AWS Bedrock Configuration
        self.aws_bedrock_proxy = aws_bedrock_proxy
        self.bedrock_model_id = bedrock_model_id
        self.aws_region = aws_region
        
        self.graphiti: Optional[Graphiti] = None
        self.embedder: Optional[CodeBERTEmbedder] = None
        
        # Entity caches
        self.java_classes: Dict[str, JavaClassEntity] = {}
        self.java_methods: Dict[str, JavaMethodEntity] = {}
        self.business_rules: Dict[str, BusinessRuleEntity] = {}
        self.struts_actions: Dict[str, StrutsActionEntity] = {}
        self.corba_interfaces: Dict[str, CORBAInterfaceEntity] = {}
        
        # Relationship tracking
        self.class_dependencies: Dict[str, Set[str]] = {}
        self.method_calls: Dict[str, Set[str]] = {}
        
        if aws_bedrock_proxy:
            logger.info(f"Initialized Graphiti service for {uri} with AWS Bedrock proxy support")
        else:
            logger.info(f"Initialized Graphiti service for {uri} with {llm_provider}")
    
    async def initialize(self):
        """Initialize the Graphiti knowledge graph with LLM configuration."""
        
        logger.info("Initializing Graphiti knowledge graph...")
        
        try:
            # Create custom embedder if CodeBERT service is available
            if self.codebert_service:
                self.embedder = CodeBERTEmbedder(self.codebert_service)
                logger.info("Using CodeBERT embedder for Graphiti")
            
            # Prepare LLM configuration
            llm_config = self._prepare_llm_config()
            
            # Initialize Graphiti with LLM configuration
            if llm_config:
                self.graphiti = Graphiti(
                    self.uri,
                    self.user,
                    self.password,
                    embedder=self.embedder,
                    **llm_config
                )
                logger.info(f"Graphiti initialized with {self.llm_provider} LLM")
            else:
                # Fallback initialization without LLM (limited functionality)
                self.graphiti = Graphiti(
                    self.uri,
                    self.user,
                    self.password,
                    embedder=self.embedder
                )
                logger.warning("Graphiti initialized without LLM - some features may be limited")
            
            # Test connection
            if hasattr(self.graphiti, 'close'):
                await self.graphiti.close()  # Test connection and close
                
                # Reinitialize after test
                if llm_config:
                    self.graphiti = Graphiti(
                        self.uri,
                        self.user,
                        self.password,
                        embedder=self.embedder,
                        **llm_config
                    )
                else:
                    self.graphiti = Graphiti(
                        self.uri,
                        self.user,
                        self.password,
                        embedder=self.embedder
                    )
            
            logger.info("Graphiti knowledge graph initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {e}")
            # Provide specific guidance for Bedrock setup issues
            if self.aws_bedrock_proxy and "api" in str(e).lower():
                logger.error("AWS Bedrock proxy may not be running. Please ensure the proxy is started.")
                logger.error("Quick setup: pip install litellm && litellm --model bedrock/anthropic.claude-3-sonnet")
            raise
    
    def _prepare_llm_config(self) -> Optional[Dict[str, Any]]:
        """Prepare LLM configuration for Graphiti initialization."""
        
        if self.aws_bedrock_proxy:
            # Configure for AWS Bedrock through OpenAI-compatible proxy
            logger.info(f"Configuring Graphiti for AWS Bedrock model: {self.bedrock_model_id}")
            
            # If using LiteLLM proxy (recommended)
            if self.llm_base_url and "localhost" in self.llm_base_url:
                return {
                    "llm_provider": "openai",
                    "model": "bedrock/anthropic.claude-3-sonnet",  # LiteLLM format
                    "api_key": "dummy",  # LiteLLM doesn't require real API key for Bedrock
                    "base_url": self.llm_base_url
                }
            
            # If using AWS Bedrock Access Gateway
            elif self.llm_base_url:
                return {
                    "llm_provider": "openai",
                    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "api_key": self.llm_api_key or "bedrock-proxy",
                    "base_url": self.llm_base_url
                }
            
            else:
                logger.warning("AWS Bedrock proxy enabled but no base_url provided")
                return None
        
        elif self.llm_provider and self.llm_api_key:
            # Standard LLM provider configuration
            config = {
                "llm_provider": self.llm_provider,
                "model": self.llm_model,
                "api_key": self.llm_api_key
            }
            
            if self.llm_base_url:
                config["base_url"] = self.llm_base_url
            
            return config
        
        else:
            # No LLM configuration available
            logger.warning("No LLM configuration provided - Graphiti functionality will be limited")
            return None
    
    async def add_java_class(self, java_class: JavaClass) -> JavaClassEntity:
        """Add a Java class to the knowledge graph."""
        
        # Create class entity
        class_entity = JavaClassEntity(
            name=java_class.name,
            qualified_name=java_class.qualified_name,
            package=java_class.package,
            class_type=java_class.type.value,
            file_path=java_class.file_path
        )
        
        # Set additional properties
        class_entity.extends_class = java_class.extends
        class_entity.implements_interfaces = java_class.implements
        class_entity.annotations = java_class.annotations
        class_entity.is_struts_action = java_class.is_struts_action
        class_entity.is_corba_servant = java_class.is_corba_servant
        class_entity.last_modified = datetime.now()
        
        # Calculate complexity score
        class_entity.complexity_score = self._calculate_class_complexity(java_class)
        
        # Create description for embedding
        description = self._create_class_description(java_class)
        
        # Add to Graphiti
        await self.graphiti.add_entity(
            entity=class_entity,
            entity_description=description
        )
        
        # Cache locally
        self.java_classes[java_class.qualified_name] = class_entity
        
        # Add methods
        for method in java_class.methods:
            await self.add_java_method(method, java_class.qualified_name)
        
        # Create inheritance relationships
        if java_class.extends:
            await self._create_inheritance_relationship(
                java_class.qualified_name,
                java_class.extends,
                "extends"
            )
        
        for interface in java_class.implements:
            await self._create_inheritance_relationship(
                java_class.qualified_name,
                interface,
                "implements"
            )
        
        logger.debug(f"Added Java class: {java_class.qualified_name}")
        return class_entity
    
    async def add_java_method(self, method: JavaMethod, owner_class: str) -> JavaMethodEntity:
        """Add a Java method to the knowledge graph."""
        
        qualified_name = f"{owner_class}.{method.name}"
        
        # Create method entity
        method_entity = JavaMethodEntity(
            name=method.name,
            qualified_name=qualified_name,
            owner_class=owner_class,
            return_type=method.return_type
        )
        
        # Set additional properties
        method_entity.parameters = [
            {"name": p.name, "type": p.type} for p in method.parameters
        ]
        method_entity.throws_exceptions = method.throws
        method_entity.annotations = method.annotations
        method_entity.line_number = method.line_number
        method_entity.is_struts_action = method.is_struts_action
        method_entity.is_corba_method = method.is_corba_method
        method_entity.calls_methods = method.calls_methods
        
        # Calculate complexity
        method_entity.cyclomatic_complexity = self._calculate_method_complexity(method)
        
        # Create description for embedding
        description = self._create_method_description(method, owner_class)
        
        # Add to Graphiti
        await self.graphiti.add_entity(
            entity=method_entity,
            entity_description=description
        )
        
        # Cache locally
        self.java_methods[qualified_name] = method_entity
        
        # Create ownership relationship
        await self._create_ownership_relationship(qualified_name, owner_class, "method_of")
        
        # Create method call relationships
        for called_method in method.calls_methods:
            await self._create_call_relationship(qualified_name, called_method)
        
        logger.debug(f"Added Java method: {qualified_name}")
        return method_entity
    
    async def add_business_rule(
        self,
        name: str,
        description: str,
        rule_type: str,
        source_methods: List[str],
        **kwargs
    ) -> BusinessRuleEntity:
        """Add a business rule to the knowledge graph."""
        
        # Create business rule entity
        rule_entity = BusinessRuleEntity(
            name=name,
            description=description,
            rule_type=rule_type
        )
        
        # Set additional properties
        rule_entity.source_methods = source_methods
        for key, value in kwargs.items():
            if hasattr(rule_entity, key):
                setattr(rule_entity, key, value)
        
        # Add to Graphiti
        await self.graphiti.add_entity(
            entity=rule_entity,
            entity_description=description
        )
        
        # Cache locally
        self.business_rules[name] = rule_entity
        
        # Create relationships to source methods
        for method_name in source_methods:
            await self._create_rule_relationship(name, method_name, "extracted_from")
        
        logger.debug(f"Added business rule: {name}")
        return rule_entity
    
    async def add_struts_action(
        self,
        name: str,
        path: str,
        action_class: str,
        **kwargs
    ) -> StrutsActionEntity:
        """Add a Struts action mapping to the knowledge graph."""
        
        # Create Struts action entity
        action_entity = StrutsActionEntity(
            name=name,
            path=path,
            action_class=action_class
        )
        
        # Set additional properties
        for key, value in kwargs.items():
            if hasattr(action_entity, key):
                setattr(action_entity, key, value)
        
        # Create description
        description = f"Struts action mapping {path} handled by {action_class}"
        
        # Add to Graphiti
        await self.graphiti.add_entity(
            entity=action_entity,
            entity_description=description
        )
        
        # Cache locally
        self.struts_actions[path] = action_entity
        
        # Create relationship to action class
        await self._create_mapping_relationship(path, action_class, "handled_by")
        
        logger.debug(f"Added Struts action: {path}")
        return action_entity
    
    async def add_corba_interface(
        self,
        name: str,
        module: str,
        operations: List[Dict[str, Any]],
        **kwargs
    ) -> CORBAInterfaceEntity:
        """Add a CORBA interface to the knowledge graph."""
        
        # Create CORBA interface entity
        interface_entity = CORBAInterfaceEntity(
            name=name,
            module=module
        )
        
        # Set additional properties
        interface_entity.operations = operations
        for key, value in kwargs.items():
            if hasattr(interface_entity, key):
                setattr(interface_entity, key, value)
        
        # Create description
        description = f"CORBA interface {name} in module {module} with {len(operations)} operations"
        
        # Add to Graphiti
        await self.graphiti.add_entity(
            entity=interface_entity,
            entity_description=description
        )
        
        # Cache locally
        self.corba_interfaces[name] = interface_entity
        
        logger.debug(f"Added CORBA interface: {name}")
        return interface_entity
    
    async def find_related_entities(
        self,
        entity_name: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Find entities related to a given entity."""
        
        try:
            # Use Graphiti's search capabilities
            results = await self.graphiti.search(
                query=f"Find entities related to {entity_name}",
                num_results=50
            )
            
            # Group results by entity type
            related_entities = {
                "classes": [],
                "methods": [],
                "business_rules": [],
                "struts_actions": [],
                "corba_interfaces": []
            }
            
            for result in results:
                entity_data = result.get("entity", {})
                entity_type = entity_data.get("type", "unknown")
                
                if entity_type == "JavaClassEntity":
                    related_entities["classes"].append(entity_data)
                elif entity_type == "JavaMethodEntity":
                    related_entities["methods"].append(entity_data)
                elif entity_type == "BusinessRuleEntity":
                    related_entities["business_rules"].append(entity_data)
                elif entity_type == "StrutsActionEntity":
                    related_entities["struts_actions"].append(entity_data)
                elif entity_type == "CORBAInterfaceEntity":
                    related_entities["corba_interfaces"].append(entity_data)
            
            return related_entities
            
        except Exception as e:
            logger.error(f"Failed to find related entities for {entity_name}: {e}")
            return {}
    
    async def semantic_search(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        num_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Perform semantic search over the knowledge graph."""
        
        try:
            # Enhance query with entity type filters
            if entity_types:
                type_filter = " OR ".join(f"type:{etype}" for etype in entity_types)
                enhanced_query = f"{query} ({type_filter})"
            else:
                enhanced_query = query
            
            # Perform search
            results = await self.graphiti.search(
                query=enhanced_query,
                num_results=num_results
            )
            
            # Process and enrich results
            processed_results = []
            for result in results:
                entity_data = result.get("entity", {})
                score = result.get("score", 0.0)
                
                processed_result = {
                    "entity": entity_data,
                    "score": score,
                    "relevance": self._calculate_relevance_score(entity_data, query)
                }
                processed_results.append(processed_result)
            
            # Sort by relevance
            processed_results.sort(key=lambda x: x["relevance"], reverse=True)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Failed to perform semantic search: {e}")
            return []
    
    async def get_architecture_overview(self) -> Dict[str, Any]:
        """Get an overview of the system architecture."""
        
        try:
            overview = {
                "statistics": {
                    "total_classes": len(self.java_classes),
                    "total_methods": len(self.java_methods),
                    "business_rules": len(self.business_rules),
                    "struts_actions": len(self.struts_actions),
                    "corba_interfaces": len(self.corba_interfaces)
                },
                "packages": {},
                "frameworks": {
                    "struts": {"classes": 0, "actions": 0},
                    "corba": {"interfaces": 0, "servants": 0},
                    "ejb": {"beans": 0},
                    "spring": {"components": 0}
                },
                "complexity": {
                    "high_complexity_classes": [],
                    "complex_methods": [],
                    "critical_business_rules": []
                }
            }
            
            # Analyze packages
            for class_entity in self.java_classes.values():
                package = class_entity.package
                if package not in overview["packages"]:
                    overview["packages"][package] = {
                        "classes": 0,
                        "methods": 0,
                        "complexity": 0.0
                    }
                
                overview["packages"][package]["classes"] += 1
                overview["packages"][package]["complexity"] += class_entity.complexity_score
            
            # Analyze frameworks
            for class_entity in self.java_classes.values():
                if class_entity.is_struts_action:
                    overview["frameworks"]["struts"]["classes"] += 1
                
                if class_entity.is_corba_servant:
                    overview["frameworks"]["corba"]["servants"] += 1
            
            overview["frameworks"]["struts"]["actions"] = len(self.struts_actions)
            overview["frameworks"]["corba"]["interfaces"] = len(self.corba_interfaces)
            
            # Find complex entities
            complex_classes = [
                (name, entity.complexity_score)
                for name, entity in self.java_classes.items()
                if entity.complexity_score > 10.0
            ]
            complex_classes.sort(key=lambda x: x[1], reverse=True)
            overview["complexity"]["high_complexity_classes"] = complex_classes[:10]
            
            complex_methods = [
                (name, entity.cyclomatic_complexity)
                for name, entity in self.java_methods.items()
                if entity.cyclomatic_complexity > 5
            ]
            complex_methods.sort(key=lambda x: x[1], reverse=True)
            overview["complexity"]["complex_methods"] = complex_methods[:10]
            
            critical_rules = [
                (name, entity.priority)
                for name, entity in self.business_rules.items()
                if entity.priority in ["high", "critical"]
            ]
            overview["complexity"]["critical_business_rules"] = critical_rules
            
            return overview
            
        except Exception as e:
            logger.error(f"Failed to get architecture overview: {e}")
            return {}
    
    # Helper methods
    
    def _calculate_class_complexity(self, java_class: JavaClass) -> float:
        """Calculate complexity score for a Java class."""
        
        complexity = 0.0
        
        # Base complexity
        complexity += len(java_class.methods) * 0.5
        complexity += len(java_class.fields) * 0.1
        complexity += len(java_class.inner_classes) * 2.0
        
        # Inheritance complexity
        if java_class.extends:
            complexity += 1.0
        complexity += len(java_class.implements) * 0.5
        
        # Framework complexity
        if java_class.is_struts_action:
            complexity += 2.0
        if java_class.is_corba_servant:
            complexity += 3.0
        
        # Annotation complexity
        complexity += len(java_class.annotations) * 0.2
        
        return complexity
    
    def _calculate_method_complexity(self, method: JavaMethod) -> int:
        """Calculate cyclomatic complexity for a method."""
        
        # Simple heuristic based on method properties
        complexity = 1  # Base complexity
        
        # Add complexity for parameters
        complexity += len(method.parameters)
        
        # Add complexity for exceptions
        complexity += len(method.throws)
        
        # Framework-specific complexity
        if method.is_struts_action:
            complexity += 2
        if method.is_corba_method:
            complexity += 1
        
        return complexity
    
    def _create_class_description(self, java_class: JavaClass) -> str:
        """Create a natural language description of a Java class."""
        
        parts = []
        
        parts.append(f"{java_class.type.value} {java_class.name}")
        
        if java_class.package:
            parts.append(f"in package {java_class.package}")
        
        if java_class.extends:
            parts.append(f"extends {java_class.extends}")
        
        if java_class.implements:
            parts.append(f"implements {', '.join(java_class.implements)}")
        
        if java_class.is_struts_action:
            parts.append("is a Struts action class")
        
        if java_class.is_corba_servant:
            parts.append("is a CORBA servant class")
        
        parts.append(f"with {len(java_class.methods)} methods")
        parts.append(f"and {len(java_class.fields)} fields")
        
        return ". ".join(parts)
    
    def _create_method_description(self, method: JavaMethod, owner_class: str) -> str:
        """Create a natural language description of a Java method."""
        
        parts = []
        
        parts.append(f"method {method.name}")
        parts.append(f"in class {owner_class}")
        parts.append(f"returns {method.return_type}")
        
        if method.parameters:
            param_types = [p.type for p in method.parameters]
            parts.append(f"takes parameters of types: {', '.join(param_types)}")
        
        if method.is_struts_action:
            parts.append("is a Struts action method")
        
        if method.is_corba_method:
            parts.append("is a CORBA method")
        
        if method.throws:
            parts.append(f"throws {', '.join(method.throws)}")
        
        return ". ".join(parts)
    
    def _calculate_relevance_score(self, entity_data: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for search results."""
        
        score = 0.0
        query_lower = query.lower()
        
        # Check name matches
        name = entity_data.get("name", "").lower()
        if query_lower in name:
            score += 2.0
        
        # Check description matches
        description = entity_data.get("description", "").lower()
        if query_lower in description:
            score += 1.0
        
        # Boost for framework-specific queries
        if "struts" in query_lower and entity_data.get("is_struts_action"):
            score += 1.5
        
        if "corba" in query_lower and entity_data.get("is_corba_method"):
            score += 1.5
        
        return score
    
    # Relationship creation methods
    
    async def _create_inheritance_relationship(
        self,
        child: str,
        parent: str,
        relationship_type: str
    ):
        """Create inheritance relationship between classes."""
        
        try:
            await self.graphiti.add_relationship(
                source_entity_name=child,
                target_entity_name=parent,
                relationship_description=f"{child} {relationship_type} {parent}"
            )
        except Exception as e:
            logger.warning(f"Failed to create inheritance relationship: {e}")
    
    async def _create_ownership_relationship(
        self,
        child: str,
        parent: str,
        relationship_type: str
    ):
        """Create ownership relationship (method to class, etc.)."""
        
        try:
            await self.graphiti.add_relationship(
                source_entity_name=child,
                target_entity_name=parent,
                relationship_description=f"{child} is {relationship_type} {parent}"
            )
        except Exception as e:
            logger.warning(f"Failed to create ownership relationship: {e}")
    
    async def _create_call_relationship(self, caller: str, callee: str):
        """Create method call relationship."""
        
        try:
            await self.graphiti.add_relationship(
                source_entity_name=caller,
                target_entity_name=callee,
                relationship_description=f"{caller} calls {callee}"
            )
        except Exception as e:
            logger.warning(f"Failed to create call relationship: {e}")
    
    async def _create_rule_relationship(
        self,
        rule_name: str,
        method_name: str,
        relationship_type: str
    ):
        """Create business rule relationship."""
        
        try:
            await self.graphiti.add_relationship(
                source_entity_name=rule_name,
                target_entity_name=method_name,
                relationship_description=f"Business rule {rule_name} is {relationship_type} {method_name}"
            )
        except Exception as e:
            logger.warning(f"Failed to create rule relationship: {e}")
    
    async def _create_mapping_relationship(
        self,
        mapping: str,
        target: str,
        relationship_type: str
    ):
        """Create Struts action mapping relationship."""
        
        try:
            await self.graphiti.add_relationship(
                source_entity_name=mapping,
                target_entity_name=target,
                relationship_description=f"Action mapping {mapping} is {relationship_type} {target}"
            )
        except Exception as e:
            logger.warning(f"Failed to create mapping relationship: {e}")
    
    async def close(self):
        """Close the Graphiti connection."""
        
        if self.graphiti:
            await self.graphiti.close()
            logger.info("Graphiti service closed")