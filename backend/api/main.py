# main.py
# FastAPI backend - the bridge between React frontend and FEA solver

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil
import uuid

from solver.pipeline import run_full_analysis

# Initialize FastAPI app
app = FastAPI(title="FEA Platform API", version="1.0.0")

# CORS = Cross-Origin Resource Sharing
# React runs on port 3000, FastAPI on port 8000
# Without this, browser blocks requests between them
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder to store uploaded files
UPLOAD_DIR = r"C:\Users\aysal\Desktop\AI_Component_Analyzer\uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ── Data models ───────────────────────────────────────
# Pydantic models define what data the API expects to receive

class MaterialInput(BaseModel):
    name: str           = "STEEL"
    youngs_modulus: float = 210000.0
    poisson_ratio: float  = 0.3
    density: float        = 7.85e-9
    yield_strength: float = 235.0

class AnalysisInput(BaseModel):
    file_id: str              # ID of uploaded file
    material: MaterialInput
    force_z: float = -10000.0 # Force in Newtons
    mesh_size: float = 8.0    # Mesh size in mm


# ── Endpoints ─────────────────────────────────────────
# Endpoint = a URL that does something when called

@app.get("/")
def root():
    """Health check - confirms API is running"""
    return {"status": "FEA Platform API is running"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Receives a STEP file from the browser and saves it.
    Returns a file_id to reference it later.
    """
    
    # Validate file extension
    if not file.filename.lower().endswith(('.step', '.stp')):
        raise HTTPException(400, "Only STEP files (.step, .stp) are accepted")
    
    # Generate unique ID for this file
    file_id   = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.step")
    
    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    
    return {
        "file_id"  : file_id,
        "filename" : file.filename,
        "size_kb"  : round(file_size / 1024, 1),
        "message"  : "File uploaded successfully"
    }


@app.post("/analyze")
async def analyze(data: AnalysisInput):
    """
    Runs FEA analysis on an uploaded file.
    Returns stress, displacement and safety factor results.
    """
    
    file_path = os.path.join(UPLOAD_DIR, f"{data.file_id}.step")
    
    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found: {data.file_id}")
    
    output_dir = os.path.join(UPLOAD_DIR, data.file_id)
    os.makedirs(output_dir, exist_ok=True)
    
    material = {
        "name"           : data.material.name,
        "youngs_modulus" : data.material.youngs_modulus,
        "poisson_ratio"  : data.material.poisson_ratio,
        "density"        : data.material.density,
        "yield_strength" : data.material.yield_strength,
    }
    
    loads = {"force_z": data.force_z}
    
    try:
        results = run_full_analysis(
            step_file  = file_path,
            output_dir = output_dir,
            material   = material,
            loads      = loads,
            mesh_size  = data.mesh_size,
        )
        
        if results is None:
            raise HTTPException(500, "Analysis failed")
        
        return {
            "status"           : "success",
            "num_nodes"        : results["num_nodes"],
            "num_elements"     : results["num_elements"],
            "max_displacement" : round(results["max_displacement"], 6),
            "max_von_mises"    : round(results["max_von_mises"], 2),
            "safety_factor"    : round(results["safety_factor"], 2),
            "assessment"       : results["assessment"],
        }
        
    except Exception as e:
        raise HTTPException(500, f"Analysis error: {str(e)}")


@app.get("/materials")
def get_materials():
    """Returns list of available materials"""
    return {
        "materials": [
            {"name": "Structural Steel S235",  "E": 210000, "nu": 0.3,  "rho": 7.85e-9, "fy": 235},
            {"name": "Structural Steel S355",  "E": 210000, "nu": 0.3,  "rho": 7.85e-9, "fy": 355},
            {"name": "Aluminum 6061-T6",       "E": 68900,  "nu": 0.33, "rho": 2.70e-9, "fy": 276},
            {"name": "Aluminum 7075-T6",       "E": 71700,  "nu": 0.33, "rho": 2.81e-9, "fy": 503},
            {"name": "Titanium Ti-6Al-4V",     "E": 113800, "nu": 0.34, "rho": 4.43e-9, "fy": 880},
            {"name": "Stainless Steel 316L",   "E": 193000, "nu": 0.27, "rho": 8.00e-9, "fy": 170},
        ]
    }