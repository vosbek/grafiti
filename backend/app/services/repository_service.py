"""
Repository Management and Dependency Discovery Service

Handles repository cloning, dependency analysis, and recursive discovery
for enterprise Java applications with Maven, Gradle, and Ant support.
"""

import asyncio
import logging
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
import subprocess
import json

import aiofiles
import git
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class DependencyInfo(BaseModel):
    """Represents a discovered dependency."""
    
    group_id: str
    artifact_id: str
    version: Optional[str] = None
    scope: Optional[str] = None
    repository_url: Optional[str] = None
    dependency_type: str  # maven, gradle, ant, jar, internal


class RepositoryInfo(BaseModel):
    """Represents repository information."""
    
    name: str
    url: str
    local_path: str
    build_system: str  # maven, gradle, ant, mixed
    dependencies: List[DependencyInfo]
    is_analyzed: bool = False
    analysis_timestamp: Optional[str] = None


class RepositoryService:
    """Manages repository operations and dependency discovery."""
    
    def __init__(self, workspace_dir: str, max_concurrent_clones: int = 5):
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent_clones = max_concurrent_clones
        
        # Cache for discovered repositories and dependencies
        self.repository_cache: Dict[str, RepositoryInfo] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Repository name mapping for internal dependencies
        self.name_mappings: Dict[str, str] = {}
        self._load_name_mappings()
    
    def _load_name_mappings(self):
        """Load repository name mappings from configuration."""
        
        # Default mappings for common enterprise patterns
        self.name_mappings = {
            # Common internal package to repository mappings
            "com.company.auth": "authentication-service",
            "com.company.payment": "payment-service", 
            "com.company.user": "user-management",
            "com.company.common": "common-utilities",
            "org.company": "company-framework",
        }
        
        # Try to load custom mappings
        mapping_file = self.workspace_dir / "repository-mappings.json"
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r') as f:
                    custom_mappings = json.load(f)
                    self.name_mappings.update(custom_mappings)
                logger.info(f"Loaded {len(custom_mappings)} custom repository mappings")
            except Exception as e:
                logger.warning(f"Failed to load repository mappings: {e}")
    
    async def discover_dependencies(self, starting_repo_url: str) -> List[str]:
        """
        Discover all dependent repositories starting from a main repository.
        
        Returns list of repository URLs to clone.
        """
        
        logger.info(f"Starting dependency discovery from: {starting_repo_url}")
        
        discovered_repos = set()
        to_process = [starting_repo_url]
        processed = set()
        
        while to_process:
            current_repo = to_process.pop(0)
            
            if current_repo in processed:
                continue
                
            logger.info(f"Analyzing repository: {current_repo}")
            processed.add(current_repo)
            discovered_repos.add(current_repo)
            
            try:
                # Clone repository temporarily for analysis
                temp_repo_info = await self._clone_repository_temp(current_repo)
                
                # Analyze dependencies
                dependencies = await self._analyze_repository_dependencies(temp_repo_info)
                
                # Find repository URLs for dependencies
                new_repos = await self._resolve_dependency_repositories(dependencies)
                
                # Add new repositories to process queue
                for repo_url in new_repos:
                    if repo_url not in processed and repo_url not in to_process:
                        to_process.append(repo_url)
                        logger.info(f"Discovered dependency repository: {repo_url}")
                
            except Exception as e:
                logger.warning(f"Failed to analyze repository {current_repo}: {e}")
                continue
        
        logger.info(f"Discovery complete. Found {len(discovered_repos)} repositories")
        return list(discovered_repos)
    
    async def _clone_repository_temp(self, repo_url: str) -> RepositoryInfo:
        """Clone repository to temporary location for analysis."""
        
        repo_name = self._extract_repo_name(repo_url)
        temp_path = self.workspace_dir / "temp" / repo_name
        
        # Remove existing temp directory
        if temp_path.exists():
            import shutil
            shutil.rmtree(temp_path)
        
        temp_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Clone repository
            logger.info(f"Cloning {repo_url} to {temp_path}")
            repo = git.Repo.clone_from(repo_url, temp_path, depth=1)  # Shallow clone
            
            return RepositoryInfo(
                name=repo_name,
                url=repo_url,
                local_path=str(temp_path),
                build_system="unknown",
                dependencies=[]
            )
            
        except Exception as e:
            logger.error(f"Failed to clone repository {repo_url}: {e}")
            raise
    
    def _extract_repo_name(self, repo_url: str) -> str:
        """Extract repository name from URL."""
        
        parsed = urlparse(repo_url)
        path = parsed.path.strip('/')
        
        if path.endswith('.git'):
            path = path[:-4]
        
        return path.split('/')[-1]
    
    async def _analyze_repository_dependencies(self, repo_info: RepositoryInfo) -> List[DependencyInfo]:
        """Analyze repository to extract all dependencies."""
        
        repo_path = Path(repo_info.local_path)
        dependencies = []
        
        # Detect build system(s)
        build_systems = []
        
        if (repo_path / "pom.xml").exists():
            build_systems.append("maven")
        
        if any(repo_path.glob("build.gradle*")):
            build_systems.append("gradle")
        
        if (repo_path / "build.xml").exists():
            build_systems.append("ant")
        
        repo_info.build_system = ",".join(build_systems) if build_systems else "unknown"
        
        # Analyze Maven dependencies
        if "maven" in build_systems:
            maven_deps = await self._analyze_maven_dependencies(repo_path)
            dependencies.extend(maven_deps)
        
        # Analyze Gradle dependencies
        if "gradle" in build_systems:
            gradle_deps = await self._analyze_gradle_dependencies(repo_path)
            dependencies.extend(gradle_deps)
        
        # Analyze Ant dependencies
        if "ant" in build_systems:
            ant_deps = await self._analyze_ant_dependencies(repo_path)
            dependencies.extend(ant_deps)
        
        # Analyze JAR dependencies (lib folders)
        jar_deps = await self._analyze_jar_dependencies(repo_path)
        dependencies.extend(jar_deps)
        
        # Analyze Java imports for internal dependencies
        import_deps = await self._analyze_java_imports(repo_path)
        dependencies.extend(import_deps)
        
        repo_info.dependencies = dependencies
        logger.info(f"Found {len(dependencies)} dependencies in {repo_info.name}")
        
        return dependencies
    
    async def _analyze_maven_dependencies(self, repo_path: Path) -> List[DependencyInfo]:
        """Analyze Maven pom.xml files for dependencies."""
        
        dependencies = []
        
        # Find all pom.xml files (including modules)
        pom_files = list(repo_path.rglob("pom.xml"))
        
        for pom_file in pom_files:
            try:
                tree = ET.parse(pom_file)
                root = tree.getroot()
                
                # Handle XML namespaces
                ns = {'maven': 'http://maven.apache.org/POM/4.0.0'}
                if root.tag.startswith('{'):
                    ns_url = root.tag.split('}')[0][1:]
                    ns = {'maven': ns_url}
                
                # Extract dependencies
                deps = root.findall(".//maven:dependency", ns)
                if not deps:  # Try without namespace
                    deps = root.findall(".//dependency")
                
                for dep in deps:
                    group_id = self._get_element_text(dep, "groupId", ns)
                    artifact_id = self._get_element_text(dep, "artifactId", ns)
                    version = self._get_element_text(dep, "version", ns)
                    scope = self._get_element_text(dep, "scope", ns)
                    
                    if group_id and artifact_id:
                        dependencies.append(DependencyInfo(
                            group_id=group_id,
                            artifact_id=artifact_id,
                            version=version,
                            scope=scope,
                            dependency_type="maven"
                        ))
                
            except Exception as e:
                logger.warning(f"Failed to parse Maven POM {pom_file}: {e}")
        
        return dependencies
    
    async def _analyze_gradle_dependencies(self, repo_path: Path) -> List[DependencyInfo]:
        """Analyze Gradle build files for dependencies."""
        
        dependencies = []
        
        # Find all Gradle build files
        gradle_files = list(repo_path.rglob("build.gradle*"))
        
        for gradle_file in gradle_files:
            try:
                async with aiofiles.open(gradle_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Parse Gradle dependencies using regex
                # This is a simplified parser - could be enhanced with proper Groovy parsing
                dependency_patterns = [
                    r"implementation\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                    r"compile\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                    r"api\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                    r"testImplementation\s+['\"]([^:]+):([^:]+):([^'\"]+)['\"]",
                ]
                
                for pattern in dependency_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches:
                        group_id, artifact_id, version = match
                        dependencies.append(DependencyInfo(
                            group_id=group_id,
                            artifact_id=artifact_id,
                            version=version,
                            dependency_type="gradle"
                        ))
                
            except Exception as e:
                logger.warning(f"Failed to parse Gradle file {gradle_file}: {e}")
        
        return dependencies
    
    async def _analyze_ant_dependencies(self, repo_path: Path) -> List[DependencyInfo]:
        """Analyze Ant build.xml files for dependencies."""
        
        dependencies = []
        
        # Find all build.xml files
        ant_files = list(repo_path.rglob("build.xml"))
        
        for ant_file in ant_files:
            try:
                tree = ET.parse(ant_file)
                root = tree.getroot()
                
                # Look for ivy dependencies
                ivy_deps = root.findall(".//ivy:dependency", {'ivy': 'antlib:org.apache.ivy.ant'})
                if not ivy_deps:
                    ivy_deps = root.findall(".//dependency")
                
                for dep in ivy_deps:
                    org = dep.get('org')
                    name = dep.get('name')
                    rev = dep.get('rev')
                    
                    if org and name:
                        dependencies.append(DependencyInfo(
                            group_id=org,
                            artifact_id=name,
                            version=rev,
                            dependency_type="ant"
                        ))
                
                # Look for JAR file references
                jar_refs = root.findall(".//fileset")
                for fileset in jar_refs:
                    includes = fileset.get('includes', '')
                    if '*.jar' in includes:
                        # This indicates JAR dependencies but we'll handle them separately
                        pass
                
            except Exception as e:
                logger.warning(f"Failed to parse Ant file {ant_file}: {e}")
        
        return dependencies
    
    async def _analyze_jar_dependencies(self, repo_path: Path) -> List[DependencyInfo]:
        """Analyze JAR files in lib directories."""
        
        dependencies = []
        
        # Common library directory names
        lib_dirs = ["lib", "libs", "library", "libraries", "ext", "external"]
        
        for lib_dir_name in lib_dirs:
            lib_paths = list(repo_path.rglob(lib_dir_name))
            
            for lib_path in lib_paths:
                if lib_path.is_dir():
                    jar_files = list(lib_path.glob("*.jar"))
                    
                    for jar_file in jar_files:
                        # Extract artifact name from JAR filename
                        jar_name = jar_file.stem
                        
                        # Try to parse version from filename
                        version_match = re.search(r'-(\d+(?:\.\d+)*(?:-\w+)?)$', jar_name)
                        if version_match:
                            artifact_id = jar_name[:version_match.start()]
                            version = version_match.group(1)
                        else:
                            artifact_id = jar_name
                            version = None
                        
                        dependencies.append(DependencyInfo(
                            group_id="unknown",
                            artifact_id=artifact_id,
                            version=version,
                            dependency_type="jar"
                        ))
        
        return dependencies
    
    async def _analyze_java_imports(self, repo_path: Path) -> List[DependencyInfo]:
        """Analyze Java source files for import statements indicating internal dependencies."""
        
        dependencies = []
        internal_packages = set()
        
        # Find all Java files
        java_files = list(repo_path.rglob("*.java"))
        
        for java_file in java_files[:100]:  # Limit to first 100 files for performance
            try:
                async with aiofiles.open(java_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Extract import statements
                import_pattern = r'import\s+(static\s+)?([a-zA-Z_][a-zA-Z0-9_.]*);'
                imports = re.findall(import_pattern, content)
                
                for _, import_name in imports:
                    # Look for internal company packages
                    if any(import_name.startswith(prefix) for prefix in ["com.company", "org.company", "com.internal"]):
                        # Extract package root (first 3 parts)
                        package_parts = import_name.split('.')
                        if len(package_parts) >= 3:
                            package_root = '.'.join(package_parts[:3])
                            internal_packages.add(package_root)
                
            except Exception as e:
                logger.warning(f"Failed to analyze Java file {java_file}: {e}")
        
        # Convert internal packages to dependencies
        for package in internal_packages:
            dependencies.append(DependencyInfo(
                group_id=package,
                artifact_id="internal",
                dependency_type="internal"
            ))
        
        return dependencies
    
    def _get_element_text(self, parent, tag_name: str, namespaces: Dict[str, str]) -> Optional[str]:
        """Helper to get element text with namespace support."""
        
        element = parent.find(f"maven:{tag_name}", namespaces)
        if element is None:
            element = parent.find(tag_name)
        
        return element.text if element is not None else None
    
    async def _resolve_dependency_repositories(self, dependencies: List[DependencyInfo]) -> List[str]:
        """Resolve dependencies to repository URLs."""
        
        repository_urls = []
        
        for dep in dependencies:
            if dep.dependency_type == "internal":
                # Try to map internal packages to repository URLs
                repo_url = await self._resolve_internal_dependency(dep.group_id)
                if repo_url:
                    repository_urls.append(repo_url)
            
            elif dep.dependency_type in ["maven", "gradle"]:
                # Try to find repository URL for external dependencies
                # This would typically involve querying Maven Central, internal Nexus, etc.
                repo_url = await self._resolve_external_dependency(dep)
                if repo_url:
                    repository_urls.append(repo_url)
        
        return repository_urls
    
    async def _resolve_internal_dependency(self, package_name: str) -> Optional[str]:
        """Resolve internal package to repository URL."""
        
        # Check explicit mappings first
        if package_name in self.name_mappings:
            repo_name = self.name_mappings[package_name]
            # Convert to GitHub URL (customize for your organization)
            return f"https://github.com/your-org/{repo_name}.git"
        
        # Try common naming patterns
        package_parts = package_name.split('.')
        if len(package_parts) >= 3:
            potential_names = [
                package_parts[-1],  # Last part
                f"{package_parts[-2]}-{package_parts[-1]}",  # Last two parts
                package_parts[-1].replace('_', '-'),  # Convert underscores
            ]
            
            for name in potential_names:
                # This would typically query your Git organization
                # For now, we'll just construct potential URLs
                potential_url = f"https://github.com/your-org/{name}.git"
                
                # In a real implementation, you'd check if this repository exists
                # if await self._repository_exists(potential_url):
                #     return potential_url
        
        return None
    
    async def _resolve_external_dependency(self, dep: DependencyInfo) -> Optional[str]:
        """Resolve external dependency to source repository URL."""
        
        # This would typically involve:
        # 1. Querying Maven Central for source repository
        # 2. Checking if it's an internal artifact in Nexus
        # 3. Looking up known mappings
        
        # For demonstration, we'll skip external dependencies
        # In enterprise environments, you might want to include some
        
        return None
    
    async def clone_repositories(self, repository_urls: List[str]) -> Dict[str, RepositoryInfo]:
        """Clone multiple repositories concurrently."""
        
        logger.info(f"Cloning {len(repository_urls)} repositories...")
        
        semaphore = asyncio.Semaphore(self.max_concurrent_clones)
        tasks = []
        
        for repo_url in repository_urls:
            task = self._clone_single_repository(semaphore, repo_url)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        cloned_repos = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to clone {repository_urls[i]}: {result}")
            else:
                cloned_repos[result.url] = result
        
        logger.info(f"Successfully cloned {len(cloned_repos)} repositories")
        return cloned_repos
    
    async def _clone_single_repository(self, semaphore: asyncio.Semaphore, repo_url: str) -> RepositoryInfo:
        """Clone a single repository with concurrency control."""
        
        async with semaphore:
            repo_name = self._extract_repo_name(repo_url)
            local_path = self.workspace_dir / repo_name
            
            # Remove existing directory if it exists
            if local_path.exists():
                import shutil
                shutil.rmtree(local_path)
            
            try:
                logger.info(f"Cloning {repo_url}...")
                repo = git.Repo.clone_from(repo_url, local_path)
                
                repo_info = RepositoryInfo(
                    name=repo_name,
                    url=repo_url,
                    local_path=str(local_path),
                    build_system="unknown",
                    dependencies=[]
                )
                
                # Cache the repository info
                self.repository_cache[repo_url] = repo_info
                
                logger.info(f"Successfully cloned {repo_name}")
                return repo_info
                
            except Exception as e:
                logger.error(f"Failed to clone {repo_url}: {e}")
                raise
    
    def get_cloned_repositories(self) -> List[RepositoryInfo]:
        """Get list of all cloned repositories."""
        
        return list(self.repository_cache.values())
    
    def get_dependency_graph(self) -> Dict[str, List[str]]:
        """Get the complete dependency graph."""
        
        return {k: list(v) for k, v in self.dependency_graph.items()}