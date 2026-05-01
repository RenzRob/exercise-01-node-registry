"""Node Registry API — FastAPI app."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Node
from .schemas import NodeCreate, NodeResponse, NodeUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Node Registry", lifespan=lifespan)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db_status = "connected"
    nodes_count = 0
    try:
        db.execute(text("SELECT 1"))
        nodes_count = db.scalar(
            select(func.count()).select_from(Node).where(Node.status == "active")
        ) or 0
    except SQLAlchemyError:
        db_status = "disconnected"
    return {"status": "ok", "db": db_status, "nodes_count": nodes_count}


@app.post("/api/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Node).where(Node.name == payload.name))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Node already exists")

    node = Node(name=payload.name, host=payload.host, port=payload.port, status="active")
    db.add(node)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Node already exists")
    db.refresh(node)
    return node


@app.get("/api/nodes", response_model=list[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    return db.scalars(select(Node).order_by(Node.id)).all()


@app.get("/api/nodes/{name}", response_model=NodeResponse)
def get_node(name: str, db: Session = Depends(get_db)):
    node = db.scalar(select(Node).where(Node.name == name))
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return node


@app.put("/api/nodes/{name}", response_model=NodeResponse)
def update_node(name: str, payload: NodeUpdate, db: Session = Depends(get_db)):
    node = db.scalar(select(Node).where(Node.name == name))
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(node, field, value)

    db.commit()
    db.refresh(node)
    return node


@app.delete("/api/nodes/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(name: str, db: Session = Depends(get_db)):
    node = db.scalar(select(Node).where(Node.name == name))
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    node.status = "inactive"
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
