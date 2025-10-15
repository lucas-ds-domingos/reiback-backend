from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tomador,documentos,segurado,propostas,gerarpdf, webhokassas, apolices, usuarios, corretor, assesoria, representanteLegal, fiador, ccg, webhokD4sing,dashbord
from fastapi.staticfiles import StaticFiles
import asyncio
import sys

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tomador.router, prefix="/tomador", tags=["Tomador"])
app.include_router(segurado.router, prefix="/segurado", tags=["Segurado"])
app.include_router(propostas.router, prefix="/api", tags=["Propostas"])
app.include_router(gerarpdf.router, prefix="/api/gerar-pdf", tags=["gerar-pdf"])
app.include_router(webhokassas.router, prefix="/api")
app.include_router(apolices.router)
app.include_router(usuarios.router, prefix="/api")
app.include_router(corretor.router, prefix="/api")
app.include_router(assesoria.router, prefix="/api")
app.include_router(representanteLegal.router, prefix="/api")
app.include_router(fiador.router, prefix="/api")
app.include_router(ccg.router, prefix="/api/ccg", tags=["CCG"])
app.include_router(webhokD4sing.router) 
app.include_router(dashbord.router, prefix="/api")
app.include_router(documentos.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")



