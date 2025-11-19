import os
import time
import json
from datetime import datetime, timezone
from typing import List, Optional, Union

from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, Field

from sqlalchemy import (
    create_engine, Column, Integer, String,
    Text, DateTime, ForeignKey
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session

import logging

# ------------------------------------------------
# Configuración básica
# ------------------------------------------------

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://jacks:secret@localhost:5432/jacks_cave"
)

LOG_FILE = "logs/api.log"
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(message)s"  # el mensaje será JSON
)

logger = logging.getLogger("jacks_cave_logger")
SERVICE_NAME = "jacks-cave-api"

app = FastAPI(title="Jack's Cave API", version="1.0")

# ------------------------------------------------
# SQLAlchemy
# ------------------------------------------------
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ------------------------------------------------
# Modelos de BD
# ------------------------------------------------

class AuthorDB(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    bio = Column(Text, nullable=True)
    role = Column(String(50), nullable=False, default="student")

    articles = relationship("ArticleDB", back_populates="author")


class ArticleDB(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default="blog")
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=False)
    tags = Column(String(255), nullable=True)  # almacenamos "tag1,tag2"
    published_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

    author = relationship("AuthorDB", back_populates="articles")

# Crear tablas al inicio (para el proyecto está bien así)
Base.metadata.create_all(bind=engine)

# ------------------------------------------------
# Función de carga inicial (seed)
# ------------------------------------------------

def seed_db():
    db = SessionLocal()
    try:
        # Si ya hay autores, asumimos que la BD está poblada y no repetimos
        if db.query(AuthorDB).count() > 0:
            return

        # Autores iniciales
        a1 = AuthorDB(
            name="Gustavo",
            bio="Estudiante de CS y miembro de la asociación de estudiantes.",
            role="association_member",
        )
        a2 = AuthorDB(
            name="Diego",
            bio="Backend developer y miembro del crew del podcast.",
            role="podcast_crew",
        )
        a3 = AuthorDB(
            name="Marta",
            bio="Diseñadora UX que escribe sobre experiencia de usuario.",
            role="student",
        )

        db.add_all([a1, a2, a3])
        db.commit()

        db.refresh(a1)
        db.refresh(a2)
        db.refresh(a3)

        # Artículos iniciales
        art1 = ArticleDB(
            title="Cómo sobrevivir al primer semestre de CS",
            content="Tips prácticos sobre horarios, carga de cursos y salud mental.",
            category="blog",
            author_id=a1.id,
            tags="primer_semestre,tips,estudiantes",
            published_at=datetime.now(timezone.utc)
        )
        art2 = ArticleDB(
            title="Resumen del último meetup de la asociación",
            content="Crónica del meetup, networking y charla con egresados.",
            category="news",
            author_id=a1.id,
            tags="asociacion,eventos,meetup",
            published_at=datetime.now(timezone.utc)
        )
        art3 = ArticleDB(
            title="Buenas prácticas para APIs en proyectos de curso",
            content="Consejos técnicos para organizar endpoints, errores y documentación.",
            category="blog",
            author_id=a2.id,
            tags="apis,backend,proyectos",
            published_at=datetime.now(timezone.utc)
        )

        db.add_all([art1, art2, art3])
        db.commit()
    finally:
        db.close()

# Ejecutar seed al arrancar (solo si la BD está vacía)
seed_db()

# ------------------------------------------------
# Esquemas Pydantic
# ------------------------------------------------

class AuthorBase(BaseModel):
    name: str
    bio: Optional[str] = None
    role: str = Field(default="student")

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int

    class Config:
        from_attributes = True


class ArticleBase(BaseModel):
    title: str
    content: str
    category: str = Field(default="blog")
    author_id: int
    tags: Optional[Union[List[str], str]] = []

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: int
    published_at: datetime

    class Config:
        from_attributes = True

# ------------------------------------------------
# Dependencia para la sesión de BD
# ------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------
# Middleware de logging (para ELK)
# ------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ns = int((time.time() - start_time) * 1_000_000_000)  # nanosegundos

    log_data = {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "http.request.method": request.method,
        "http.response.status_code": response.status_code,
        "event.duration": duration_ns,
        "url.path": request.url.path,
        "service.name": SERVICE_NAME,
        "log.level": "INFO"
    }

    logger.info(json.dumps(log_data))
    return response

# ------------------------------------------------
# Endpoints base
# ------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc)}

@app.get("/")
def root():
    return {"message": "Jack's Cave API operando", "version": "v1"}

# ------------------------------------------------
# Endpoints de Autores
# ------------------------------------------------

@app.get("/authors", response_model=List[Author])
def list_authors(db: Session = Depends(get_db)):
    authors = db.query(AuthorDB).all()
    return authors

@app.post("/authors", response_model=Author, status_code=201)
def create_author(author: AuthorCreate, db: Session = Depends(get_db)):
    db_author = AuthorDB(
        name=author.name,
        bio=author.bio,
        role=author.role,
    )
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@app.get("/authors/{author_id}", response_model=Author)
def get_author(author_id: int, db: Session = Depends(get_db)):
    author = db.query(AuthorDB).filter(AuthorDB.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

# ------------------------------------------------
# Endpoints de Artículos
# ------------------------------------------------

def tags_to_str(tags: Optional[List[str]]) -> str:
    if not tags:
        return ""
    return ",".join(tags)

def tags_from_str(tags_str: Optional[str]) -> List[str]:
    if not tags_str:
        return []
    return [t for t in tags_str.split(",") if t]

@app.get("/articles", response_model=List[Article])
def list_articles(db: Session = Depends(get_db)):
    articles_db = db.query(ArticleDB).all()
    # Adaptar tags antes de devolver
    articles: List[Article] = []
    for a in articles_db:
        art = Article.model_validate(a)
        art.tags = tags_from_str(a.tags)
        articles.append(art)
    return articles

@app.post("/articles", response_model=Article, status_code=201)
def create_article(article: ArticleCreate, db: Session = Depends(get_db)):
    # Verificar que el autor exista
    author = db.query(AuthorDB).filter(AuthorDB.id == article.author_id).first()
    if not author:
        raise HTTPException(status_code=400, detail="Author does not exist")

    db_article = ArticleDB(
        title=article.title,
        content=article.content,
        category=article.category,
        author_id=article.author_id,
        tags=tags_to_str(article.tags),
        published_at=datetime.now(timezone.utc),
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)

    art = Article.from_orm(db_article)
    art.tags = tags_from_str(db_article.tags)
    return art

@app.get("/articles/{article_id}", response_model=Article)
def get_article(article_id: int, db: Session = Depends(get_db)):
    a = db.query(ArticleDB).filter(ArticleDB.id == article_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    art = Article.from_orm(a)
    art.tags = tags_from_str(a.tags)
    return art

@app.get("/authors/{author_id}/articles", response_model=List[Article])
def list_articles_by_author(author_id: int, db: Session = Depends(get_db)):
    # Valida autor
    author = db.query(AuthorDB).filter(AuthorDB.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")

    articles_db = db.query(ArticleDB).filter(ArticleDB.author_id == author_id).all()
    articles: List[Article] = []
    for a in articles_db:
        art = Article.from_orm(a)
        art.tags = tags_from_str(a.tags)
        articles.append(art)
    return articles
