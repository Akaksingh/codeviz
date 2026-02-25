#!/usr/bin/env python3
"""
Quick test script for CodeViz API
Run this to test all endpoints automatically
"""

import requests
import json
import time
import os

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    print("✅ Health check passed")

def test_home():
    """Test home endpoint"""
    print("🔍 Testing home endpoint...")
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    print("✅ Home endpoint passed")

def test_analyze():
    """Test analyze endpoint with sample file"""
    print("🔍 Testing analyze endpoint...")
    
    # Create sample Python file
    sample_code = '''
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return f"{self.name} says Woof!"

def create_pet(name: str) -> Dog:
    return Dog(name)

import os
from typing import List
'''
    
    with open("temp_test.py", "w") as f:
        f.write(sample_code)
    
    try:
        with open("temp_test.py", "rb") as f:
            files = {"file": ("temp_test.py", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/analyze", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify analysis results
        assert "classes" in data
        assert "functions" in data
        assert "imports" in data
        assert len(data["classes"]) == 2  # Animal, Dog
        assert len(data["functions"]) == 1  # create_pet
        
        print(f"✅ Analysis passed - {len(data['classes'])} classes, {len(data['functions'])} functions")
        
    finally:
        os.remove("temp_test.py")

def test_diagram_generation():
    """Test diagram generation"""
    print("🔍 Testing diagram generation...")
    
    sample_code = '''
class Shape:
    def area(self):
        pass

class Rectangle(Shape):
    def area(self):
        return self.width * self.height

import math
'''
    
    with open("temp_diagram.py", "w") as f:
        f.write(sample_code)
    
    try:
        # Test class diagram
        with open("temp_diagram.py", "rb") as f:
            files = {"file": ("temp_diagram.py", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/diagram?diagram_type=class", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "mermaid_code" in data
        assert "classDiagram" in data["mermaid_code"]
        assert "Shape <|-- Rectangle" in data["mermaid_code"]
        
        print("✅ Class diagram generation passed")
        
        # Test dependency diagram
        with open("temp_diagram.py", "rb") as f:
            files = {"file": ("temp_diagram.py", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/diagram?diagram_type=dependency", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "mermaid_code" in data
        assert "graph TD" in data["mermaid_code"]
        
        print("✅ Dependency diagram generation passed")
        
    finally:
        os.remove("temp_diagram.py")

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("🔍 Testing error handling...")
    
    # Test invalid file type
    with open("test.txt", "w") as f:
        f.write("This is not Python code")
    
    try:
        with open("test.txt", "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/analyze", files=files)
        
        assert response.status_code == 400
        print("✅ Invalid file type error handling passed")
        
    finally:
        os.remove("test.txt")
    
    # Test syntax error
    broken_code = '''
class BrokenClass
    def missing_colon()
        return "error"
'''
    
    with open("broken.py", "w") as f:
        f.write(broken_code)
    
    try:
        with open("broken.py", "rb") as f:
            files = {"file": ("broken.py", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/analyze", files=files)
        
        assert response.status_code == 400
        assert "syntax" in response.json()["detail"].lower()
        print("✅ Syntax error handling passed")
        
    finally:
        os.remove("broken.py")

def main():
    """Run all tests"""
    print("🚀 Starting CodeViz API Tests...\n")
    
    try:
        test_health()
        test_home()
        test_analyze()
        test_diagram_generation()
        test_error_handling()
        
        print("\n🎉 All tests passed! Your CodeViz API is working correctly.")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running on http://localhost:8000")
        print("   Start it with: python main.py")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()