from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import tomador, segurado,propostas,gerarpdf
from fastapi.staticfiles import StaticFiles
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


app = FastAPI()

# Configuração do CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(tomador.router, prefix="/tomador", tags=["Tomador"])
app.include_router(segurado.router, prefix="/segurado", tags=["Segurado"])
app.include_router(propostas.router, prefix="/api", tags=["Propostas"])
app.include_router(gerarpdf.router, prefix="/api/gerar-pdf", tags=["gerar-pdf"])


app.mount("/static", StaticFiles(directory="app/static"), name="static")



