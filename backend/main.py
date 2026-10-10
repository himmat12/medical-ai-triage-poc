import sys
import os
from pathlib import Path

# Adding the current directory to Python path so imports work
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Importing your FastAPI app from app/main.py
try:
    from app.main import app

    print("✅ Successfully imported FastAPI app from app.main")
except ImportError as e:
    print(f"❌ Failed to import FastAPI app: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")

    # Trying alternative import paths
    try:
        sys.path.insert(0, f"{current_dir}/backend")
        from app.main import app

        print("✅ Successfully imported FastAPI app using alternative path")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        raise


def predict():
    """Health check endpoint for Cerebrium"""
    return {"status": "Backend API is running", "app": "FastAPI"}


# Exporting the FastAPI app for uvicorn
__all__ = ["app"]

# for local testing
if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting FastAPI backend locally...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
