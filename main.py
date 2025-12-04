from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import os
import uuid

app = FastAPI()

# ============================
#  CORS (importante si usarás web)
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
#  Cargar modelo YOLO (una vez)
# ============================
model = YOLO("best.pt")

# Nombres de clases según tu YAML
class_names = ['floración', 'fruto_verde', 'fruto_blanco', 'casi_madura', 'madura']


# ============================
#      ENDPOINT PREDICT
# ============================
@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    # Guardar archivo temporal con nombre único
    temp_name = f"temp_{uuid.uuid4()}.jpg"
    with open(temp_name, "wb") as f:
        f.write(await file.read())

    # Hacer predicción
    results = model(temp_name)[0]

    # Contar detecciones
    counts = {name: 0 for name in class_names}

    for cls_id in results.boxes.cls:
        cls_id = int(cls_id)
        if cls_id < len(class_names):
            counts[class_names[cls_id]] += 1

    # Eliminar archivo temporal
    if os.path.exists(temp_name):
        os.remove(temp_name)

    # ============================
    #   LÓGICA DE ETAPA FENOLÓGICA
    # ============================
    flores = counts['floración']
    verdes = counts['fruto_verde']
    blancos = counts['fruto_blanco']
    casi = counts['casi_madura']
    maduras = counts['madura']

    total_frutos = verdes + blancos + casi + maduras

    if flores + total_frutos == 0:
        etapa = "Desarrollo vegetativo"
    elif flores > total_frutos:
        etapa = "Floración"
    elif flores > 0 and verdes > flores:
        etapa = "Floración - inicio de fructificación"
    elif verdes + blancos > flores and casi + maduras <= flores:
        etapa = "Fructificación"
    elif casi + maduras > verdes + blancos:
        etapa = "Madurez"
    else:
        etapa = "Etapa no definida claramente"

    return {
        "counts": counts,
        "etapa_fenologica": etapa
    }


# ============================
#      ENDPOINT ROOT
# ============================
@app.get("/")
def root():
    return {"message": "API YOLO de fresas funcionando correctamente"}


