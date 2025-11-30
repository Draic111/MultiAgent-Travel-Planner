# api_server.py
"""
FastAPI backend server for Travel Planner System
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pipeline import run_pipeline
import uvicorn

app = FastAPI(title="Travel Planner API", version="1.0.0")

# Configure CORS - Allow frontend to make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TripConfig(BaseModel):
    """Trip configuration model matching the backend requirements"""
    origin_city: str = Field(..., description="Origin city name")
    destination_city: str = Field(..., description="Destination city name")
    check_in_date: str = Field(..., description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(..., description="Check-out date in YYYY-MM-DD format")
    num_people: int = Field(..., gt=0, description="Number of travelers")
    total_budget: float = Field(..., gt=0, description="Total budget in USD")


class PlanRequest(BaseModel):
    """Request model from frontend (may have different field names)"""
    origin_city: str
    destination_city: str
    departure_date: str  # Frontend sends this as departure_date
    return_date: str  # Frontend sends this as return_date
    num_people: int
    budget: float  # Frontend sends this as budget


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Travel Planner API is running"}


@app.post("/api/plan", response_model=dict)
async def create_travel_plan(request: PlanRequest):
    """
    Create a travel plan based on user input
    
    Frontend sends:
    - departure_date, return_date, budget
    
    Backend needs:
    - check_in_date, check_out_date, total_budget
    
    This endpoint handles the field name mapping.
    """
    try:
        # Map frontend field names to backend field names
        trip_config = {
            "origin_city": request.origin_city,
            "destination_city": request.destination_city,
            "check_in_date": request.departure_date,  # Map departure_date -> check_in_date
            "check_out_date": request.return_date,  # Map return_date -> check_out_date
            "num_people": request.num_people,
            "total_budget": request.budget,  # Map budget -> total_budget
        }
        
        # Run the pipeline
        result = run_pipeline(trip_config, verbose=False)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")


@app.post("/api/plan/verbose", response_model=dict)
async def create_travel_plan_verbose(request: PlanRequest):
    """
    Create a travel plan with detailed execution logs
    """
    try:
        # Map frontend field names to backend field names
        trip_config = {
            "origin_city": request.origin_city,
            "destination_city": request.destination_city,
            "check_in_date": request.departure_date,
            "check_out_date": request.return_date,
            "num_people": request.num_people,
            "total_budget": request.budget,
        }
        
        # Run the pipeline with verbose output
        result = run_pipeline(trip_config, verbose=True)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

