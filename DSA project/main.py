import os
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal, Optional

from fastapi import FastAPI, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

import database
from inventory import StoreError, store

BASE = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(app):
    database.init_db()
    store.load()  
    yield


app = FastAPI(title="Small Store Inventory", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")



class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    category: str = Field(min_length=1, max_length=30)
    price: float = Field(gt=0, le=100000)
    quantity: int = Field(ge=0, le=100000)
    expiry: Optional[str] = None

    @field_validator("name", "category")
    @classmethod
    def not_blank(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("price")
    @classmethod
    def two_decimals(cls, v):
        return round(v, 2)

    @field_validator("expiry")
    @classmethod
    def valid_date(cls, v):
        if v in (None, ""):
            return None
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("must be a valid date (YYYY-MM-DD)")
        return v


class ProductCreate(ProductBase):
    sku: str = Field(pattern=r"^[A-Za-z0-9-]{1,20}$")

    @field_validator("sku")
    @classmethod
    def upper(cls, v):
        return v.upper()


class SellRequest(BaseModel):
    quantity: int = Field(ge=1, le=100000)


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc):
    msgs = []
    for e in exc.errors():
        field = ".".join(str(x) for x in e["loc"] if x not in ("body", "query", "path"))
        msg = e["msg"].replace("Value error, ", "")
        msgs.append(f"{field}: {msg}" if field else msg)
    return JSONResponse(status_code=422, content={"detail": "; ".join(msgs)})


@app.exception_handler(StoreError)
async def store_error_handler(request, exc):
    return JSONResponse(status_code=exc.status, content={"detail": str(exc)})



@app.get("/", include_in_schema=False)
def home():
    return FileResponse(os.path.join(BASE, "static", "index.html"))


@app.get("/api/products")
def list_products(
    sort_by: Literal["name", "price", "quantity", "expiry"] = "name",
    order: Literal["asc", "desc"] = "asc",
    algo: Literal["merge", "quick"] = "merge",
):
    return store.sorted_list(sort_by, order, algo) 


@app.get("/api/products/{sku}")
def get_product(sku: str):
    return store.get(sku.upper())  


@app.post("/api/products", status_code=201)
def create_product(p: ProductCreate):
    return store.add(p.model_dump())


@app.put("/api/products/{sku}")
def update_product(sku: str, p: ProductBase):
    return store.update(sku.upper(), p.model_dump())


@app.delete("/api/products/{sku}")
def delete_product(sku: str):
    store.remove(sku.upper())
    return {"deleted": sku.upper()}


@app.post("/api/products/{sku}/sell")
def sell_product(sku: str, req: SellRequest):
    return store.sell(sku.upper(), req.quantity)  


@app.get("/api/sales")
def recent_sales(limit: int = Query(10, ge=1, le=100)):
    return store.recent_sales(limit)  


@app.get("/api/sales/report")
def sales_report():
    return store.sales_report()  


@app.post("/api/sales/undo")
def undo_sale():
    return store.undo_last_sale()  


@app.get("/api/search")
def search(q: str = Query(..., min_length=1, max_length=60), mode: Literal["linear", "binary"] = "linear"):
    if not q.strip():
        raise StoreError("Search text must not be blank.")
    return store.search(q.strip(), mode)


@app.get("/api/expiring")
def expiring(limit: int = Query(5, ge=1, le=50)):
    return store.expiring(limit)  


@app.get("/api/price-range")
def price_range(min_price: float = Query(0, ge=0), max_price: float = Query(..., ge=0)):
    return store.price_range(min_price, max_price) 


@app.get("/api/structures")
def structures():
    return store.structures()
