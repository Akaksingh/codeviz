# CodeViz - Code-to-Architecture Diagram Generator

A production-ready FastAPI backend that analyzes Python code and generates interactive architecture diagrams in Mermaid format.

![CodeViz Demo](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)
![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)

## 🚀 Features

### Core Functionality
- **📁 File Upload** - Accept Python (.py) file uploads via REST API
- **🔍 AST Analysis** - Deep code structure analysis using Python's Abstract Syntax Tree
- **📊 Architecture Diagrams** - Generate multiple diagram types in Mermaid format:
  - **Class Diagrams** - Classes, methods, inheritance relationships
  - **Dependency Graphs** - Import relationships and external dependencies  
  - **Component Diagrams** - High-level architecture overview
  - **Function Call Diagrams** - Function call flow visualization

### Advanced Analysis
- **🔗 Relationship Detection** - Inheritance, composition, function calls
- **📈 Complexity Metrics** - Coupling scores, inheritance depth, complexity analysis
- **🏷️ Pattern Recognition** - Detect MVC, Service Layer, Repository patterns
- **📝 AI-Ready Summaries** - Human-readable architecture descriptions

### Production Features
- **⚡ Async/Await** - High-performance async request handling
- **🛡️ Error Handling** - Comprehensive error handling with proper HTTP codes
- **📋 Input Validation** - File type, size, and syntax validation
- **📊 Logging & Monitoring** - Structured logging with request tracking
- **🧪 Test Coverage** - Comprehensive unit and integration tests

## 🏗️ Architecture

### Project Structure
```
codeviz/
├── main.py                          # FastAPI application and endpoints
├── parsers/
│   ├── __init__.py
│   ├── python_parsers.py           # AST-based code analysis
│   └── relationship_detector.py    # Relationship and pattern detection
├── generators/
│   ├── __init__.py
│   └── diagram_generator.py        # Mermaid diagram generation
├── tests/
│   ├── __init__.py
│   ├── tests_parser.py             # Original test cases
│   └── test_comprehensive.py       # Comprehensive test suite
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

### Data Flow
```
1. Client uploads Python file → FastAPI endpoint
2. File validation (type, size, syntax)
3. AST parsing extracts classes, functions, imports
4. Relationship detector finds inheritance, calls, composition
5. Diagram generator creates Mermaid syntax
6. Return JSON with diagram + analysis metadata
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip or poetry

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Akaksingh/codeviz.git
   cd codeviz
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the development server**
   ```bash
   python main.py
   ```
   
   Or with uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the API**
   - **API Documentation**: http://localhost:8000/docs
   - **Alternative Docs**: http://localhost:8000/redoc  
   - **Health Check**: http://localhost:8000/health

## 📡 API Endpoints

### Core Endpoints

#### `GET /`
**Home page with API information**
```json
{
  "name": "CodeViz API",
  "version": "2.0.0", 
  "description": "Python code architecture analysis",
  "endpoints": {...}
}
```

#### `GET /health`
**Health check for monitoring**
```json
{
  "status": "healthy",
  "timestamp": 1703123456.789,
  "python_version": "3.11.0"
}
```

#### `POST /analyze`
**Comprehensive code analysis**

**Request:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_file.py"
```

**Response:**
```json
{
  "filename": "your_file.py",
  "classes": [
    {
      "name": "MyClass",
      "methods": [
        {
          "name": "__init__",
          "args": [{"name": "param"}],
          "decorators": [],
          "is_async": false,
          "return_type": null
        }
      ],
      "bases": ["BaseClass"],
      "docstring": "Class description"
    }
  ],
  "functions": [...],
  "imports": [...],
  "relationships": {
    "inheritance": [...],
    "calls": [...],
    "composition": [...]
  },
  "summary": {
    "total_classes": 5,
    "complexity_score": 23,
    "inheritance_depth": 3
  }
}
```

#### `POST /diagram`
**Generate Mermaid diagrams**

**Request:**
```bash
curl -X POST "http://localhost:8000/diagram?diagram_type=class&include_analysis=false" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_file.py"
```

**Query Parameters:**
- `diagram_type`: `class` | `dependency` | `component` | `calls`
- `include_analysis`: `true` | `false` (include full analysis data)

**Response:**
```json
{
  "filename": "your_file.py",
  "diagram_type": "class",
  "mermaid_code": "classDiagram\n    Animal <|-- Dog\n    class Dog {\n        +bark()\n    }",
  "summary_text": "This codebase contains 2 classes with inheritance...",
  "stats": {
    "total_classes": 2,
    "complexity_score": 15
  }
}
```

### Diagram Types

#### 1. Class Diagrams (`diagram_type=class`)
Shows classes, methods, and inheritance relationships:
```mermaid
classDiagram
    Animal <|-- Dog
    class Animal {
        +speak()
        +eat()
    }
    class Dog {
        +bark()
        +fetch(item)
    }
```

#### 2. Dependency Graphs (`diagram_type=dependency`)  
Shows import relationships:
```mermaid
graph TD
    A[MyApp] --> B[Python Standard Library]
    A --> C[fastapi]
    A --> D[sqlalchemy]
    B --> B1[os]
    B --> B2[json]
```

#### 3. Component Diagrams (`diagram_type=component`)
High-level architecture overview:
```mermaid
graph TB
    A[Controllers] --> B[Business Logic]
    B --> C[Data Models]
    B --> D[External Dependencies]
```

#### 4. Function Call Diagrams (`diagram_type=calls`)
Function call flow visualization:
```mermaid
graph LR
    main --> create_user
    create_user --> validate_input
    create_user --> save_to_db
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=parsers --cov=generators --cov-report=html

# Run specific test file
python -m pytest tests/test_comprehensive.py -v

# Run original quick tests
python tests/tests_parser.py
```

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: Full pipeline testing
- **Edge Cases**: Empty files, syntax errors, complex inheritance
- **API Tests**: Endpoint validation and error handling

## 🔧 Configuration

### Environment Variables
Create a `.env` file for configuration:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# File Upload Limits  
MAX_FILE_SIZE_MB=10
ALLOWED_EXTENSIONS=.py

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Future: AI Integration
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...

# Future: Database
# DATABASE_URL=postgresql://user:pass@localhost/codeviz
# REDIS_URL=redis://localhost:6379
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud Deployment

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/codeviz
gcloud run deploy codeviz \
  --image gcr.io/PROJECT_ID/codeviz \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Railway
```bash
# Add Railway config
echo 'web: uvicorn main:app --host=0.0.0.0 --port=$PORT' > Procfile
railway login
railway init
railway up
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

### Code Quality
```bash
# Format code
black . --line-length 88

# Lint code  
flake8 . --max-line-length 88

# Type checking
mypy parsers/ generators/ main.py
```

### Adding New Features
1. **New Diagram Types**: Add generators in `generators/diagram_generator.py`
2. **Enhanced Analysis**: Extend parsers in `parsers/python_parsers.py`
3. **New Language Support**: Create new parser modules
4. **AI Integration**: Add AI summary modules

## 📊 Performance Metrics

### Typical Performance
- **Small files** (<100 lines): < 50ms
- **Medium files** (100-1000 lines): < 200ms  
- **Large files** (1000+ lines): < 1s
- **Memory usage**: ~50MB baseline + ~1MB per 1000 lines

### Optimization Features
- Async request handling
- Streaming file processing
- Response caching (ready for Redis)
- Background task support

## 🗺️ Roadmap

### Phase 1: Current (MVP) ✅
- [x] Core AST parsing
- [x] Basic diagram generation
- [x] REST API endpoints
- [x] Comprehensive testing

### Phase 2: Enhanced Analysis (Next)
- [ ] Multi-file project analysis
- [ ] GitHub repository integration
- [ ] Advanced pattern detection
- [ ] Custom diagram styling

### Phase 3: AI Integration
- [ ] Claude/GPT API integration
- [ ] Natural language architecture summaries
- [ ] Code quality recommendations
- [ ] Architectural anti-pattern detection

### Phase 4: Production Scale
- [ ] PostgreSQL data persistence
- [ ] Redis caching layer
- [ ] User authentication
- [ ] Analysis history storage
- [ ] Webhook integrations

### Phase 5: Advanced Features
- [ ] Real-time collaboration
- [ ] Custom analysis rules
- [ ] Integration with IDEs
- [ ] Architectural linting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Akaksingh**
- GitHub: [@Akaksingh](https://github.com/Akaksingh)
- Project: [CodeViz](https://github.com/Akaksingh/codeviz)

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Mermaid.js](https://mermaid.js.org/) - Diagram syntax and rendering
- [Python AST](https://docs.python.org/3/library/ast.html) - Code parsing foundation

---

**⭐ Star this repository if you find it helpful!**