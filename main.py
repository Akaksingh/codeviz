from fastapi import FastAPI , UploadFile
import ast #pythons built in abstract syntax tree module
from typing import List , Dict
app = FastAPI() #creates the api instance 

class CodeAnalyzer(ast.NodeVisitor):
     def __init__(self):
          self.classes = []
          self.functions = []
          self.imports = []
     def visit_ClassDef(self , node):
          class_info = {
               "name": node.name , 
               "methods": [m.name for m in node.body if isinstance(m , ast.FunctionDef)] ,
               "line": node.lineno
          }
          self.classes.append(class_info)
          self.generic_visit(node) 

     def visit_FunctionDef(self , node):
           self.functions.append({
                 "name": node.name , 
                 "line": node.lineno
           })   
           self.generic_visit(node) 
     def visit_Import(self , node):
          for alias in node.names:
               self.imports.append(alias.name)
            self.generic_visit(node)
     def visit_ImportFrom(self , node):
          module = node.module or ""
          for alias in node.names:
                self.imports.append(f"{module}.{alias.name}")
          self.generic_visit(node=)           


@app.post("/analyze") #URL endpoint of the post endpoint , where URL= analyze
async def analyze_code(file: UploadFile): # as file reading is asynchronous 
     contents  = await file.read() # read the contents of the uploaded file
     # content is in bytes ut ast.parse nees strings 
     tree = ast.parse(contents.decode("utf-8"))
     #we will use the ast module to parse the code and extarct the function names and their arguments
     analyzer = CodeAnalyzer()
     analyzer.visit(tree)
     return {
        "classes": analyzer.classes,
        "functions": analyzer.functions,
        "imports": analyzer.imports,
        "summary": {
            "total_classes": len(analyzer.classes),
            "total_functions": len(analyzer.functions),
            "total_imports": len(analyzer.imports)
        }
    }

      
@app.get("/")
def home():# when someone visits the root URL of the API , this function will be called and it will return a simple message indicating that the API is running
     return{"status":"CodeViz API is running!Wollah"}
