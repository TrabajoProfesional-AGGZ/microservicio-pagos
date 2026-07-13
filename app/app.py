from .controllers import pagos_controller as pagos
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SocioUnido - Microservicio de Pagos}",
    description="Microservicio encargado de procesar pagos y recibir notificaciones de Mercado Pago.",
    version="1.0.0",
    openapi_url="/api/v1/openapi/pagos.json"
)

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