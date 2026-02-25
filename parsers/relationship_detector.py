import ast
from typing import Dict, List, Any, Set, Optional


class RelationshipDetector(ast.NodeVisitor):
    """
    AST-based relationship detector that finds connections between code components.
    
    Uses the visitor pattern to traverse the AST and detect:
    - Inheritance relationships (class A extends B)
    - Function call relationships (function X calls Y)
    - Import dependencies (module imports)
    - Composition relationships (class A uses class B)
    
    This is the SECOND PASS after basic parsing to find relationships.
    """

    def __init__(self):
        self.relationships = {
            "inheritance": [],   # parent-child class relationships
            "calls": [],         # function/method call relationships
            "imports": [],       # import dependency relationships
            "composition": []    # composition/aggregation relationships
        }
        
        # Track current context during AST traversal
        self.current_class: Optional[str] = None
        self.current_function: Optional[str] = None
        self.scope_stack: List[str] = []  # Track nested scopes
        
        # Store extracted entities for cross-referencing
        self.class_names: Set[str] = set()
        self.function_names: Set[str] = set()
        self.imported_modules: Dict[str, str] = {}  # module -> alias mapping

    def visit_ClassDef(self, node):
        """
        Extract inheritance relationships from class definitions.
        
        Example: class Dog(Animal, Mammal) -> Dog inherits from Animal and Mammal
        """
        self.class_names.add(node.name)
        
        # Detect inheritance from base classes
        for base in node.bases:
            parent_name = self._get_name(base)
            if parent_name != "unknown":
                self.relationships["inheritance"].append({
                    "child": node.name,
                    "parent": parent_name,
                    "line": node.lineno,
                    "type": "inherits"
                })

        # Set context for visiting class body
        old_class = self.current_class
        self.current_class = node.name
        self.scope_stack.append(f"class:{node.name}")
        
        # Visit class body (methods, nested classes)
        self.generic_visit(node)
        
        # Restore context
        self.current_class = old_class
        self.scope_stack.pop()
    
    def visit_FunctionDef(self, node):
        """
        Track function definitions and set context for call detection.
        """
        if not self.current_class:  # Only track top-level functions
            self.function_names.add(node.name)
        
        # Set context for visiting function body
        old_function = self.current_function
        self.current_function = node.name
        
        if self.current_class:
            scope_name = f"{self.current_class}.{node.name}"
        else:
            scope_name = node.name
        
        self.scope_stack.append(f"function:{scope_name}")
        
        # Visit function body to detect calls
        self.generic_visit(node)
        
        # Restore context
        self.current_function = old_function
        self.scope_stack.pop()
    
    def visit_AsyncFunctionDef(self, node):
        """Handle async functions same as regular functions"""
        self.visit_FunctionDef(node)
    
    def visit_Import(self, node):
        """
        Track import statements: import os, numpy as np
        """
        for alias in node.names:
            module = alias.name
            alias_name = alias.asname or alias.name
            
            self.imported_modules[alias_name] = module
            
            self.relationships["imports"].append({
                "module": module,
                "alias": alias.asname,
                "type": "import",
                "line": node.lineno,
                "from_scope": self._get_current_scope()
            })
    
    def visit_ImportFrom(self, node):
        """
        Track from-import statements: from fastapi import FastAPI
        """
        module = node.module or ""
        
        for alias in node.names:
            name = alias.name
            alias_name = alias.asname or name
            
            # Track the imported name
            if module:
                full_name = f"{module}.{name}"
            else:
                full_name = name
            
            self.imported_modules[alias_name] = full_name
            
            self.relationships["imports"].append({
                "module": module,
                "name": name,
                "alias": alias.asname,
                "type": "from_import",
                "line": node.lineno,
                "from_scope": self._get_current_scope()
            })

    def visit_Call(self, node):
        """
        Detect function/method calls to understand code flow.
        
        Examples:
        - my_function() -> detects call to my_function
        - obj.method() -> detects method call
        - MyClass() -> detects instantiation
        """
        caller_scope = self._get_current_scope()
        callee = self._extract_call_target(node.func)
        
        if callee and caller_scope:
            self.relationships["calls"].append({
                "from": caller_scope,
                "to": callee,
                "line": node.lineno,
                "type": "function_call",
                "call_type": self._classify_call(node.func)
            })
        
        # Check for composition (instantiating other classes)
        if self._is_class_instantiation(node.func):
            instantiated_class = self._get_name(node.func)
            if instantiated_class and self.current_class:
                self.relationships["composition"].append({
                    "container": self.current_class,
                    "contained": instantiated_class,
                    "line": node.lineno,
                    "type": "instantiation"
                })

        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """
        Detect composition relationships through class instantiation in assignments.
        
        Example: self.engine = Engine() -> Car contains Engine
        """
        if isinstance(node.value, ast.Call) and self.current_class:
            instantiated_class = self._get_name(node.value.func)
            
            if instantiated_class and instantiated_class in self.class_names:
                # Check if assignment is to instance variable (self.something)
                for target in node.targets:
                    if (isinstance(target, ast.Attribute) and 
                        isinstance(target.value, ast.Name) and 
                        target.value.id == "self"):
                        
                        self.relationships["composition"].append({
                            "container": self.current_class,
                            "contained": instantiated_class,
                            "attribute": target.attr,
                            "line": node.lineno,
                            "type": "composition"
                        })
        
        self.generic_visit(node)

    def _get_name(self, node):
        """
        Extract a readable name from various AST node types.
        
        Handles: Name, Attribute (obj.attr), Subscript (obj[key])
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            base = self._get_name(node.value)
            if base:
                return f"{base}[]"
        return "unknown"
    
    def _extract_call_target(self, node):
        """
        Extract the target of a function call.
        
        Examples:
        - func() -> "func"
        - obj.method() -> "obj.method"  
        - MyClass() -> "MyClass"
        """
        if isinstance(node, ast.Name):
            # Simple function call: func()
            return node.id
        elif isinstance(node, ast.Attribute):
            # Method call: obj.method()
            base = self._get_name(node.value)
            if base:
                return f"{base}.{node.attr}"
        
        return None
    
    def _classify_call(self, node):
        """
        Classify the type of function call.
        """
        if isinstance(node, ast.Name):
            return "function"
        elif isinstance(node, ast.Attribute):
            return "method"
        else:
            return "complex"
    
    def _is_class_instantiation(self, node):
        """
        Check if a call node represents class instantiation.
        
        Heuristic: If the called name starts with uppercase, it's likely a class.
        """
        if isinstance(node, ast.Name):
            return node.id[0].isupper() if node.id else False
        elif isinstance(node, ast.Attribute):
            return node.attr[0].isupper() if node.attr else False
        
        return False
    
    def _get_current_scope(self):
        """
        Get the current scope as a readable string.
        
        Examples:
        - "global"
        - "class:Dog"
        - "class:Dog.function:bark"
        """
        if not self.scope_stack:
            return "global"
        
        return ".".join(self.scope_stack)
    
    def analyze_relationships(self, code: str) -> Dict[str, List[Dict]]:
        """
        Main entry point for relationship analysis.
        
        Args:
            code: Python source code string
        
        Returns:
            Dictionary of detected relationships
        """
        try:
            tree = ast.parse(code)
            self.visit(tree)
            return self.relationships
        except SyntaxError as e:
            raise SyntaxError(f"Cannot parse code for relationship analysis: {e}")
    
    def get_complexity_metrics(self) -> Dict[str, Any]:
        """
        Calculate complexity metrics based on relationships.
        
        Returns:
            Dictionary with various complexity measurements
        """
        return {
            "inheritance_depth": self._calculate_inheritance_depth(),
            "coupling_score": self._calculate_coupling(),
            "call_graph_complexity": len(self.relationships["calls"]),
            "total_dependencies": len(self.relationships["imports"]),
            "composition_relationships": len(self.relationships["composition"])
        }
    
    def _calculate_inheritance_depth(self) -> int:
        """
        Calculate the maximum inheritance depth in the codebase.
        """
        inheritance = self.relationships["inheritance"]
        if not inheritance:
            return 0
        
        # Build parent-child mapping
        children = {}
        for rel in inheritance:
            parent = rel["parent"]
            child = rel["child"]
            if parent not in children:
                children[parent] = []
            children[parent].append(child)
        
        # Find maximum depth using DFS
        def get_depth(node, visited):
            if node in visited:
                return 0  # Avoid cycles
            visited.add(node)
            
            if node not in children:
                return 1
            
            max_child_depth = 0
            for child in children[node]:
                child_depth = get_depth(child, visited.copy())
                max_child_depth = max(max_child_depth, child_depth)
            
            return 1 + max_child_depth
        
        # Find root nodes (classes that are not children of anyone)
        all_children = set(rel["child"] for rel in inheritance)
        all_parents = set(rel["parent"] for rel in inheritance)
        roots = all_parents - all_children
        
        if not roots:
            return 1
        
        max_depth = 0
        for root in roots:
            depth = get_depth(root, set())
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def _calculate_coupling(self) -> float:
        """
        Calculate coupling score based on function calls and imports.
        
        Higher score = more coupled (potentially harder to maintain)
        """
        calls = len(self.relationships["calls"])
        imports = len(self.relationships["imports"])
        classes = len(self.class_names)
        functions = len(self.function_names)
        
        if classes + functions == 0:
            return 0.0
        
        # Normalize by number of entities
        coupling_score = (calls + imports) / (classes + functions)
        
        # Cap at reasonable maximum
        return min(coupling_score, 10.0)