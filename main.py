import base64
from datetime import datetime, timezone
import json
from typing import Annotated, Any, Generic, Optional, TypeVar
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.concurrency import asynccontextmanager
from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Session, create_engine, func, select

class Campaign(SQLModel, table=True):
    campaign_id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    due_date: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

class CampaignCreate(SQLModel):
    name: str
    due_date: datetime | None = None

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables(): 
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        if not session.exec(select(Campaign)).first():
            session.add_all([Campaign(name = "Sosa Rise", due_date = datetime.now(timezone.utc)),
                             Campaign(name = "Sosa Takeover", due_date = datetime.now(timezone.utc))])
            session.commit()
    yield
    
app = FastAPI(root_path="/api/v1", lifespan=lifespan)

@app.get("/")
async def root():
   return {"message": "Hello World"}

"""
Campaigns
-campaign_id
-name
-due_date
-created_at
"""
T = TypeVar("T")
class Response(BaseModel, Generic[T]):
    data: T

#@app.get("/campaigns", response_model=Response[list[Campaign]])
#async def read_campaigns(session: SessionDep, page: int = Query(1, ge=1)):
#    print(f"Page: {page}")
#    limit = 20
#    offset = (page - 1) * limit
#    data = session.exec(select(Campaign))(Campaign.campaign_id).offset(offset).limit(limit).all() 
#    return {"data": data}

class PaginationResponse(BaseModel, Generic[T]):
    data: T
    next: Optional[str]
    #prev: Optional[str]

def encode_cursor(value):
    raw = json.dumps({"id": value})
    return base64.urlsafe_b64encode(raw.encode()).decode()

def decode_cursor(cursor):
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    payload = json.loads(raw)
    return payload.get("id")

@app.get("/campaigns", response_model=PaginationResponse[list[Campaign]])
async def read_campaigns(request: Request, session: SessionDep, cursor: Optional[str] = Query(None), limit: int = Query(20, ge=1)):
    
    # Build the query inside the select()
    #query = select(Campaign).order_by(Campaign.campaign_id).offset(offset).limit(limit)
    
    #data = session.exec(query).all()
    #base_url = str(request.url).split("?")[0]#
    #next_url = f"{base_url}?offset={offset + limit}&page_size={limit}" 

    #if offset > 0:
    #    prev_url = f"{base_url}?offset={max(0, offset - limit)}&page_size={limit}"
    #else:
    #    prev_url = None#
    
    cursor_id = 0
    if cursor:
        cursor_id = decode_cursor(cursor)

    data = session.exec(select(Campaign).order_by(Campaign.campaign_id).where(Campaign.campaign_id > cursor_id).limit(limit+1)).all()

    base_url = str(request.url).split("?")[0]

    next_url = None

    if len (data) > limit:
        next_cursor = encode_cursor(data[:limit][-1].campaign_id)
        next_url = f"{base_url}?cursor={next_cursor}&limit={limit}" 
    

    return {"data": data[:limit],
            "next": next_url, 
            #"prev": prev_url
            
            }

#@app.get("/campaigns", response_model=PaginationResponse[list[Campaign]])
#async def read_campaigns(request: Request, session: SessionDep, offset: int = Query(0, ge=0),
#                            limit: int = Query(20, ge=1)):
#    
#    # Build the query inside the select()
#    query = select(Campaign).order_by(Campaign.campaign_id).offset(offset).limit(limit)
#    data = session.exec(query).all()
#    
#    base_url = str(request.url).split("?")[0]#

#    next_url = f"{base_url}?offset={offset + limit}&page_size={limit}" #

#    if offset > 0:
#        prev_url = f"{base_url}?offset={max(0, offset - limit)}&page_size={limit}"
#    else:
#        prev_url = None#

#    return {"data": data,
#            "next": next_url, 
#            "prev": prev_url
#            
#            }

#@app.get("/campaigns")
#async def read_campaigns():
#    return {"campaigns": data}
#

@app.get("/campaigns/{id}", response_model=Response[Campaign])
async def read_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"data": data}

#@app.get("/campaigns/{campaign_id}")
#async def read_campaign(campaign_id: int):
#    # Search for the campaign
#    campaign = next((item for item in data  if item["campaign_id"] == campaign_id), None)
#    
#    if not campaign:
#        # This tells the client "404" specifically
#        raise HTTPException(status_code=404, detail="Campaign not found")
#        
#    return campaign

@app.post("/campaigns", status_code=201, response_model=Response[Campaign])
async def create_campaign(campaign: CampaignCreate, session: SessionDep):
    db_campaign = Campaign.model_validate(campaign)
    session.add(db_campaign)
    session.commit()
    session.refresh(db_campaign)
    return {"data": db_campaign}

#@app.post("/campaigns",status_code=201)
#async def create_campaign(body: dict[str, Any]):
#    # Get the JSON body of the request
#    
#    new : Any = {
#        "campaign_id": randint(100, 1000),  # Generate a random campaign_id
#        "name": body.get("name"),
#        "due_date": body.get("due_date"),
#        "created_at": datetime.now()
#    }
#    
#    data.append(new)
#    return {"campaign": new}
#

@app.put("/campaigns/{id}", response_model=Response[Campaign])
async def update_campaign(id: int, campaign: CampaignCreate, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    data.name = campaign.name
    data.due_date = campaign.due_date
    session.add(data)
    session.commit()
    session.refresh(data)
    return {"data": data}
   
#@app.put("/campaigns/{campaign_id}")
#async def update_campaign(campaign_id:  int, body: dict[str, Any]):
#    for index, campaign in enumerate(data):
#        if campaign["campaign_id"] == campaign_id:
#            updated : Any = {
#                "campaign_id": campaign_id,
#                "name": body.get("name"),
#                "due_date": body.get("due_date"),
#                "created_at": campaign["created_at"]
#            }
#
#            data[index] = updated
#            return {"campaign": updated}
#    raise HTTPException(status_code=404, detail="Campaign not found")
#

@app.delete("/campaigns/{id}", status_code=204)
async def delete_campaign(id: int, session: SessionDep):
    data = session.get(Campaign, id)
    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    session.delete(data)
    session.commit()
    return Response(status_code=204)

#@app.delete("/campaigns/{campaign_id}")
#async def delete_campaign(campaign_id: int):
#    for index, campaign in enumerate(data):
#        if campaign["campaign_id"] == campaign_id:
#            data.pop(index)
#            return Response(status_code=204)
#    raise HTTPException(status_code=404, detail="Campaign not found")
