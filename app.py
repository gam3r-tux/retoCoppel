import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.comicsdb


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ComicModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str = Field(...)
    onSaleDate: str = Field(...)
    image: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "Jane Doe",
                "onSaleDate": "2029-12-31T00:00:00-0500",
                "image": "",
            }
        }


class UpdateComicModel(BaseModel):
    title: str = Field(...)
    onSaleDate: str = Field(...)
    image: str = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "title": "Jane Doe",
                "onSaleDate": "2029-12-31T00:00:00-0500",
                "image": "",
            }
        }


@app.post("/", response_description="Add new comic", response_model=ComicModel)
async def create_comic(comic: ComicModel = Body(...)):
    comic = jsonable_encoder(comic)
    new_comic = await db["comics"].insert_one(comic)
    created_comic = await db["comics"].find_one({"_id": new_comic.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_comic)


@app.get(
    "/", response_description="List all comics", response_model=List[ComicModel]
)
async def list_comics():
    comics = await db["comics"].find().to_list(1000)
    return comics


@app.get(
    "/{id}", response_description="Get a single comic", response_model=ComicModel
)
async def show_comic(id: str):
    if (comic := await db["comics"].find_one({"_id": id})) is not None:
        return comic

    raise HTTPException(status_code=404, detail=f"Comic {id} not found")


@app.put("/{id}", response_description="Update a comic", response_model=ComicModel)
async def update_comic(id: str, comic: UpdateComicModel = Body(...)):
    comic = {k: v for k, v in comic.dict().items() if v is not None}

    if len(comic) >= 1:
        update_result = await db["comics"].update_one({"_id": id}, {"$set": comic})

        if update_result.modified_count == 1:
            if (
                updated_comic := await db["comics"].find_one({"_id": id})
            ) is not None:
                return updated_comic

    if (existing_comic := await db["comics"].find_one({"_id": id})) is not None:
        return existing_comic

    raise HTTPException(status_code=404, detail=f"Comic {id} not found")


@app.delete("/{id}", response_description="Delete a comic")
async def delete_comic(id: str):
    delete_result = await db["comics"].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Comic {id} not found")
