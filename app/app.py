from .controllers import pagos
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origenes_permitidos = [
    "http://localhost:5173",
    "https://aplicacion-ruddy.vercel.app",
]

# 2. Agregamos el middleware a la aplicación
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(pagos.router)