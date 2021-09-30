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
    return templates.TemplateResponse('inde.html', context={'request': request,"url":URL})

@app.get("/warehouse", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('addunit.html', context={'request': request,"url":URL})

@app.get("/production", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse('subunit.html', context={'request': request,"url":URL}) 

@app.get("/data" )
def data(request: Request):
    dats = []
    query =  'select * from main order by qty asc'
    cursor = conn.execute(query)
    for row in cursor:
        dats.append(dict(partname=row[0],qty=row[1]))

    return dats


class addreq(BaseModel):
    partname:str

class subreq(BaseModel):
    partname:str

@app.post("/add" )
def add(request: Request,data:addreq):
    part = data.partname.upper()
    query =  'select qty from main WHERE partname="'+part+'" order by qty asc'
    cursor = conn.execute(query)
    check = cursor.fetchall()
    if len(check)==0:
        query =  'INSERT INTO main(partname,qty) VALUES("'+part+'",1)'
        cursor = conn.execute(query)
        conn.commit()
    else:
        query =  'select qty from main WHERE partname="'+part+'" order by qty asc'
        cursor = conn.execute(query)
        for row in cursor:
            exqty = row[0]
        
        nwqty = exqty+1
        query =  'update main set qty="'+str(nwqty)+'" WHERE partname="'+part+'"'
        cursor = conn.execute(query)
        conn.commit()
    return {"success":"Part Loaded"}

@app.post("/subb")
def subb(request: Request,data:subreq):
    part = data.partname.upper()
    query =  'select qty from main WHERE partname="'+part+'" order by qty asc'
    cursor = conn.execute(query)
    check = cursor.fetchall()
    if len(check)==0:
        return {"success":"No Part Found"}

    else:
        query =  'select qty from main WHERE partname="'+part+'" order by qty asc'
        cursor = conn.execute(query)
        for row in cursor:
            exqty = row[0]
        
        nwqty = exqty-1
        query =  'update main set qty="'+str(nwqty)+'" WHERE partname="'+part+'"'
        cursor = conn.execute(query)
        conn.commit()
    return {"success":"Part Consumed"}





 

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

