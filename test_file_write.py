"""
Quick test to verify file writing works correctly
"""
import json
from pathlib import Path

# Get the data directory path (same way as summary_agent.py)
data_dir = Path(__file__).parent / "backend" / "data"
data_dir.mkdir(exist_ok=True)

exec_summary_path = data_dir / "executive_summary.txt"
summaries_path = data_dir / "summaries.json"

print(f"📁 Data directory: {data_dir}")
print(f"📁 Absolute path: {data_dir.resolve()}")
print(f"📄 Executive summary path: {exec_summary_path}")
print(f"📄 Summaries JSON path: {summaries_path}")
print()

# Test 1: Write executive summary
print("🔄 Test 1: Writing executive summary...")
test_executive_content = """FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.

Key Features:
- Fast: Very high performance, on par with NodeJS and Go
- Fast to code: Increase the speed to develop features by about 200% to 300%
- Fewer bugs: Reduce about 40% of human (developer) induced errors
- Intuitive: Great editor support with auto-completion
- Easy: Designed to be easy to use and learn
- Short: Minimize code duplication
- Robust: Get production-ready code with automatic interactive documentation
- Standards-based: Based on the open standards for APIs: OpenAPI and JSON Schema

This is a TEST executive summary to verify file writing works correctly.
"""

try:
    with open(exec_summary_path, "w", encoding="utf-8") as f:
        f.write(test_executive_content)
    print(f"✅ Executive summary written successfully!")
    print(f"   File size: {exec_summary_path.stat().st_size} bytes")
except Exception as e:
    print(f"❌ Error writing executive summary: {e}")

print()

# Test 2: Write summaries JSON
print("🔄 Test 2: Writing summaries JSON...")
test_summaries = {
    "first-steps": "FastAPI allows you to create APIs quickly with automatic interactive documentation. Use decorators like @app.get() and @app.post() to define endpoints.",
    "path-params": "Path parameters are defined in the route path using curly braces. FastAPI automatically validates and converts types.",
    "query-params": "Query parameters are optional values in the URL query string. They provide filtering and pagination capabilities.",
    "request-body": "Request bodies use Pydantic models for automatic validation and serialization. FastAPI handles JSON conversion automatically.",
    "response-model": "Response models define the structure of API responses using Pydantic. Enables automatic validation and documentation."
}

try:
    with open(summaries_path, "w", encoding="utf-8") as f:
        json.dump(test_summaries, f, indent=2, ensure_ascii=False)
    print(f"✅ Summaries JSON written successfully!")
    print(f"   File size: {summaries_path.stat().st_size} bytes")
    print(f"   Number of sections: {len(test_summaries)}")
except Exception as e:
    print(f"❌ Error writing summaries JSON: {e}")

print()

# Test 3: Read back and verify
print("🔄 Test 3: Reading back to verify...")
try:
    with open(exec_summary_path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"✅ Executive summary read back: {len(content)} characters")
    print(f"   First 100 chars: {content[:100]}...")
except Exception as e:
    print(f"❌ Error reading executive summary: {e}")

try:
    with open(summaries_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"✅ Summaries JSON read back: {len(data)} sections")
    print(f"   Sections: {list(data.keys())}")
except Exception as e:
    print(f"❌ Error reading summaries JSON: {e}")

print()
print("=" * 60)
print("✅ File write test complete!")
print("=" * 60)
print()
print("Now check the files:")
print(f"   cat {exec_summary_path}")
print(f"   cat {summaries_path}")
