"""
Java AST Parsing Service

Parses Java source code to extract abstract syntax trees and structural information
for Struts, CORBA, and general Java enterprise applications.
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

import aiofiles

logger = logging.getLogger(__name__)


class JavaElementType(Enum):
    """Types of Java code elements."""
    CLASS = "class"
    INTERFACE = "interface"
    ENUM = "enum"
    METHOD = "method"
    FIELD = "field"
    CONSTRUCTOR = "constructor"
    ANNOTATION = "annotation"


@dataclass
class JavaModifier:
    """Represents Java modifiers."""
    public: bool = False
    private: bool = False
    protected: bool = False
    static: bool = False
    final: bool = False
    abstract: bool = False
    synchronized: bool = False
    native: bool = False
    transient: bool = False
    volatile: bool = False


@dataclass
class JavaParameter:
    """Represents a method parameter."""
    name: str
    type: str
    is_final: bool = False
    annotations: List[str] = field(default_factory=list)


@dataclass
class JavaMethod:
    """Represents a Java method."""
    name: str
    return_type: str
    parameters: List[JavaParameter] = field(default_factory=list)
    modifiers: JavaModifier = field(default_factory=JavaModifier)
    annotations: List[str] = field(default_factory=list)
    throws: List[str] = field(default_factory=list)
    line_number: int = 0
    body_lines: int = 0
    calls_methods: List[str] = field(default_factory=list)
    is_struts_action: bool = False
    is_corba_method: bool = False


@dataclass
class JavaField:
    """Represents a Java field."""
    name: str
    type: str
    modifiers: JavaModifier = field(default_factory=JavaModifier)
    annotations: List[str] = field(default_factory=list)
    initial_value: Optional[str] = None
    line_number: int = 0


@dataclass
class JavaClass:
    """Represents a Java class, interface, or enum."""
    name: str
    qualified_name: str
    type: JavaElementType
    package: str
    modifiers: JavaModifier = field(default_factory=JavaModifier)
    annotations: List[str] = field(default_factory=list)
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    methods: List[JavaMethod] = field(default_factory=list)
    fields: List[JavaField] = field(default_factory=list)
    inner_classes: List['JavaClass'] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    line_number: int = 0
    file_path: str = ""
    
    # Struts-specific
    is_struts_action: bool = False
    struts_mappings: List[str] = field(default_factory=list)
    
    # CORBA-specific
    is_corba_servant: bool = False
    is_corba_helper: bool = False
    corba_interfaces: List[str] = field(default_factory=list)


@dataclass
class StrutsMapping:
    """Represents a Struts action mapping."""
    path: str
    type: str
    name: Optional[str] = None
    scope: Optional[str] = None
    input: Optional[str] = None
    forwards: Dict[str, str] = field(default_factory=dict)
    form_bean: Optional[str] = None


@dataclass
class StrutsFormBean:
    """Represents a Struts form bean."""
    name: str
    type: str
    properties: List[str] = field(default_factory=list)


@dataclass
class CORBAInterface:
    """Represents a CORBA IDL interface."""
    name: str
    module: str
    operations: List[Dict[str, Any]] = field(default_factory=list)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    inherits: List[str] = field(default_factory=list)


class JavaParserService:
    """Service for parsing Java code and extracting structural information."""
    
    def __init__(self):
        self.parsed_files: Dict[str, JavaClass] = {}
        self.struts_mappings: Dict[str, StrutsMapping] = {}
        self.struts_form_beans: Dict[str, StrutsFormBean] = {}
        self.corba_interfaces: Dict[str, CORBAInterface] = {}
        
        # Regex patterns for Java parsing
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for Java parsing."""
        
        # Class/Interface/Enum declarations
        self.class_pattern = re.compile(
            r'(?:public\s+|private\s+|protected\s+)?'
            r'(?:static\s+|final\s+|abstract\s+)*'
            r'(class|interface|enum)\s+(\w+)'
            r'(?:\s+extends\s+(\w+(?:\.\w+)*))?'
            r'(?:\s+implements\s+([\w\s,.<>]+))?'
        )
        
        # Method declarations
        self.method_pattern = re.compile(
            r'(?:public\s+|private\s+|protected\s+)?'
            r'(?:static\s+|final\s+|abstract\s+|synchronized\s+|native\s+)*'
            r'(\w+(?:\[\]|<[^>]+>)?)\s+'
            r'(\w+)\s*\(([^)]*)\)'
            r'(?:\s+throws\s+([\w\s,.<>]+))?'
        )
        
        # Field declarations
        self.field_pattern = re.compile(
            r'(?:public\s+|private\s+|protected\s+)?'
            r'(?:static\s+|final\s+|transient\s+|volatile\s+)*'
            r'(\w+(?:\[\]|<[^>]+>)?)\s+'
            r'(\w+)(?:\s*=\s*([^;]+))?;'
        )
        
        # Import statements
        self.import_pattern = re.compile(r'import\s+(static\s+)?([^;]+);')
        
        # Package declaration
        self.package_pattern = re.compile(r'package\s+([^;]+);')
        
        # Annotations
        self.annotation_pattern = re.compile(r'@(\w+)(?:\([^)]*\))?')
        
        # Struts-specific patterns
        self.struts_action_pattern = re.compile(r'extends\s+.*Action')
        self.struts_form_pattern = re.compile(r'extends\s+.*ActionForm')
        
        # CORBA-specific patterns
        self.corba_servant_pattern = re.compile(r'extends\s+.*POA')
        self.corba_helper_pattern = re.compile(r'class\s+\w+Helper')
        self.corba_holder_pattern = re.compile(r'class\s+\w+Holder')
    
    async def parse_java_file(self, file_path: Path) -> Optional[JavaClass]:
        """Parse a single Java file and extract class information."""
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            return self._parse_java_content(content, str(file_path))
            
        except Exception as e:
            logger.warning(f"Failed to parse Java file {file_path}: {e}")
            return None
    
    def _parse_java_content(self, content: str, file_path: str) -> Optional[JavaClass]:
        """Parse Java content and extract class information."""
        
        lines = content.split('\n')
        
        # Extract package
        package = ""
        package_match = self.package_pattern.search(content)
        if package_match:
            package = package_match.group(1).strip()
        
        # Extract imports
        imports = []
        for match in self.import_pattern.finditer(content):
            import_stmt = match.group(2).strip()
            imports.append(import_stmt)
        
        # Find main class declaration
        class_match = self.class_pattern.search(content)
        if not class_match:
            return None
        
        class_type_str = class_match.group(1)
        class_name = class_match.group(2)
        extends_class = class_match.group(3)
        implements_str = class_match.group(4)
        
        # Parse implements list
        implements = []
        if implements_str:
            implements = [impl.strip() for impl in implements_str.split(',')]
        
        # Determine class type
        if class_type_str == "class":
            class_type = JavaElementType.CLASS
        elif class_type_str == "interface":
            class_type = JavaElementType.INTERFACE
        else:  # enum
            class_type = JavaElementType.ENUM
        
        # Create class object
        qualified_name = f"{package}.{class_name}" if package else class_name
        
        java_class = JavaClass(
            name=class_name,
            qualified_name=qualified_name,
            type=class_type,
            package=package,
            extends=extends_class,
            implements=implements,
            imports=imports,
            file_path=file_path
        )
        
        # Detect Struts components
        if self.struts_action_pattern.search(content):
            java_class.is_struts_action = True
        
        # Detect CORBA components
        if self.corba_servant_pattern.search(content):
            java_class.is_corba_servant = True
        elif self.corba_helper_pattern.search(content):
            java_class.is_corba_helper = True
        
        # Parse methods
        java_class.methods = self._parse_methods(content, lines)
        
        # Parse fields
        java_class.fields = self._parse_fields(content, lines)
        
        # Parse annotations at class level
        java_class.annotations = self._parse_annotations_before_line(
            lines, class_match.start()
        )
        
        return java_class
    
    def _parse_methods(self, content: str, lines: List[str]) -> List[JavaMethod]:
        """Parse method declarations from Java content."""
        
        methods = []
        
        for match in self.method_pattern.finditer(content):
            return_type = match.group(1)
            method_name = match.group(2)
            params_str = match.group(3)
            throws_str = match.group(4)
            
            # Skip if this looks like a field or other construct
            if return_type in ['class', 'interface', 'enum']:
                continue
            
            # Parse parameters
            parameters = self._parse_parameters(params_str)
            
            # Parse throws clause
            throws = []
            if throws_str:
                throws = [t.strip() for t in throws_str.split(',')]
            
            # Find line number
            line_number = content[:match.start()].count('\n') + 1
            
            # Parse annotations
            annotations = self._parse_annotations_before_line(lines, match.start())
            
            # Check if this is a Struts action method
            is_struts_action = (
                method_name in ['execute', 'perform'] or
                'ActionMapping' in params_str or
                'ActionForm' in params_str
            )
            
            # Check if this is a CORBA method
            is_corba_method = (
                'org.omg.CORBA' in '\n'.join(annotations) or
                any('CORBA' in throw for throw in throws)
            )
            
            method = JavaMethod(
                name=method_name,
                return_type=return_type,
                parameters=parameters,
                throws=throws,
                line_number=line_number,
                annotations=annotations,
                is_struts_action=is_struts_action,
                is_corba_method=is_corba_method
            )
            
            methods.append(method)
        
        return methods
    
    def _parse_fields(self, content: str, lines: List[str]) -> List[JavaField]:
        """Parse field declarations from Java content."""
        
        fields = []
        
        for match in self.field_pattern.finditer(content):
            field_type = match.group(1)
            field_name = match.group(2)
            initial_value = match.group(3)
            
            # Find line number
            line_number = content[:match.start()].count('\n') + 1
            
            # Parse annotations
            annotations = self._parse_annotations_before_line(lines, match.start())
            
            field = JavaField(
                name=field_name,
                type=field_type,
                initial_value=initial_value.strip() if initial_value else None,
                line_number=line_number,
                annotations=annotations
            )
            
            fields.append(field)
        
        return fields
    
    def _parse_parameters(self, params_str: str) -> List[JavaParameter]:
        """Parse method parameters string."""
        
        parameters = []
        
        if not params_str.strip():
            return parameters
        
        # Split by commas, but handle generics
        param_parts = []
        current_param = ""
        bracket_depth = 0
        
        for char in params_str:
            if char == '<':
                bracket_depth += 1
            elif char == '>':
                bracket_depth -= 1
            elif char == ',' and bracket_depth == 0:
                param_parts.append(current_param.strip())
                current_param = ""
                continue
            
            current_param += char
        
        if current_param.strip():
            param_parts.append(current_param.strip())
        
        # Parse each parameter
        for param_str in param_parts:
            parts = param_str.strip().split()
            if len(parts) >= 2:
                # Handle final modifier
                is_final = 'final' in parts
                param_type = parts[-2] if is_final else parts[0]
                param_name = parts[-1]
                
                # Extract annotations
                annotations = [part for part in parts if part.startswith('@')]
                
                parameter = JavaParameter(
                    name=param_name,
                    type=param_type,
                    is_final=is_final,
                    annotations=annotations
                )
                
                parameters.append(parameter)
        
        return parameters
    
    def _parse_annotations_before_line(self, lines: List[str], start_pos: int) -> List[str]:
        """Parse annotations that appear before a given position."""
        
        annotations = []
        line_num = start_pos
        
        # Look backwards for annotations
        while line_num > 0:
            line_num -= 1
            line = lines[line_num].strip()
            
            if not line or line.startswith('//') or line.startswith('/*'):
                continue
            
            annotation_matches = self.annotation_pattern.findall(line)
            if annotation_matches:
                annotations.extend(annotation_matches)
            else:
                break  # Stop if we hit a non-annotation line
        
        return annotations[::-1]  # Reverse to maintain order
    
    async def parse_struts_config(self, config_path: Path) -> Dict[str, StrutsMapping]:
        """Parse Struts configuration files."""
        
        mappings = {}
        
        try:
            tree = ET.parse(config_path)
            root = tree.getroot()
            
            # Parse action mappings
            action_mappings = root.findall('.//action-mapping') or root.findall('.//action')
            
            for action in action_mappings:
                path = action.get('path')
                action_type = action.get('type')
                name = action.get('name')
                scope = action.get('scope')
                input_path = action.get('input')
                
                # Parse forwards
                forwards = {}
                forward_elements = action.findall('.//forward')
                for forward in forward_elements:
                    forward_name = forward.get('name')
                    forward_path = forward.get('path')
                    if forward_name and forward_path:
                        forwards[forward_name] = forward_path
                
                if path:
                    mapping = StrutsMapping(
                        path=path,
                        type=action_type or "",
                        name=name,
                        scope=scope,
                        input=input_path,
                        forwards=forwards
                    )
                    mappings[path] = mapping
            
            # Parse form beans
            form_beans = root.findall('.//form-bean')
            for form_bean in form_beans:
                name = form_bean.get('name')
                bean_type = form_bean.get('type')
                
                if name and bean_type:
                    self.struts_form_beans[name] = StrutsFormBean(
                        name=name,
                        type=bean_type
                    )
            
        except Exception as e:
            logger.warning(f"Failed to parse Struts config {config_path}: {e}")
        
        return mappings
    
    async def parse_corba_idl(self, idl_path: Path) -> Dict[str, CORBAInterface]:
        """Parse CORBA IDL files."""
        
        interfaces = {}
        
        try:
            async with aiofiles.open(idl_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            # Simple IDL parsing - this could be enhanced with proper IDL parser
            lines = content.split('\n')
            current_module = ""
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # Parse module
                if line.startswith('module '):
                    module_match = re.search(r'module\s+(\w+)', line)
                    if module_match:
                        current_module = module_match.group(1)
                
                # Parse interface
                elif line.startswith('interface '):
                    interface_match = re.search(r'interface\s+(\w+)(?:\s*:\s*([\w\s,]+))?', line)
                    if interface_match:
                        interface_name = interface_match.group(1)
                        inherits_str = interface_match.group(2)
                        
                        inherits = []
                        if inherits_str:
                            inherits = [inh.strip() for inh in inherits_str.split(',')]
                        
                        # Parse interface body
                        operations = []
                        attributes = []
                        
                        i += 1
                        while i < len(lines) and not lines[i].strip().startswith('}'):
                            op_line = lines[i].strip()
                            
                            # Parse operations (methods)
                            if '(' in op_line and ')' in op_line:
                                op_match = re.search(r'(\w+)\s+(\w+)\s*\(([^)]*)\)', op_line)
                                if op_match:
                                    return_type = op_match.group(1)
                                    op_name = op_match.group(2)
                                    params = op_match.group(3)
                                    
                                    operations.append({
                                        'name': op_name,
                                        'return_type': return_type,
                                        'parameters': params
                                    })
                            
                            # Parse attributes
                            elif 'attribute' in op_line:
                                attr_match = re.search(r'attribute\s+(\w+)\s+(\w+)', op_line)
                                if attr_match:
                                    attr_type = attr_match.group(1)
                                    attr_name = attr_match.group(2)
                                    
                                    attributes.append({
                                        'name': attr_name,
                                        'type': attr_type
                                    })
                            
                            i += 1
                        
                        interfaces[interface_name] = CORBAInterface(
                            name=interface_name,
                            module=current_module,
                            operations=operations,
                            attributes=attributes,
                            inherits=inherits
                        )
                
                i += 1
            
        except Exception as e:
            logger.warning(f"Failed to parse CORBA IDL {idl_path}: {e}")
        
        return interfaces
    
    async def parse_repository(self, repo_path: Path) -> Dict[str, Any]:
        """Parse an entire repository and extract all Java structures."""
        
        logger.info(f"Parsing repository: {repo_path}")
        
        results = {
            'classes': {},
            'struts_mappings': {},
            'struts_form_beans': {},
            'corba_interfaces': {},
            'statistics': {
                'total_files': 0,
                'java_files': 0,
                'struts_actions': 0,
                'corba_servants': 0,
                'total_methods': 0,
                'total_fields': 0
            }
        }
        
        # Find and parse Java files
        java_files = list(repo_path.rglob("*.java"))
        results['statistics']['java_files'] = len(java_files)
        
        # Parse Java files concurrently
        semaphore = asyncio.Semaphore(10)  # Limit concurrent file operations
        tasks = []
        
        for java_file in java_files:
            task = self._parse_file_with_semaphore(semaphore, java_file)
            tasks.append(task)
        
        parsed_classes = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(parsed_classes):
            if isinstance(result, Exception):
                logger.warning(f"Failed to parse {java_files[i]}: {result}")
                continue
            
            if result:
                results['classes'][result.qualified_name] = result
                
                # Update statistics
                results['statistics']['total_methods'] += len(result.methods)
                results['statistics']['total_fields'] += len(result.fields)
                
                if result.is_struts_action:
                    results['statistics']['struts_actions'] += 1
                
                if result.is_corba_servant:
                    results['statistics']['corba_servants'] += 1
        
        # Parse Struts configuration files
        struts_configs = list(repo_path.rglob("struts-config*.xml"))
        for config_file in struts_configs:
            mappings = await self.parse_struts_config(config_file)
            results['struts_mappings'].update(mappings)
        
        results['struts_form_beans'] = self.struts_form_beans
        
        # Parse CORBA IDL files
        idl_files = list(repo_path.rglob("*.idl"))
        for idl_file in idl_files:
            interfaces = await self.parse_corba_idl(idl_file)
            results['corba_interfaces'].update(interfaces)
        
        results['statistics']['total_files'] = len(java_files) + len(struts_configs) + len(idl_files)
        
        logger.info(f"Parsed repository {repo_path.name}: "
                   f"{results['statistics']['java_files']} Java files, "
                   f"{len(results['classes'])} classes, "
                   f"{results['statistics']['struts_actions']} Struts actions, "
                   f"{results['statistics']['corba_servants']} CORBA servants")
        
        return results
    
    async def _parse_file_with_semaphore(self, semaphore: asyncio.Semaphore, file_path: Path) -> Optional[JavaClass]:
        """Parse a file with semaphore-controlled concurrency."""
        
        async with semaphore:
            return await self.parse_java_file(file_path)
    
    def get_parsing_statistics(self) -> Dict[str, int]:
        """Get statistics about parsed files."""
        
        return {
            'total_classes': len(self.parsed_files),
            'struts_actions': sum(1 for cls in self.parsed_files.values() if cls.is_struts_action),
            'corba_servants': sum(1 for cls in self.parsed_files.values() if cls.is_corba_servant),
            'interfaces': sum(1 for cls in self.parsed_files.values() if cls.type == JavaElementType.INTERFACE),
            'total_methods': sum(len(cls.methods) for cls in self.parsed_files.values()),
            'total_fields': sum(len(cls.fields) for cls in self.parsed_files.values())
        }