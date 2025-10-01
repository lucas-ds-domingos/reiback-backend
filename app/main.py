from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tomador, segurado,propostas,gerarpdf, webhokassas, apolices, usuarios
from fastapi.staticfiles import StaticFiles
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

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

app.mount("/static", StaticFiles(directory="app/static"), name="static")



