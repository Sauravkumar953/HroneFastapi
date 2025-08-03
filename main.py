from fastapi import FastAPI, Query
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import  Optional,List
import re


app = FastAPI()
client = MongoClient("mongodb+srv://Saurav:Saurav%40123456@clustertestnew.en4ar.mongodb.net/")

db = client["SauravDB"]
products_collection =db["products"]
orders_collection =db["orders"]

class SizeItem(BaseModel):
    sizeType:str
    qty:int
    
class productModel(BaseModel): 
    name:str    
    price:float
    sizes:list[SizeItem]
    
    
###-----Post Product
@app.post("/create_product")
async def create_product(req_data:productModel):
    
        data =req_data.model_dump()
        result =products_collection.insert_one(data)
        return{"product has been created, inserted_id": str(result.inserted_id)}

##------Post Order
class item(BaseModel):
    productId: str
    qty : int
    
class order(BaseModel):
    userId:str
    items:list[item]
    
        
@app.post("/orders")
async def create_orders(req_data:order):
    
    data = req_data.model_dump()
    result = orders_collection.insert_one(data)    
    return{"id": str(result.inserted_id)}

######------------GET Product

@app.get("/products")
def list_products(
        name: Optional[str] = Query(None, description="Partial name search or regex"),
        sizes: Optional[str] = Query(None, description="Filter by size"),
        limit: Optional[int] = Query(10, ge=1, le=100),
        offset: Optional[int] = Query(0, ge=0)
    ):
    query = {}

    if name:
        # Case-insensitive regex search
        query["name"] = {"$regex": re.escape(name), "$options": "i"}

    if sizes:
        query["sizes"] = {"$elemMatch": {"$regex": re.escape(sizes), "$options": "i"}}

    # Sort by _id for pagination
    cursor = products_collection.find(query, {"sizes": 0}).sort("_id").skip(offset).limit(limit)
    
    products = []
    for product in cursor:
        product["_id"] = str(product["_id"])  # Convert ObjectId to string
        products.append(product)

    return {
         "data": products,
        # "total": products_collection.count_documents(query),
        "page": {"next":limit,"limit":0,"previous":-limit}
        # "offset": offset,
    }
    
####------ GET Order

@app.get("/orders")
def list_orders(
    userid: Optional[str] = Query(None, description="User ID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = {}
    if userid:
        query["userId"] = userid

    total = orders_collection.count_documents(query)

    cursor = orders_collection.find(query).sort("_id").skip(offset).limit(limit)

    orders = []
    for order in cursor:
        order["_id"] = str(order["_id"])
        orders.append(order)

    next_offset = offset + limit if (offset + limit) < total else None
    prev_offset = offset - limit if offset - limit >= 0 else None

    return {
        "data": orders,
        "total": total,
        "page": {
            "limit": limit,
            "offset": offset,
            "next": next_offset,
            "previous": prev_offset
        }
    }
