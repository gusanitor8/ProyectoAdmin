from fastapi import FastAPI
import logging
import pandas as pd
from datetime import datetime
import os

app = FastAPI()

# -----------------------------------
# Configuración de logging
# -----------------------------------
LOG_FILE = "logs/api.log"
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# -----------------------------------
# “Base de datos” con pandas
# -----------------------------------
DATA_FILE = "data/items.csv"
os.makedirs("data", exist_ok=True)

# Si no existe, crear archivo CSV inicial
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame({"id": [], "name": []})
    df.to_csv(DATA_FILE, index=False)


def load_items():
    return pd.read_csv(DATA_FILE)


def save_item(item_name: str):
    df = load_items()
    new_id = len(df) + 1
    df.loc[len(df)] = [new_id, item_name]
    df.to_csv(DATA_FILE, index=False)
    return {"id": new_id, "name": item_name}


# -----------------------------------
# Endpoints
# -----------------------------------

@app.get("/")
def read_root():
    logger.info("Request to /")
    return {"message": "API funcionando correctamente"}

@app.get("/items")
def get_items():
    logger.info("Request to /items")
    df = load_items()
    return df.to_dict(orient="records")

@app.post("/items")
def create_item(name: str):
    logger.info(f"Creando item: {name}")
    new_item = save_item(name)
    return new_item

@app.get("/health")
def health_check():
    logger.info("Health check recibido")
    return {"status": "ok", "timestamp": datetime.utcnow()}