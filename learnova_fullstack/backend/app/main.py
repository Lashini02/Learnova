from fastapi import FastAPI, HTTPException as StarletteHTTPException  # type: ignore[import]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from fastapi.exceptions import RequestValidationError  # type: ignore[import]
from fastapi.responses import JSONResponse  # type: ignore[import]
from app.api import auth, profile, crud_routes
from app.db.session import Base, engine, SessionLocal
from app.services.seed import seed_demo_data

app = FastAPI(title="Learnova API", version="1.0.0", description="Backend API for Learnova Student Learning & Task Organizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": f"Validation error: {str(exc)}", "errors": exc.errors()},
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

@app.get("/")
def root():
    return {"app": "Learnova API", "status": "running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(crud_routes.router, prefix="/api")
