from datetime import datetime
from random import randint
from typing import Any
from fastapi import FastAPI, HTTPException, Request, Response

app = FastAPI(root_path="/api/v1")

@app.get("/")
async def root():
    return {"message": "Hello World"}


data :Any = [
    {"campaign_id": 1, "name": "First Campaign", "due_date": datetime.now(), "created_at": datetime.now()},
    {"campaign_id": 2, "name": "Sosa Takeover", "due_date": datetime.now(), "created_at": datetime.now()}


]
"""
Campaigns
-campaign_id
-name
-due_date
-created_at
"""

@app.get("/campaigns")
async def read_campaigns():
    return {"campaigns": data}

@app.get("/campaigns/{campaign_id}")
async def read_campaign(campaign_id: int):
    # Search for the campaign
    campaign = next((item for item in data  if item["campaign_id"] == campaign_id), None)
    
    if not campaign:
        # This tells the client "404" specifically
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    return campaign

@app.post("/campaigns",status_code=201)
async def create_campaign(body: dict[str, Any]):
    # Get the JSON body of the request
    
    new : Any = {
        "campaign_id": randint(100, 1000),  # Generate a random campaign_id
        "name": body.get("name"),
        "due_date": body.get("due_date"),
        "created_at": datetime.now()
    }
    
    data.append(new)
    return {"campaign": new}

@app.put("/campaigns/{campaign_id}")
async def update_campaign(campaign_id:  int, body: dict[str, Any]):
    for index, campaign in enumerate(data):
        if campaign["campaign_id"] == campaign_id:
            updated : Any = {
                "campaign_id": campaign_id,
                "name": body.get("name"),
                "due_date": body.get("due_date"),
                "created_at": campaign["created_at"]
            }

            data[index] = updated
            return {"campaign": updated}
    raise HTTPException(status_code=404, detail="Campaign not found")

@app.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int):
    for index, campaign in enumerate(data):
        if campaign["campaign_id"] == campaign_id:
            data.pop(index)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail="Campaign not found")
