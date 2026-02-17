from typing import List, Dict


def generate_class_diagram(classes: List[Dict], relationships: Dict) -> str:
    """
    Converts class data into Mermaid diagram syntax.

    WHY MERMAID?
    Mermaid is a text-based diagram tool. Instead of drawing boxes manually,
    you write text like:
        classDiagram
            Animal <|-- Dog
            class Dog {
                +bark()
            }
    And it AUTO-RENDERS into a visual diagram.
    We use it because it's easy to generate from code and renders in browsers.

    Example output:
        classDiagram
            class Dog {
                +bark()
                +fetch()
            }
            Animal <|-- Dog
    """
    lines = ["classDiagram"]

    # Add each class with its methods
    for cls in classes:
        lines.append(f"    class {cls['name']} {{")
        for method in cls.get("methods", []):
            lines.append(f"        +{method}()")
        lines.append("    }")

    # Add inheritance arrows
    # Mermaid syntax: Parent <|-- Child  means Child inherits Parent
    for rel in relationships.get("inheritance", []):
        lines.append(f"    {rel['parent']} <|-- {rel['child']}")

    return "\n".join(lines)


def generate_dependency_graph(classes: List[Dict], imports: List[Dict]) -> str:
    """
    Shows what external libraries this code depends on.

    Example output:
        graph TD
            UserService --> fastapi
            UserService --> sqlalchemy
    """
    lines = ["graph TD"]

    # Get all class names
    class_names = [cls["name"] for cls in classes]

    # Get unique external modules (not relative imports)
    external_modules = set()
    for imp in imports:
        module = imp.get("module", "")
        if module and not module.startswith("."):
            # Only take top-level package name (e.g., "fastapi" from "fastapi.middleware")
            top_level = module.split(".")[0]
            external_modules.add(top_level)

    # Connect each class to the modules it uses
    for cls_name in class_names:
        for module in external_modules:
            lines.append(f"    {cls_name} --> {module}[{module}]")

    # If no classes, just show modules
    if not class_names and external_modules:
        for module in external_modules:
            lines.append(f"    App --> {module}[{module}]")

    return "\n".join(lines)


def generate_summary_text(analysis: Dict) -> str:
    """
    Generates a human-readable summary of the codebase.
    This will later be replaced with AI-generated summary.
    """
    classes = analysis.get("classes", [])
    functions = analysis.get("functions", [])
    imports = analysis.get("imports", [])
    relationships = analysis.get("relationships", {})
    inheritance = relationships.get("inheritance", [])

    lines = [
        f"This file contains {len(classes)} class(es) and {len(functions)} top-level function(s).",
    ]

    if inheritance:
        inh_str = ", ".join([f"{r['child']} extends {r['parent']}" for r in inheritance])
        lines.append(f"Inheritance: {inh_str}.")

    if imports:
        modules = list(set([i.get("module", "") for i in imports]))[:5]
        lines.append(f"Key dependencies: {', '.join(modules)}.")

    score = analysis.get("summary", {}).get("complexity_score", 0)
    if score < 5:
        complexity = "simple"
    elif score < 15:
        complexity = "moderate"
    else:
        complexity = "complex"

    lines.append(f"Overall complexity: {complexity} (score: {score}).")

    return " ".join(lines)