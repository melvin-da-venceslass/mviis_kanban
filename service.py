from os import curdir
from sqlite3.dbapi2 import Cursor
import uvicorn
from typing import Optional
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import json
import sqlite3
conn = sqlite3.connect('test.db',check_same_thread=False)
app = FastAPI(title='KANBAN_APP', version="v1.0", description="A MVIIS_MAKE", docs_url=None, redoc_url=None)
#URL = "http://localhost:5052"
URL = "https://mviis-kanban-app.herokuapp.com"

origins = [
    "https://localhost", "http://localhost",
    "https://localhost:5052", "http://localhost:5052",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class errorClass(BaseModel):
    version:str="1.0"
    status:str="failed"
    remarks:str
    errorType:str
    errorCode:Optional[str]=None

layer_4 = errorClass

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('home.html', context={'request': request,"url":URL})

@app.get("/production", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('production.html', context={'request': request,"url":URL})

@app.get("/delivery", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('delivery.html', context={'request': request,"url":URL})

@app.get("/warehouse", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('dispatch.html', context={'request': request,"url":URL})

@app.get("/inventory", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('inventory.html', context={'request': request,"url":URL}) 

@app.get("/data" )
def data(request: Request):
    dats = []
    query = """SELECT part_master.partname,part_master.min,part_master.max,COUNT(CASE WHEN stage IN ("TRANSIST")   THEN 1 ELSE NULL END) AS trans, 
       COUNT(CASE WHEN stage IN ("PRODUCTION") THEN 1 ELSE NULL END) AS prod,
	   COUNT(CASE WHEN stage IN ("WAREHOUSE") THEN 1 ELSE NULL END) AS wh,
	   COUNT(CASE WHEN stage IN ("INVENTORY") THEN 1 ELSE NULL END) AS inv FROM main INNER JOIN part_master on main.partname=part_master.id GROUP BY  part_master.partname"""
    cursor = conn.execute(query)
    for row in cursor:
        dats.append(dict(part=row[0],min=row[1],max=row[2],tqty=row[3],pqty=row[4]))

    
    return dats


class addreq(BaseModel):
    uniqname:str
class subreq(BaseModel):
    partname:str

@app.post("/dispatch" )
def add(request: Request,data:addreq):
    try:
        uniq  = data.uniqname.upper()
        query =  f'SELECT * from main WHERE unique_id="{uniq}" AND stage="INVENTORY" '
        cursor = conn.execute(query)
        check = cursor.fetchall()
        if len(check)>0:
            query = f'UPDATE main set stage="TRANSIST" where unique_id="{uniq}"'
            cursor = conn.execute(query)
            conn.commit()
            return {"status":"Dispatch Success!"}
        else:
            query =  f'SELECT stage from main WHERE unique_id="{uniq}"'
            cursor = conn.execute(query)
            for each in cursor:
                location = each[0]
            return {"status":f"Dispatch Failed #location: {location}"}
    except:
        return{"status":"Invalid Operation"}

@app.post("/deliver" )
def add(request: Request,data:addreq):
    try:
        uniq  = data.uniqname.upper()
        query =  f'SELECT * from main WHERE unique_id="{uniq}" AND stage="TRANSIST" '
        cursor = conn.execute(query)
        check = cursor.fetchall()
        if len(check)>0:
            query = f'UPDATE main set stage="PRODUCTION" where unique_id="{uniq}"'
            cursor = conn.execute(query)
            conn.commit()
            return {"status":"Delivery Success!"}
        else:
            query =  f'SELECT stage from main WHERE unique_id="{uniq}"'
            cursor = conn.execute(query)
            for each in cursor:
                location = each[0]
            return {"status":f"Delivery Failed #location: {location}"}
    except:
        return{"status":"Invalid Operation"}


@app.post("/consume" )
def add(request: Request,data:addreq):
    try:
        uniq  = data.uniqname.upper()
        query =  f'SELECT * from main WHERE unique_id="{uniq}" AND stage="PRODUCTION" '
        cursor = conn.execute(query)
        check = cursor.fetchall()
        if len(check)>0:
            query = f'UPDATE main set stage="CONSUMED" where unique_id="{uniq}"'
            cursor = conn.execute(query)
            conn.commit()
            return {"status":"Consumption Success!"}
        else:
            query =  f'SELECT stage from main WHERE unique_id="{uniq}"'
            cursor = conn.execute(query)
            for each in cursor:
                location = each[0]
            return {"status":f"Consumption Failed #location: {location}"}
    except:
        return{"status":"Invalid Operation"}


@app.post("/store" )
def add(request: Request,data:addreq):
    try:
        uniq  = data.uniqname.upper()
        query =  f'SELECT * from main WHERE unique_id="{uniq}" '
        cursor = conn.execute(query)
        check = cursor.fetchall()
        if len(check)>0:
            query = f'UPDATE main set stage="INVENTORY" where unique_id="{uniq}"'
            cursor = conn.execute(query)
            conn.commit()
            return {"status":"Stored to Inventory Success!"}
        else:
            query =  f'SELECT stage from main WHERE unique_id="{uniq}"'
            cursor = conn.execute(query)
            for each in cursor:
                location = each[0]
            return {"status":f"Invalid UID"}
    except:
        return{"status":"Invalid Operation"}






 

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    resp = dict(status="failed",remarks=str(exc),errorCode="422",errorType="Validation Error")
    resp = dict(layer_4(**resp))
    return JSONResponse(status_code=422,content=resp)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return templates.TemplateResponse('404.html', status_code=404,context={'request': request})

if __name__ == "__main__":
    uvicorn.run("service:app", reload=True, host='localhost', port=5052, workers=1)

