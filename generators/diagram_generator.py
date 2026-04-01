from typing import List, Dict, Any, Set, Optional
import logging

logger = logging.getLogger(__name__)


class MermaidGenerator:

    
    def __init__(self):
        self.colors = {
            "class": "#e1f5fe",
            "interface": "#f3e5f5", 
            "external": "#fff3e0",
            "stdlib": "#e8f5e8",
            "function": "#fce4ec"
        }


def generate_class_diagram(classes: List[Dict], relationships: Dict) -> str:

    lines = ["classDiagram"]

    # Add each class with detailed method information
    for cls in classes:
        lines.append(f"    class {cls['name']} {{")
        
        # Add methods with enhanced details
        for method in cls.get("methods", []):
            method_name = method["name"] if isinstance(method, dict) else method
            
            if isinstance(method, dict):
                # Enhanced method display
                params = ", ".join([arg["name"] if isinstance(arg, dict) else arg 
                                  for arg in method.get("args", [])])
                
                # Determine visibility
                if method_name.startswith("__") and method_name.endswith("__"):
                    visibility = "~"  # Protected (dunder methods)
                elif method_name.startswith("_"):
                    visibility = "-"  # Private
                else:
                    visibility = "+"  # Public
                
                # Add method type indicators
                decorations = []
                if method.get("is_async"):
                    decorations.append("async")
                if method.get("is_static"):
                    decorations.append("static")
                if method.get("is_property"):
                    decorations.append("property")
                
                decoration_str = " ".join(decorations)
                if decoration_str:
                    decoration_str = f" [{decoration_str}]"
                
                # Format return type if available
                return_type = method.get("return_type", "")
                return_str = f" -> {return_type}" if return_type else ""
                
                lines.append(f"        {visibility}{method_name}({params}){return_str}{decoration_str}")
            else:
                # Simple method display (fallback)
                visibility = "-" if method_name.startswith("_") else "+"
                lines.append(f"        {visibility}{method_name}()")
        
        lines.append("    }")

    # Add inheritance relationships with enhanced arrow types
    inheritance_rels = relationships.get("inheritance", [])
    for rel in inheritance_rels:
        child = rel["child"]
        parent = rel["parent"]
        
        # Only add if both classes exist in our analysis
        class_names = {cls["name"] for cls in classes}
        if child in class_names and parent in class_names:
            lines.append(f"    {parent} <|-- {child}")

    # Add composition relationships if available
    composition_rels = relationships.get("composition", [])
    for rel in composition_rels:
        container = rel["container"]
        contained = rel["contained"]
        
        # Use composition arrow for "has-a" relationships
        class_names = {cls["name"] for cls in classes}
        if container in class_names and contained in class_names:
            lines.append(f"    {container} --* {contained}")

    return "\n".join(lines)


def generate_dependency_graph(classes: List[Dict], imports: List[Dict]) -> str:
    """
    Shows what external libraries this code depends on.

    Enhanced with:
    - Standard library vs external package detection
    - Module grouping and organization
    - Better node styling
    - Import type differentiation
    """
    lines = ["graph TD"]

    # Get all class names for internal references
    class_names = [cls["name"] for cls in classes]
    
    # Group imports by type for better visualization
    stdlib_modules = {
        "os", "sys", "json", "datetime", "collections", "re", "math", 
        "pathlib", "typing", "asyncio", "logging", "unittest", "time"
    }
    
    external_modules = set()
    used_modules = set()
    
    # Process imports and categorize them
    for imp in imports:
        module = imp.get("module", "")
        if module and not module.startswith("."):
            # Get top-level package name
            top_level = module.split(".")[0]
            used_modules.add(top_level)
            
            if top_level not in stdlib_modules:
                external_modules.add(top_level)

    # Create main application node
    if class_names:
        app_name = f"App[{', '.join(class_names[:3])}{'...' if len(class_names) > 3 else ''}]"
    else:
        app_name = "App[Main Application]"
    
    lines.append(f"    A{app_name}")

    # Add standard library dependencies
    stdlib_used = used_modules & stdlib_modules
    if stdlib_used:
        node_id = "B"
        lines.append(f"    {node_id}[Python Standard Library]:::stdlib")
        lines.append(f"    A --> {node_id}")
        
        # Add individual stdlib modules as subnodes
        for i, module in enumerate(sorted(stdlib_used)):
            sub_id = f"B{i+1}"
            lines.append(f"    {sub_id}[{module}]:::stdlib")
            lines.append(f"    {node_id} --> {sub_id}")

    # Add external dependencies
    if external_modules:
        for i, module in enumerate(sorted(external_modules)):
            node_id = chr(ord('C') + i)
            lines.append(f"    {node_id}[{module}]:::external")
            lines.append(f"    A --> {node_id}")

    # Add styling for different node types
    lines.extend([
        "    classDef stdlib fill:#e8f5e8,stroke:#4caf50",
        "    classDef external fill:#fff3e0,stroke:#ff9800"
    ])

    return "\n".join(lines)


def generate_component_diagram(analysis: Dict) -> str:
    """
    Generate a high-level component architecture diagram.
    
    Shows the overall structure and key components of the codebase.
    """
    lines = ["graph TB"]
    
    classes = analysis.get("classes", [])
    functions = analysis.get("functions", [])
    imports = analysis.get("imports", [])
    
    # Group classes by apparent architectural layers
    models = []
    services = []
    controllers = []
    utilities = []
    
    for cls in classes:
        name = cls["name"].lower()
        if "model" in name or "entity" in name or "dto" in name:
            models.append(cls)
        elif "service" in name or "manager" in name or "handler" in name:
            services.append(cls)
        elif "controller" in name or "view" in name or "api" in name:
            controllers.append(cls)
        else:
            utilities.append(cls)
    
    # Create component nodes
    if controllers:
        lines.append(f"    A[Controllers<br/>{', '.join(c['name'] for c in controllers[:3])}]:::controller")
    
    if services:
        lines.append(f"    B[Business Logic<br/>{', '.join(s['name'] for s in services[:3])}]:::service")
    
    if models:
        lines.append(f"    C[Data Models<br/>{', '.join(m['name'] for m in models[:3])}]:::model")
    
    if functions:
        lines.append(f"    D[Utilities<br/>{len(functions)} functions]:::utility")
    
    # Add layer connections
    if controllers and services:
        lines.append("    A --> B")
    if services and models:
        lines.append("    B --> C")
    if functions and any([controllers, services, models]):
        lines.append("    D --> B")
    
    # Add external dependencies
    external_deps = set()
    for imp in imports:
        module = imp.get("module", "").split(".")[0]
        if module and module not in ["os", "sys", "json", "datetime", "collections"]:
            external_deps.add(module)
    
    if external_deps:
        deps_str = ", ".join(sorted(external_deps)[:4])
        if len(external_deps) > 4:
            deps_str += "..."
        lines.append(f"    E[External Deps<br/>{deps_str}]:::external")
        lines.append("    B --> E")
    
    # Add styling
    lines.extend([
        "    classDef controller fill:#e3f2fd",
        "    classDef service fill:#f3e5f5", 
        "    classDef model fill:#e8f5e8",
        "    classDef utility fill:#fff3e0",
        "    classDef external fill:#ffebee"
    ])
    
    return "\n".join(lines)


def generate_function_call_diagram(relationships: Dict) -> str:
    """
    Generate a diagram showing function call relationships.
    
    Visualizes the flow of function calls to understand code execution paths.
    """
    function_calls = relationships.get("calls", [])
    
    if not function_calls:
        return "graph TD\n    A[No function calls detected]"

    lines = ["graph LR"]
    
    # Track unique functions and relationships
    nodes = set()
    edges = set()
    
    for call in function_calls:
        caller = call.get("from", "unknown")
        callee = call.get("to", "unknown")
        call_type = call.get("call_type", "function")
        
        # Clean names for Mermaid
        caller_clean = _clean_node_name(caller)
        callee_clean = _clean_node_name(callee)
        
        nodes.add((caller_clean, caller))
        nodes.add((callee_clean, callee))
        
        # Create edge with appropriate styling
        if call_type == "method":
            edge_style = "-->"
            edge_label = ""
        else:
            edge_style = "-->"
            edge_label = ""
        
        edges.add((caller_clean, callee_clean, edge_style, edge_label))
    
    # Add nodes with readable labels
    for clean_name, original_name in nodes:
        display_name = _format_display_name(original_name)
        lines.append(f"    {clean_name}[\"{display_name}\"]")
    
    # Add edges
    for caller, callee, style, label in edges:
        if label:
            lines.append(f"    {caller} {style}|{label}| {callee}")
        else:
            lines.append(f"    {caller} {style} {callee}")
    
    return "\n".join(lines)


def generate_summary_text(analysis: Dict) -> str:
    """
    Generates a comprehensive human-readable summary of the codebase.
    
    Enhanced to provide more detailed architectural insights.
    """
    classes = analysis.get("classes", [])
    functions = analysis.get("functions", [])
    imports = analysis.get("imports", [])
    relationships = analysis.get("relationships", {})
    summary_stats = analysis.get("summary", {})
    
    lines = []
    
    # Basic structure summary
    lines.append(f"This codebase contains {len(classes)} class(es) and {len(functions)} top-level function(s).")
    
    # Inheritance analysis
    inheritance = relationships.get("inheritance", [])
    if inheritance:
        inheritance_pairs = [f"{r['child']} extends {r['parent']}" for r in inheritance[:3]]
        lines.append(f"Inheritance relationships: {', '.join(inheritance_pairs)}.")
    
    # Composition analysis
    composition = relationships.get("composition", [])
    if composition:
        lines.append(f"Found {len(composition)} composition relationship(s), indicating object-oriented design.")
    
    # Dependency analysis
    external_deps = []
    stdlib_deps = []
    
    stdlib_modules = {"os", "sys", "json", "datetime", "collections", "re", "math", "typing"}
    
    for imp in imports:
        module = imp.get("module", "").split(".")[0]
        if module:
            if module in stdlib_modules:
                stdlib_deps.append(module)
            elif module and not module.startswith("."):
                external_deps.append(module)
    
    if external_deps:
        unique_external = list(set(external_deps))[:5]
        lines.append(f"Key external dependencies: {', '.join(unique_external)}.")
    
    if stdlib_deps:
        unique_stdlib = list(set(stdlib_deps))[:3]  
        lines.append(f"Uses Python standard library: {', '.join(unique_stdlib)}.")
    
    # Complexity assessment
    complexity_score = summary_stats.get("complexity_score", 0)
    if complexity_score < 10:
        complexity = "simple"
        color = "low complexity, easy to understand"
    elif complexity_score < 30:
        complexity = "moderate"
        color = "moderate complexity, well-structured"
    elif complexity_score < 60:
        complexity = "complex"
        color = "higher complexity, may benefit from refactoring"
    else:
        complexity = "very complex"
        color = "high complexity, consider breaking into smaller modules"
    
    lines.append(f"Overall assessment: {color} (complexity score: {complexity_score}).")
    
    # Architectural pattern detection (simple heuristics)
    patterns = _detect_architectural_patterns(classes, functions)
    if patterns:
        lines.append(f"Detected patterns: {', '.join(patterns)}.")
    
    return " ".join(lines)


def _clean_node_name(name: str) -> str:
    """Clean node name for Mermaid compatibility."""
    # Replace problematic characters
    cleaned = name.replace(".", "_").replace(":", "_").replace(" ", "_")
    # Ensure it starts with a letter
    if cleaned and not cleaned[0].isalpha():
        cleaned = "N" + cleaned
    return cleaned or "unknown"


def _format_display_name(name: str) -> str:
    """Format display name to be readable in diagram."""
    if "." in name:
        parts = name.split(".")
        if len(parts) > 2:
            return f"{parts[0]}...{parts[-1]}"
    return name


def _detect_architectural_patterns(classes: List[Dict], functions: List[Dict]) -> List[str]:
    """
    Detect common architectural patterns based on class and function names.
    
    This is a simple heuristic-based approach.
    """
    patterns = []
    
    class_names = [cls["name"].lower() for cls in classes]
    
    # MVC pattern detection
    has_model = any("model" in name for name in class_names)
    has_view = any("view" in name or "template" in name for name in class_names)
    has_controller = any("controller" in name or "handler" in name for name in class_names)
    
    if has_model and has_view and has_controller:
        patterns.append("MVC (Model-View-Controller)")
    elif has_model and has_controller:
        patterns.append("Model-Controller")
    
    # Service pattern
    if any("service" in name for name in class_names):
        patterns.append("Service Layer")
    
    # Repository pattern
    if any("repository" in name or "repo" in name for name in class_names):
        patterns.append("Repository")
    
    # Factory pattern
    if any("factory" in name for name in class_names):
        patterns.append("Factory")
    
    # Singleton pattern (simple detection)
    if any("singleton" in name for name in class_names):
        patterns.append("Singleton")
    
    # API/Web framework patterns
    framework_indicators = ["api", "router", "endpoint", "route"]
    if any(indicator in name for name in class_names for indicator in framework_indicators):
        patterns.append("REST API")
    
    # Functional programming indicators
    if len(functions) > len(classes) * 2:
        patterns.append("Functional Style")
    
    return patterns
