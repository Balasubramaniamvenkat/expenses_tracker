"""
Main FastAPI application for Family Finance Tracker backend.
"""
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Try to import the categories router
categories_router = None
categories_import_error = None
try:
    from .categories import router as categories_router
    print("✓ Successfully imported categories router")
    print(f"  Router prefix: {categories_router.prefix}")
    print(f"  Router has {len(categories_router.routes)} routes")
except Exception as e:
    categories_import_error = str(e)
    print(f"⚠ Warning: Could not import categories router: {e}")
    print("  Creating fallback router for categories...")
    
    # Create fallback router with the CORRECT prefix - this is critical
    categories_router = APIRouter(prefix="/api/categories", tags=["categories"])

    @categories_router.get("/health")
    async def fallback_categories_health():
        return {
            "status": "unavailable",
            "service": "Categories API",
            "error": categories_import_error
        }
    
    @categories_router.get("/analytics")
    async def fallback_categories_analytics():
        """Fail explicitly instead of serving sample figures as real analytics."""
        raise HTTPException(
            status_code=503,
            detail=f"Categories analytics unavailable: {categories_import_error}"
        )
    
    print(f"  Fallback router created with prefix: {categories_router.prefix}")
    print(f"  Fallback router has {len(categories_router.routes)} routes")

# Create FastAPI app
app = FastAPI(
    title="Family Finance Tracker API",
    description="Backend API for Family Finance Tracker Angular Application",
    version="1.0.0"
)

# Configure CORS for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Angular development server
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Try to import other routers
transactions_router = None
upload_router = None
dashboard_router = None

try:
    from .transactions import router as transactions_router
    print("✓ Included transactions router")
except ImportError:
    print("⚠ transactions router not available")

try:
    from .upload import router as upload_router
    print("✓ Included upload router")
except ImportError:
    print("⚠ upload router not available")

try:
    from .dashboard import router as dashboard_router
    print("✓ Included dashboard router")
except ImportError as e:
    print(f"⚠ dashboard router not available: {e}")

# Try to import categories hierarchy router for drill-down support
categories_hierarchy_router = None
try:
    from .categories_hierarchy import router as categories_hierarchy_router
    print("✓ Included categories hierarchy router (drill-down support)")
except ImportError as e:
    print(f"⚠ categories hierarchy router not available: {e}")

# Try to import AI chat router
ai_router = None
try:
    from .ai_chat import router as ai_router
    print("✓ Included AI chat router")
except ImportError as e:
    print(f"⚠ AI chat router not available: {e}")

# Include the categories router (already has correct prefix)
app.include_router(categories_router)

# Include categories hierarchy router for drill-down charts
if categories_hierarchy_router:
    app.include_router(categories_hierarchy_router)
    print("✓ Categories Hierarchy API available at /api/categories/hierarchy")

# Include dashboard router
if dashboard_router:
    app.include_router(dashboard_router)

# Include other routers only if they exist
if transactions_router:
    app.include_router(transactions_router, prefix="/api")
if upload_router:
    app.include_router(upload_router, prefix="/api")
if ai_router:
    app.include_router(ai_router)
    print("✓ AI Chat API available at /api/ai/*")

@app.get("/")
async def root():
    return {
        "message": "Family Finance Tracker API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Family Finance Tracker API"}

# Print available routes for diagnostics
print(f"✓ App configured with {len(app.routes)} total routes")
print("✓ Available endpoints:")
print("  - http://localhost:8000/")
print("  - http://localhost:8000/health")
print("  - http://localhost:8000/docs")
if hasattr(categories_router, 'prefix') and categories_router.prefix:
    print(f"  - http://localhost:8000{categories_router.prefix}/health")
    print(f"  - http://localhost:8000{categories_router.prefix}/analytics")

# Add server runner for development
if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Family Finance Tracker API Server...")
    print("API Documentation: http://localhost:8000/docs")
    print("Categories API: http://localhost:8000/api/categories/analytics")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        reload_dirs=["."]
    )
