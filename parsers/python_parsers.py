import ast
from typing import List, Dict, Any, Optional, Set
import logging

logger = logging.getLogger(__name__)


class CodeAnalyzer(ast.NodeVisitor):
    """
    ### will check if anything else can be included
    AST-based Python code analyzer that extracts:
    - Classes (with methods, attributes, inheritance)
    - Top-level functions (excluding class methods)
    - Import statements
    - Docstrings and metadata
    what else can be included  i will hahev to see that 
    
    Uses the Visitor Pattern to traverse the Abstract Syntax Tree.
    
    IMPORTANT: This analyzer correctly distinguishes between class methods
    and top-level functions using the `in_class` flag during traversal.
    """

    def __init__(self):
        self.classes = []
        self.functions = []
        self.imports = []
        self.in_class = False  # tracks if we're inside a class
        self.current_class_name = None
        
        # Additional metadata tracking
        self.global_variables = []
        self.decorators = []
        self.constants = []

    def visit_ClassDef(self, node):
        """
        Called every time AST finds a class definition.
        
        Extracts:
        - Class name
        - Base classes (inheritance)
        - Methods with full details
        - Docstring
        - Line numbers
        """
        # Extract base classes for inheritance
        base_classes = []
        for base in node.bases:
            base_name = self._get_name(base)
            if base_name != "unknown":
                base_classes.append(base_name)
        
        # Get class docstring
        docstring = ast.get_docstring(node)
        
        # Extract decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]
        
        class_info = {
            "name": node.name,
            "methods": [],  # Will be populated as we visit methods
            "bases": base_classes,
            "line": node.lineno,
            "docstring": docstring,
            "decorators": decorators,
            "attributes": [],  # Instance and class attributes
        }
        
        self.classes.append(class_info)

        # Mark that we're inside a class so visit_FunctionDef
        # knows NOT to treat methods as top level functions
        old_in_class = self.in_class
        old_class_name = self.current_class_name
        
        self.in_class = True
        self.current_class_name = node.name
        
        # Walk INTO the class body to find methods
        self.generic_visit(node)
        
        # Restore state when leaving class
        self.in_class = old_in_class  
        self.current_class_name = old_class_name

    def visit_FunctionDef(self, node):
        """
        Extract function/method details.
        
        CRITICAL LOGIC: Only captures TOP-LEVEL functions, not methods.
        Methods are handled separately when in_class=True.
        """
        # Get function docstring
        docstring = ast.get_docstring(node)
        
        # Extract parameters with type annotations if available
        args = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "annotation": self._get_annotation(arg.annotation),
                "default": None  # TODO: Extract default values
            }
            # Skip 'self' parameter for methods
            if arg.arg != "self":
                args.append(param_info)
        
        # Extract decorators
        decorators = [self._get_name(dec) for dec in node.decorator_list]
        
        # Extract return type annotation
        return_annotation = self._get_annotation(node.returns)
        
        function_data = {
            "name": node.name,
            "args": args,
            "line": node.lineno,
            "docstring": docstring,
            "decorators": decorators,
            "return_type": return_annotation,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
            "is_property": "property" in decorators,
            "is_static": "staticmethod" in decorators,
            "is_class_method": "classmethod" in decorators,
        }
        
        if self.in_class:
            # This is a class method - add to current class
            if self.classes:
                self.classes[-1]["methods"].append(function_data)
        else:
            # This is a top-level function
            self.functions.append(function_data)
        
        # Visit function body for nested definitions
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Handle async functions - delegate to regular function handler"""
        self.visit_FunctionDef(node)

    def visit_Import(self, node):
        """
        Handles: import os, import numpy as np
        """
        for alias in node.names:
            import_info = {
                "module": alias.name,    # "numpy"
                "alias": alias.asname,   # "np" or None
                "type": "import",
                "line": node.lineno,
            }
            self.imports.append(import_info)

    def visit_ImportFrom(self, node):
        """
        Handles: from fastapi import FastAPI
        """
        module = node.module or ""
        for alias in node.names:
            import_info = {
                "module": module,        # "fastapi"
                "name": alias.name,      # "FastAPI"
                "alias": alias.asname,   # None or custom alias
                "type": "from_import",
                "line": node.lineno,
            }
            self.imports.append(import_info)
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """
        Extract global variables and class attributes.
        """
        if not self.in_class:
            # Global variable assignment
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_info = {
                        "name": target.id,
                        "line": node.lineno,
                        "type": "global_variable",
                        "value": self._extract_value(node.value)
                    }
                    self.global_variables.append(var_info)
        else:
            # Class attribute assignment (if assigned to self)
            for target in node.targets:
                if (isinstance(target, ast.Attribute) and 
                    isinstance(target.value, ast.Name) and 
                    target.value.id == "self"):
                    
                    attr_info = {
                        "name": target.attr,
                        "line": node.lineno,
                        "type": "instance_attribute",
                        "value": self._extract_value(node.value)
                    }
                    
                    if self.classes:
                        self.classes[-1]["attributes"].append(attr_info)
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node):
        """
        Handle annotated assignments: x: int = 5
        """
        if isinstance(node.target, ast.Name):
            var_info = {
                "name": node.target.id,
                "line": node.lineno,
                "type": "annotated_variable",
                "annotation": self._get_annotation(node.annotation),
                "value": self._extract_value(node.value) if node.value else None
            }
            
            if self.in_class:
                if self.classes:
                    self.classes[-1]["attributes"].append(var_info)
            else:
                self.global_variables.append(var_info)
        
        self.generic_visit(node)

    def _get_name(self, node) -> str:
        """
        Extract readable name from AST node.
        
        Handles various node types to get meaningful names.
        """
        if node is None:
            return "unknown"
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._get_name(node.value)
            return f"{base}.{node.attr}" if base != "unknown" else node.attr
        elif isinstance(node, ast.Call):
            # Decorator call like @dataclass()
            return self._get_name(node.func)
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            # Fallback: try to unparse the node
            try:
                return ast.unparse(node)
            except:
                return "unknown"

    def _get_annotation(self, annotation_node) -> Optional[str]:
        """
        Extract type annotation as string.
        
        Examples:
        - int -> "int"
        - List[str] -> "List[str]"
        - Optional[Dict[str, Any]] -> "Optional[Dict[str, Any]]"
        """
        if annotation_node is None:
            return None
        
        try:
            return ast.unparse(annotation_node)
        except:
            return self._get_name(annotation_node)
    
    def _extract_value(self, value_node) -> Any:
        """
        Extract simple literal values from AST nodes.
        
        Handles: strings, numbers, booleans, None
        For complex expressions, returns string representation.
        """
        if value_node is None:
            return None
        elif isinstance(value_node, ast.Constant):
            return value_node.value
        elif isinstance(value_node, ast.Name):
            return value_node.id
        elif isinstance(value_node, ast.List):
            return "[list]"
        elif isinstance(value_node, ast.Dict):
            return "{dict}"
        else:
            try:
                return ast.unparse(value_node)
            except:
                return "complex_expression"
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Generate summary statistics about the analyzed code.
        """
        total_methods = sum(len(cls["methods"]) for cls in self.classes)
        
        # Calculate complexity metrics
        inheritance_count = sum(len(cls["bases"]) for cls in self.classes)
        
        # Function complexity (simple metric based on parameter count)
        avg_function_params = 0
        if self.functions:
            total_params = sum(len(func["args"]) for func in self.functions)
            avg_function_params = total_params / len(self.functions)
        
        return {
            "total_classes": len(self.classes),
            "total_functions": len(self.functions),
            "total_methods": total_methods,
            "total_imports": len(self.imports),
            "global_variables": len(self.global_variables),
            "inheritance_relationships": inheritance_count,
            "avg_function_params": round(avg_function_params, 2),
            "complexity_score": self._calculate_complexity_score(),
        }
    
    def _calculate_complexity_score(self) -> int:
        """
        Calculate a simple complexity score for the codebase.
        
        Higher score = more complex
        """
        class_weight = 3
        function_weight = 2
        method_weight = 1
        import_weight = 1
        
        total_methods = sum(len(cls["methods"]) for cls in self.classes)
        
        return (
            len(self.classes) * class_weight +
            len(self.functions) * function_weight +
            total_methods * method_weight +
            len(self.imports) * import_weight
        )


def analyze_file(code: str, filename: str = "unknown") -> Dict:
    """
    Main entry point for Python code analysis.
    
    Args:
        code: Python source code as string
        filename: Name of the file being analyzed
        
    Returns:
        Dictionary containing structured analysis results
    """
    try:
        # Parse the code into an Abstract Syntax Tree
        tree = ast.parse(code, filename=filename)
        
        # Create analyzer and walk the tree
        analyzer = CodeAnalyzer()
        analyzer.visit(tree)
        
        # Get summary statistics
        summary_stats = analyzer.get_summary_stats()
        
        return {
            "classes": analyzer.classes,
            "functions": analyzer.functions,
            "imports": analyzer.imports,
            "global_variables": analyzer.global_variables,
            "summary": summary_stats,
            "metadata": {
                "filename": filename,
                "lines_of_code": len(code.splitlines()),
                "analysis_version": "1.0"
            }
        }
        
    except SyntaxError as e:
        logger.error(f"Syntax error in {filename}: {e}")
        raise SyntaxError(f"Invalid Python syntax at line {e.lineno}: {e.msg}")
    except Exception as e:
        logger.error(f"Error analyzing {filename}: {e}")
        raise RuntimeError(f"Analysis failed: {str(e)}")
