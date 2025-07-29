"""
CodeBERT Embedding Service

Generates semantic embeddings for Java code using Microsoft's CodeBERT model
with GPU optimization and batch processing for enterprise-scale analysis.
"""

import asyncio
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pickle
import json

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel, AutoConfig
from pydantic import BaseModel

from .java_parser_service import JavaClass, JavaMethod, JavaField

logger = logging.getLogger(__name__)


class CodeEmbedding(BaseModel):
    """Represents a code embedding with metadata."""
    
    embedding: List[float]
    code_type: str  # class, method, field, snippet
    identifier: str  # qualified name or unique identifier
    source_code: str
    metadata: Dict[str, Any] = {}
    timestamp: float = 0.0
    model_version: str = ""


class CodeBERTService:
    """Service for generating CodeBERT embeddings with enterprise optimizations."""
    
    def __init__(
        self,
        model_name: str = "microsoft/codebert-base",
        device: str = "auto",
        batch_size: int = 16,
        max_length: int = 512,
        cache_dir: Optional[str] = None
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_length = max_length
        self.cache_dir = Path(cache_dir) if cache_dir else Path("./embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Device configuration
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        # Model components
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model: Optional[AutoModel] = None
        self.sentence_transformer: Optional[SentenceTransformer] = None
        
        # Caching
        self.embedding_cache: Dict[str, CodeEmbedding] = {}
        self.cache_file = self.cache_dir / "embedding_cache.pkl"
        
        # Performance tracking
        self.stats = {
            "embeddings_generated": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
            "gpu_memory_usage": 0
        }
        
        logger.info(f"Initialized CodeBERT service with device: {self.device}")
    
    async def initialize(self):
        """Initialize the CodeBERT model and tokenizer."""
        
        logger.info(f"Loading CodeBERT model: {self.model_name}")
        start_time = time.time()
        
        try:
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Load model with appropriate device mapping
            if self.device == "cuda" and torch.cuda.is_available():
                # GPU initialization
                self.model = AutoModel.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,  # Use half precision for memory efficiency
                    device_map="auto"
                )
                self.model.eval()
                
                # Log GPU memory usage
                if torch.cuda.is_available():
                    memory_allocated = torch.cuda.memory_allocated() / 1024**3
                    memory_reserved = torch.cuda.memory_reserved() / 1024**3
                    logger.info(f"GPU memory - Allocated: {memory_allocated:.2f} GB, Reserved: {memory_reserved:.2f} GB")
                    self.stats["gpu_memory_usage"] = memory_allocated
            
            else:
                # CPU initialization
                self.model = AutoModel.from_pretrained(self.model_name)
                self.model.eval()
                logger.info("Using CPU for CodeBERT inference")
            
            # Try to initialize sentence transformer for easier usage
            try:
                self.sentence_transformer = SentenceTransformer(self.model_name, device=self.device)
                logger.info("Sentence transformer initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize sentence transformer: {e}")
                logger.info("Will use raw transformers model")
            
            # Load existing cache
            await self._load_cache()
            
            load_time = time.time() - start_time
            logger.info(f"CodeBERT model loaded successfully in {load_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to initialize CodeBERT model: {e}")
            raise
    
    async def _load_cache(self):
        """Load embedding cache from disk."""
        
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    self.embedding_cache = cached_data.get('embeddings', {})
                    logger.info(f"Loaded {len(self.embedding_cache)} cached embeddings")
            except Exception as e:
                logger.warning(f"Failed to load embedding cache: {e}")
    
    async def _save_cache(self):
        """Save embedding cache to disk."""
        
        try:
            cache_data = {
                'embeddings': self.embedding_cache,
                'stats': self.stats,
                'model_name': self.model_name,
                'timestamp': time.time()
            }
            
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            logger.debug(f"Saved {len(self.embedding_cache)} embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")
    
    def _get_cache_key(self, code: str, code_type: str) -> str:
        """Generate cache key for code snippet."""
        
        content = f"{code_type}:{code}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def generate_embedding(
        self,
        code: str,
        code_type: str = "snippet",
        identifier: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> CodeEmbedding:
        """Generate embedding for a single code snippet."""
        
        cache_key = self._get_cache_key(code, code_type)
        
        # Check cache first
        if cache_key in self.embedding_cache:
            self.stats["cache_hits"] += 1
            return self.embedding_cache[cache_key]
        
        self.stats["cache_misses"] += 1
        start_time = time.time()
        
        try:
            # Preprocess code for better embeddings
            processed_code = self._preprocess_code(code, code_type)
            
            # Generate embedding
            if self.sentence_transformer:
                embedding = await self._generate_with_sentence_transformer([processed_code])
                embedding = embedding[0]
            else:
                embedding = await self._generate_with_transformers([processed_code])
                embedding = embedding[0]
            
            # Create embedding object
            code_embedding = CodeEmbedding(
                embedding=embedding.tolist(),
                code_type=code_type,
                identifier=identifier,
                source_code=code,
                metadata=metadata or {},
                timestamp=time.time(),
                model_version=self.model_name
            )
            
            # Cache the result
            self.embedding_cache[cache_key] = code_embedding
            
            # Update stats
            processing_time = time.time() - start_time
            self.stats["embeddings_generated"] += 1
            self.stats["total_processing_time"] += processing_time
            
            logger.debug(f"Generated embedding for {code_type} in {processing_time:.3f}s")
            
            return code_embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for {code_type}: {e}")
            raise
    
    async def generate_batch_embeddings(
        self,
        code_snippets: List[Tuple[str, str, str]],  # (code, code_type, identifier)
        metadata_list: Optional[List[Dict[str, Any]]] = None
    ) -> List[CodeEmbedding]:
        """Generate embeddings for multiple code snippets in batches."""
        
        logger.info(f"Generating embeddings for {len(code_snippets)} code snippets")
        
        results = []
        metadata_list = metadata_list or [{}] * len(code_snippets)
        
        # Process in batches
        for i in range(0, len(code_snippets), self.batch_size):
            batch_end = min(i + self.batch_size, len(code_snippets))
            batch_snippets = code_snippets[i:batch_end]
            batch_metadata = metadata_list[i:batch_end]
            
            batch_results = await self._process_batch(batch_snippets, batch_metadata)
            results.extend(batch_results)
            
            # Save cache periodically
            if i % (self.batch_size * 10) == 0:
                await self._save_cache()
        
        # Final cache save
        await self._save_cache()
        
        logger.info(f"Generated {len(results)} embeddings successfully")
        return results
    
    async def _process_batch(
        self,
        batch_snippets: List[Tuple[str, str, str]],
        batch_metadata: List[Dict[str, Any]]
    ) -> List[CodeEmbedding]:
        """Process a single batch of code snippets."""
        
        # Separate cached and non-cached items
        cached_results = []
        to_process = []
        to_process_indices = []
        
        for idx, (code, code_type, identifier) in enumerate(batch_snippets):
            cache_key = self._get_cache_key(code, code_type)
            
            if cache_key in self.embedding_cache:
                cached_results.append((idx, self.embedding_cache[cache_key]))
                self.stats["cache_hits"] += 1
            else:
                to_process.append((code, code_type, identifier))
                to_process_indices.append(idx)
                self.stats["cache_misses"] += 1
        
        # Process non-cached items
        if to_process:
            start_time = time.time()
            
            # Preprocess codes
            processed_codes = [
                self._preprocess_code(code, code_type) 
                for code, code_type, _ in to_process
            ]
            
            # Generate embeddings
            if self.sentence_transformer:
                embeddings = await self._generate_with_sentence_transformer(processed_codes)
            else:
                embeddings = await self._generate_with_transformers(processed_codes)
            
            # Create embedding objects and cache them
            for idx, ((code, code_type, identifier), embedding) in enumerate(zip(to_process, embeddings)):
                code_embedding = CodeEmbedding(
                    embedding=embedding.tolist(),
                    code_type=code_type,
                    identifier=identifier,
                    source_code=code,
                    metadata=batch_metadata[to_process_indices[idx]],
                    timestamp=time.time(),
                    model_version=self.model_name
                )
                
                # Cache the result
                cache_key = self._get_cache_key(code, code_type)
                self.embedding_cache[cache_key] = code_embedding
                
                cached_results.append((to_process_indices[idx], code_embedding))
            
            # Update stats
            processing_time = time.time() - start_time
            self.stats["embeddings_generated"] += len(to_process)
            self.stats["total_processing_time"] += processing_time
            
            logger.debug(f"Processed batch of {len(to_process)} embeddings in {processing_time:.3f}s")
        
        # Sort results by original index
        cached_results.sort(key=lambda x: x[0])
        return [result for _, result in cached_results]
    
    def _preprocess_code(self, code: str, code_type: str) -> str:
        """Preprocess code for better embedding generation."""
        
        # Remove excessive whitespace
        code = ' '.join(code.split())
        
        # Truncate if too long
        if len(code) > self.max_length * 4:  # Rough character limit
            code = code[:self.max_length * 4]
        
        # Add context prefix based on code type
        if code_type == "class":
            code = f"java class: {code}"
        elif code_type == "method":
            code = f"java method: {code}"
        elif code_type == "field":
            code = f"java field: {code}"
        elif code_type == "struts_action":
            code = f"struts action: {code}"
        elif code_type == "corba_method":
            code = f"corba method: {code}"
        
        return code
    
    async def _generate_with_sentence_transformer(self, codes: List[str]) -> np.ndarray:
        """Generate embeddings using sentence transformer."""
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                lambda: self.sentence_transformer.encode(
                    codes,
                    batch_size=self.batch_size,
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True
                )
            )
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings with sentence transformer: {e}")
            raise
    
    async def _generate_with_transformers(self, codes: List[str]) -> np.ndarray:
        """Generate embeddings using raw transformers model."""
        
        try:
            embeddings = []
            
            # Process in smaller sub-batches to manage memory
            sub_batch_size = min(self.batch_size, 8)
            
            for i in range(0, len(codes), sub_batch_size):
                sub_batch = codes[i:i + sub_batch_size]
                
                # Tokenize
                inputs = self.tokenizer(
                    sub_batch,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                )
                
                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Generate embeddings
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    
                    # Use CLS token embeddings
                    cls_embeddings = outputs.last_hidden_state[:, 0, :]
                    
                    # Normalize
                    cls_embeddings = torch.nn.functional.normalize(cls_embeddings, p=2, dim=1)
                    
                    # Move to CPU and convert to numpy
                    cls_embeddings = cls_embeddings.cpu().numpy()
                    embeddings.append(cls_embeddings)
            
            # Concatenate all embeddings
            all_embeddings = np.vstack(embeddings)
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings with transformers: {e}")
            raise
    
    async def embed_java_class(self, java_class: JavaClass) -> Dict[str, CodeEmbedding]:
        """Generate embeddings for all components of a Java class."""
        
        embeddings = {}
        
        # Class-level embedding
        class_code = self._extract_class_signature(java_class)
        class_embedding = await self.generate_embedding(
            class_code,
            code_type="class",
            identifier=java_class.qualified_name,
            metadata={
                "package": java_class.package,
                "type": java_class.type.value,
                "is_struts_action": java_class.is_struts_action,
                "is_corba_servant": java_class.is_corba_servant,
                "file_path": java_class.file_path
            }
        )
        embeddings[f"class:{java_class.qualified_name}"] = class_embedding
        
        # Method embeddings
        for method in java_class.methods:
            method_code = self._extract_method_signature(method)
            method_embedding = await self.generate_embedding(
                method_code,
                code_type="method",
                identifier=f"{java_class.qualified_name}.{method.name}",
                metadata={
                    "class": java_class.qualified_name,
                    "return_type": method.return_type,
                    "is_struts_action": method.is_struts_action,
                    "is_corba_method": method.is_corba_method,
                    "line_number": method.line_number
                }
            )
            embeddings[f"method:{java_class.qualified_name}.{method.name}"] = method_embedding
        
        # Field embeddings (for important fields)
        for field in java_class.fields:
            if self._is_important_field(field):
                field_code = self._extract_field_signature(field)
                field_embedding = await self.generate_embedding(
                    field_code,
                    code_type="field",
                    identifier=f"{java_class.qualified_name}.{field.name}",
                    metadata={
                        "class": java_class.qualified_name,
                        "type": field.type,
                        "line_number": field.line_number
                    }
                )
                embeddings[f"field:{java_class.qualified_name}.{field.name}"] = field_embedding
        
        return embeddings
    
    def _extract_class_signature(self, java_class: JavaClass) -> str:
        """Extract class signature for embedding."""
        
        signature_parts = []
        
        # Add annotations
        if java_class.annotations:
            signature_parts.extend(f"@{ann}" for ann in java_class.annotations)
        
        # Add class declaration
        class_decl = f"{java_class.type.value} {java_class.name}"
        
        if java_class.extends:
            class_decl += f" extends {java_class.extends}"
        
        if java_class.implements:
            class_decl += f" implements {', '.join(java_class.implements)}"
        
        signature_parts.append(class_decl)
        
        # Add key imports (framework-related)
        key_imports = [imp for imp in java_class.imports 
                      if any(keyword in imp for keyword in ['struts', 'corba', 'javax', 'org.apache'])]
        signature_parts.extend(key_imports[:5])  # Limit to top 5
        
        return " ".join(signature_parts)
    
    def _extract_method_signature(self, method: JavaMethod) -> str:
        """Extract method signature for embedding."""
        
        signature_parts = []
        
        # Add annotations
        if method.annotations:
            signature_parts.extend(f"@{ann}" for ann in method.annotations)
        
        # Add method signature
        params = ", ".join(f"{p.type} {p.name}" for p in method.parameters)
        method_sig = f"{method.return_type} {method.name}({params})"
        
        if method.throws:
            method_sig += f" throws {', '.join(method.throws)}"
        
        signature_parts.append(method_sig)
        
        return " ".join(signature_parts)
    
    def _extract_field_signature(self, field: JavaField) -> str:
        """Extract field signature for embedding."""
        
        signature_parts = []
        
        # Add annotations
        if field.annotations:
            signature_parts.extend(f"@{ann}" for ann in field.annotations)
        
        # Add field declaration
        field_decl = f"{field.type} {field.name}"
        if field.initial_value:
            field_decl += f" = {field.initial_value}"
        
        signature_parts.append(field_decl)
        
        return " ".join(signature_parts)
    
    def _is_important_field(self, field: JavaField) -> bool:
        """Determine if a field is important enough to embed."""
        
        # Skip simple constants and basic fields
        if field.modifiers.static and field.modifiers.final:
            return False
        
        # Include fields with annotations
        if field.annotations:
            return True
        
        # Include complex types
        if any(keyword in field.type.lower() for keyword in 
               ['action', 'form', 'service', 'dao', 'manager', 'handler']):
            return True
        
        return False
    
    async def semantic_search(
        self,
        query: str,
        embeddings: Dict[str, CodeEmbedding],
        top_k: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[Tuple[str, float, CodeEmbedding]]:
        """Perform semantic search over code embeddings."""
        
        # Generate query embedding
        query_embedding = await self.generate_embedding(query, "query")
        query_vector = np.array(query_embedding.embedding)
        
        # Calculate similarities
        similarities = []
        
        for identifier, embedding in embeddings.items():
            code_vector = np.array(embedding.embedding)
            similarity = np.dot(query_vector, code_vector) / (
                np.linalg.norm(query_vector) * np.linalg.norm(code_vector)
            )
            
            if similarity >= similarity_threshold:
                similarities.append((identifier, float(similarity), embedding))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        
        return {
            **self.stats,
            "cache_size": len(self.embedding_cache),
            "device": self.device,
            "model_name": self.model_name,
            "cache_hit_rate": (
                self.stats["cache_hits"] / 
                max(self.stats["cache_hits"] + self.stats["cache_misses"], 1)
            )
        }
    
    async def close(self):
        """Clean up resources and save cache."""
        
        await self._save_cache()
        
        # Clear GPU memory
        if self.device == "cuda" and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("CodeBERT service closed")


# Utility functions for code analysis

def extract_business_logic_methods(java_class: JavaClass) -> List[JavaMethod]:
    """Extract methods that likely contain business logic."""
    
    business_methods = []
    
    for method in java_class.methods:
        # Skip getters/setters
        if method.name.startswith(('get', 'set')) and len(method.parameters) <= 1:
            continue
        
        # Skip constructors and standard methods
        if method.name in ['toString', 'equals', 'hashCode', 'clone']:
            continue
        
        # Include methods with business-related names
        business_keywords = [
            'process', 'calculate', 'validate', 'execute', 'handle',
            'create', 'update', 'delete', 'save', 'load', 'find',
            'business', 'rule', 'logic', 'workflow'
        ]
        
        if any(keyword in method.name.lower() for keyword in business_keywords):
            business_methods.append(method)
        
        # Include Struts action methods
        elif method.is_struts_action:
            business_methods.append(method)
        
        # Include methods with complex parameters or return types
        elif len(method.parameters) > 2 or 'void' not in method.return_type:
            business_methods.append(method)
    
    return business_methods