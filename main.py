import ssl
from fastapi import FastAPI,Depends
from dotenv import load_dotenv
from intent_generation import intent_generation_service
from chatbot_system import chat_bot_service
from product import product_service
from size_chart_service import size_chart_service
from interfaces.api_interface import Backfill, Chatbot, GenerateHash, GetOcassionRecommendation, GetOverview, GetRecommendation, GetSizeRequest, GetZaraProductImages, RecommendSize
from sqlalchemy.orm import Session
from database.db import get_db

# Load environment variables from .env file
load_dotenv()

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

app = FastAPI()


@app.get("/")
async def root():
    return {
        "success": True
    }



@app.post("/get_size_chart")
async def get_size_chart(request:GetSizeRequest,db: Session = Depends(get_db)):
    print(request)
    res = product_service.Products_Service().create_product(db,store_id=request.storeId,url=request.url,title=request.title,description=request.description,color=request.color)
    return res

@app.post("/backfill")
async def get_size_chart(request:Backfill,db: Session = Depends(get_db)):
    print(request)
    res = product_service.Products_Service().backfill(db=db)
    return res

@app.post("/overview")
async def get_size_chart(request:GetOverview,db: Session = Depends(get_db)):
    print(request)
    res = product_service.Products_Service().get_product_overview(request=request,db=db)
    return res

@app.post("/generate_text")
async def generate_text(request:GetOcassionRecommendation):
    print(request)
    res = intent_generation_service.IntentGenerationService().predict_ocassion_bert(description=request.description, title=request.title)
    return res

@app.post("/fine_tune_gpt")
async def generate_text(request:GetOcassionRecommendation):
    print(request)
    res = intent_generation_service.IntentGenerationService().fine_tune_gpt2()
    return res

@app.post("/train_bert")
async def generate_text(request:GetOcassionRecommendation):
    print(request)
    res = intent_generation_service.IntentGenerationService().train_bert()
    return res

@app.post("/get_zara_product_images_and_price")
async def generate_text(request:GetZaraProductImages,db: Session = Depends(get_db)):
    print(request)
    res = product_service.Products_Service().backfill_images(db=db)
    return "OK"
@app.post("/train_bert")
async def generate_text(request:GetOcassionRecommendation):
    print(request)
    res = intent_generation_service.IntentGenerationService().train_bert()
    return res

@app.post("/generate_hash")
async def generate_text(request:GenerateHash):
    print(request)
    res = product_service.Products_Service().generate_hash(color=request.color, occasion=request.ocassion,category=request.category)
    return res

@app.post("/recommend_size")
async def generate_text(request:RecommendSize):
    print(request)
    res = intent_generation_service.IntentGenerationService().recommend_size(height=request.height,weight=request.weight,age=request.age,body_shape=request.body_shape)
    return res

@app.post("/create_embeddings")
async def create_embeddings(request:RecommendSize,db: Session = Depends(get_db)):
    print(request)
    res = product_service.Products_Service().create_embeddings(db)
    return res

@app.post("/create_faiss_index")
async def create_faiss_index(request:RecommendSize,db: Session = Depends(get_db)):
    print(request)
    res = product_service.Products_Service().create_faiss_index(db)
    return res

@app.post("/get_recommendation")
async def create_faiss_index(request:GetRecommendation,db: Session = Depends(get_db)):
    print(request)
    res = product_service.Products_Service().get_recommendation(db,request.query)
    return res

@app.post("/chatbot")
async def chatbot(request:Chatbot,db: Session = Depends(get_db)):
    print(request)
    res = chat_bot_service.Chat_Bot_Service().chatbot(db,request)
    return res

import json
@app.post("/create_color_db")
async def generate_text(request:GetOcassionRecommendation):
    input_file = './color/basic.json'
    output_file = './color/colors.json'
    with open(input_file, 'r') as file:
        data = json.load(file)
    result_dict = {item['name'].lower(): item['hex'] for item in data}    
    with open(output_file, 'w') as file:
        json.dump(result_dict, file, indent=4)
    return "OK"


