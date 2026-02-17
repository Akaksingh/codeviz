import ast

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from generators.diagram_generator import (
     generate_class_diagram,
     generate_dependency_graph,
     generate_summary_text,
)
from parsers.python_parsers import analyze_file
from parsers.relationship_detector import RelationshipDetector


app = FastAPI(
     title="CodeViz API",
     description="Upload Python files and get architecture analysis + diagrams",
     version="1.0.0",
)

app.add_middleware(
     CORSMiddleware,
     allow_origins=["*"],
     allow_methods=["*"],
     allow_headers=["*"],
)


@app.get("/")
def home():
     return {
          "status": "CodeViz API is running!",
          "version": "1.0.0",
          "endpoints": {
               "POST /analyze": "Upload .py file and get structure",
               "POST /diagram": "Upload .py file and get mermaid diagrams",
               "GET /health": "Health check",
          },
     }


@app.get("/health")
def health():
     return {"status": "healthy"}


@app.post("/analyze")
@app.post("/analayze")
async def analyze_code(file: UploadFile):
     if not file.filename or not file.filename.endswith(".py"):
          raise HTTPException(status_code=400, detail="Only .py files are supported")

     try:
          contents = await file.read()
          code = contents.decode("utf-8")

          analysis = analyze_file(code)
          tree = ast.parse(code)
          rel_detector = RelationshipDetector()
          rel_detector.visit(tree)

          return {
               "filename": file.filename,
               "classes": analysis["classes"],
               "functions": analysis["functions"],
               "imports": analysis["imports"],
               "relationships": rel_detector.relationships,
               "summary": analysis["summary"],
          }
     except SyntaxError as error:
          raise HTTPException(status_code=400, detail=f"Invalid Python syntax: {error}")
     except Exception as error:
          raise HTTPException(status_code=500, detail=f"Analysis failed: {error}")


@app.post("/diagram")
async def generate_diagrams(file: UploadFile, diagram_type: str = "class"):
     if not file.filename or not file.filename.endswith(".py"):
          raise HTTPException(status_code=400, detail="Only .py files are supported")

     try:
          contents = await file.read()
          code = contents.decode("utf-8")

          analysis = analyze_file(code)
          tree = ast.parse(code)
          rel_detector = RelationshipDetector()
          rel_detector.visit(tree)

          full_analysis = {**analysis, "relationships": rel_detector.relationships}

          if diagram_type == "class":
               diagram = generate_class_diagram(
                    analysis["classes"],
                    rel_detector.relationships,
               )
          elif diagram_type == "dependency":
               diagram = generate_dependency_graph(
                    analysis["classes"],
                    analysis["imports"],
               )
          else:
               raise HTTPException(
                    status_code=400,
                    detail="diagram_type must be 'class' or 'dependency'",
               )

          summary_text = generate_summary_text(full_analysis)

          return {
               "filename": file.filename,
               "diagram": diagram,
               "summary_text": summary_text,
               "stats": analysis["summary"],
          }
     except SyntaxError as error:
          raise HTTPException(status_code=400, detail=f"Syntax error: {error}")
     except Exception as error:
          raise HTTPException(status_code=500, detail=f"Diagram generation failed: {error}")