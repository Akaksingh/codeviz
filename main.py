import ast
import logging
import time
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from generators.diagram_generator import (
    generate_class_diagram,
    generate_dependency_graph,
    generate_component_diagram,
    generate_function_call_diagram,
    generate_summary_text,
)
from parsers.python_parsers import analyze_file
from parsers.relationship_detector import RelationshipDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CodeViz - Code-to-Architecture Diagram Generator",
    description="Upload Python files and get architecture analysis + interactive diagrams",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request/Response logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all requests and responses for monitoring"""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response


@app.get("/")
async def home():
    """
    API information and available endpoints.
    """
    return {
        "name": "CodeViz API",
        "version": "2.0.0",
        "description": "Python code architecture analysis and diagram generation",
        "status": "running",
        "endpoints": {
            "GET /": "This information page",
            "GET /health": "Health check endpoint",
            "POST /analyze": "Analyze Python file structure and relationships",
            "POST /diagram": "Generate Mermaid diagrams from Python files",
            "GET /docs": "Interactive API documentation",
        },
        "diagram_types": ["class", "dependency", "component", "calls"],
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and deployment.
    """
    try:
        # Basic health indicators
        import sys
        import platform
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "python_version": sys.version,
            "platform": platform.system(),
            "api_version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/analyze")
async def analyze_code(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Comprehensive Python code analysis endpoint.
    
    Analyzes uploaded file and returns:
    - Classes with methods, inheritance, and metadata
    - Top-level functions with parameters and type hints  
    - Import statements and dependencies
    - Relationships (inheritance, calls, composition)
    - Summary statistics and complexity metrics
    
    Args:
        file: Python file (.py extension required)
        
    Returns:
        JSON with complete analysis results
    """
    # Validate file upload
    if not file.filename:
        raise HTTPException(
            status_code=400, 
            detail="No file provided"
        )
    
    if not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400, 
            detail="Only Python (.py) files are supported"
        )
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 10MB."
        )

    try:
        logger.info(f"Starting analysis of {file.filename}")
        
        # Read and decode file contents
        contents = await file.read()
        try:
            code = contents.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400, 
                detail="File must be valid UTF-8 encoded text"
            )
        
        # Validate non-empty file
        if not code.strip():
            return {
                "filename": file.filename,
                "message": "Empty file",
                "classes": [],
                "functions": [],
                "imports": [],
                "relationships": {"inheritance": [], "calls": [], "imports": [], "composition": []},
                "summary": {"total_classes": 0, "total_functions": 0, "total_imports": 0, "complexity_score": 0},
                "status": "success"
            }

        # Perform comprehensive analysis
        analysis = analyze_file(code, file.filename)
        
        # Detect relationships using AST
        tree = ast.parse(code)
        rel_detector = RelationshipDetector()
        rel_detector.visit(tree)
        
        # Get complexity metrics
        complexity_metrics = rel_detector.get_complexity_metrics()
        
        # Combine results
        complete_analysis = {
            "filename": file.filename,
            "classes": analysis["classes"],
            "functions": analysis["functions"],
            "imports": analysis["imports"],
            "global_variables": analysis.get("global_variables", []),
            "relationships": rel_detector.relationships,
            "summary": {
                **analysis["summary"],
                **complexity_metrics
            },
            "metadata": {
                **analysis.get("metadata", {}),
                "analysis_timestamp": time.time(),
                "file_size_bytes": len(contents),
                "lines_of_code": len(code.splitlines())
            },
            "status": "success"
        }
        
        logger.info(f"Successfully analyzed {file.filename} - {len(analysis['classes'])} classes, {len(analysis['functions'])} functions")
        
        return complete_analysis
        
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file.filename}: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid Python syntax at line {e.lineno}: {e.msg}"
        )
    except ValueError as e:
        logger.warning(f"Value error in {file.filename}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"File processing error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error analyzing {file.filename}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal analysis error: {str(e)}"
        )


@app.post("/diagram")
async def generate_diagrams(
    file: UploadFile = File(...),
    diagram_type: str = Query(
        default="class",
        description="Type of diagram to generate",
        enum=["class", "dependency", "component", "calls"]
    ),
    include_analysis: bool = Query(
        default=False,
        description="Include full analysis data in response"
    )
) -> Dict[str, Any]:
    """
    Generate Mermaid diagrams from uploaded Python file.
    
    Supported diagram types:
    - class: Class diagram with inheritance and methods
    - dependency: Import dependency graph
    - component: High-level architecture overview
    - calls: Function call flow diagram
    
    Args:
        file: Python file (.py extension required)
        diagram_type: Type of diagram to generate
        include_analysis: Whether to include full analysis in response
        
    Returns:
        JSON with Mermaid diagram syntax and metadata
    """
    # Validate file
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(
            status_code=400, 
            detail="Only Python (.py) files are supported"
        )

    try:
        logger.info(f"Generating {diagram_type} diagram for {file.filename}")
        
        # Read and analyze file
        contents = await file.read()
        code = contents.decode("utf-8")

        # Perform analysis
        analysis = analyze_file(code, file.filename)
        tree = ast.parse(code)
        rel_detector = RelationshipDetector()
        rel_detector.visit(tree)

        # Combine analysis with relationships
        full_analysis = {
            **analysis,
            "relationships": rel_detector.relationships
        }

        # Generate requested diagram
        diagram = None
        if diagram_type == "class":
            diagram = generate_class_diagram(
                analysis["classes"],
                rel_detector.relationships
            )
        elif diagram_type == "dependency":
            diagram = generate_dependency_graph(
                analysis["classes"],
                analysis["imports"]
            )
        elif diagram_type == "component":
            diagram = generate_component_diagram(full_analysis)
        elif diagram_type == "calls":
            diagram = generate_function_call_diagram(rel_detector.relationships)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported diagram type: {diagram_type}"
            )

        # Generate AI-like summary
        summary_text = generate_summary_text(full_analysis)

        # Prepare response
        response = {
            "filename": file.filename,
            "diagram_type": diagram_type,
            "mermaid_code": diagram,
            "summary_text": summary_text,
            "stats": {
                "total_classes": len(analysis["classes"]),
                "total_functions": len(analysis["functions"]),
                "total_imports": len(analysis["imports"]),
                "complexity_score": analysis["summary"].get("complexity_score", 0),
                "inheritance_relationships": len(rel_detector.relationships.get("inheritance", [])),
                "function_calls": len(rel_detector.relationships.get("calls", []))
            },
            "timestamp": time.time(),
            "status": "success"
        }
        
        # Optionally include full analysis
        if include_analysis:
            response["full_analysis"] = full_analysis
        
        logger.info(f"Generated {diagram_type} diagram for {file.filename}")
        
        return response
        
    except SyntaxError as e:
        logger.warning(f"Syntax error in {file.filename}: {e}")
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid Python syntax: {e.msg}"
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 encoded text"
        )
    except Exception as e:
        logger.error(f"Error generating diagram for {file.filename}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Diagram generation failed: {str(e)}"
        )


# Legacy endpoint for backward compatibility
@app.post("/analayze")
async def analyze_code_legacy(file: UploadFile = File(...)):
    """Legacy endpoint - redirects to /analyze"""
    return await analyze_code(file)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler with logging"""
    logger.warning(f"HTTP {exc.status_code} error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Handle internal server errors"""
    logger.error(f"Internal server error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "status_code": 500
        }
    )


# For development and testing
if __name__ == "__main__":
    import uvicorn
    import time
    
    logger.info("Starting CodeViz API server...")
    
    # Run with auto-reload for development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )