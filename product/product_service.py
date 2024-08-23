import os
from sqlalchemy.orm import Session
from database.crud import create_product, get_all_embeddings, get_all_products, get_last_row, get_product, get_product_by_id, update_product
from intent_generation import intent_generation_service
from interfaces.api_interface import GetOverview
from models.db_models import Embeddings, Product
from size_chart_service import size_chart_service
import hashlib
from urllib.parse import urlparse, parse_qs
from openai import OpenAI
import json
import numpy as np
import faiss
from sqlalchemy import text


class Products_Service:
    def find_garment_category(self,title: str) -> str:
        categories = ["shirt", "t-shirt", "trousers", "jeans", "shorts", "jackets"]
        words = title.lower().split()
        last_word = words[-1]
        if last_word in categories:
            return last_word.capitalize()
        for word in words:
            if word in categories:
                return word.capitalize()
        return "Unknown"
    
    def getProductId(self,url):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        return query_params.get('v1', [None])[0]
    
    def get_product_overview(self,request:GetOverview,db:Session):
        productRequest = request.product
        product = self.create_product(db=db,store_id=productRequest.storeId,url=productRequest.url,title=productRequest.title,description=productRequest.description,color=productRequest.color)
        size_recommendation = {}
        size_info = request.size_info
        if size_info:
            size_recommendation = intent_generation_service.IntentGenerationService().recommend_size(size_info.height,size_info.weight,size_info.age,size_info.body_shape)
        print(size_recommendation)
        vibeCheck = size_chart_service.SizeChartService().get_vibe_check(product=product,size_data=product.size_chart,preferences=request.preferences,recommendation=size_recommendation)
        return {
            'product':product,
            'size_recommendation':size_recommendation,
            'vibeCheck':vibeCheck,
            'vibecheck_copy': self.get_copy_vibecheck(vibeCheck=vibeCheck),
            'occasion_copy': self.get_copy_ocassion(ocassion=product.ocassion)
        }
    
    def get_copy_vibecheck(self,vibeCheck):
        if vibeCheck > 80:
            return f'With an impressive approval rating of over {vibeCheck}%, Get ready to elevate your style with confidence—this choice is a winner.'
        elif vibeCheck >= 65 and vibeCheck < 80:
            return f"Scoring a solid {vibeCheck}%, this product has a lot going for it! You'll love how it fits, and while there's room for improvement in color and style, it’s still a smart addition to your wardrobe. Grab it now and make it your own!"
        elif vibeCheck >= 25 and vibeCheck < 65:
            return f"This product has received less than {vibeCheck}% approval, so there may be some fit concerns. If you're okay with a potential sizing challenge, this could still be a good choice."
        elif vibeCheck >= 0 and vibeCheck < 25:
            return f"With an approval rating below {vibeCheck}%, this product may not be the best fit for you in terms of size, color, or style. Consider exploring Our FashionGPT 🤖"

    def get_copy_ocassion(self,ocassion:str):
        if ocassion.lower() == 'casual':
            return 'This outfit is your go-to for everyday style! Stay cool, stay casual, and own the day!'
        elif ocassion.lower() == 'party':
            return 'Get ready to turn heads at your next party! This outfit is all about making a statement—fun and totally you.'
        elif ocassion.lower() == 'official':
            return 'Elevate your professional wardrobe with this sharp, sophisticated outfit. Ideal for any official setting'


    

    def create_product(self,db:Session, store_id, url, title, description,color)->Product:
        color = color.split("|")[0].strip().split("Colour:").pop().strip()
        product_id = self.getProductId(url)
        oneClickProductId = f'{store_id}-{product_id}'
        product = get_product(db=db,product_id=oneClickProductId)
        isUpdate = False
        if product and product.id:
            return product
        product_info = size_chart_service.SizeChartService().fetch_size_guide(store_id=store_id,product_id=product_id,description=description)
        primarycolor = intent_generation_service.IntentGenerationService().categorize_color(color_name=color)
        ocassion = intent_generation_service.IntentGenerationService().predict_ocassion_bert(description=description,title=title)
        category = self.find_garment_category(title)
        media_and_price = intent_generation_service.IntentGenerationService().get_zara_product_images_and_price(url)
        media = media_and_price[0]
        price = media_and_price[1]
        print(media_and_price)
        product_info['color'] = color
        product_info['ocassion'] = ocassion
        product_info['name'] = title
        product_info['category'] = category
        product_info['url'] = url
        product_info['media'] = media
        product_info['price'] = price
        product_info['embedding_index_id'] = self.generate_hash(color=primarycolor,occasion=ocassion, category=category)
        if isUpdate:
            update_product(db,product.id,product_info)
        else:
            product_info['product_id'] = oneClickProductId
            create_product(db,product_info)
        print(product_info)
        return Product(**product_info)
    
    def generate_hash(self,color: str, occasion: str, category: str) -> str:
        combined_string = f"{color.lower()}-{occasion.lower()}-{category.lower()}"
        print(combined_string)
        hash_object = hashlib.sha256(combined_string.encode())
        hash_hex = hash_object.hexdigest()
        return hash_hex
    
    def backfill(self,db:Session):
        products = get_all_products(db,None)
        for product in products:
            media_and_price = intent_generation_service.IntentGenerationService().get_zara_product_images_and_price(product.url)
            update_product(db,product.id,{"price":media_and_price[1]})
    
    def create_embeddings(self,db):
        last_row = get_last_row(db=db)
        last_product_id = last_row.product_id
        products = get_all_products(db,last_product_id)
        print(last_product_id, len(products))
        open_ai_key = os.getenv('OPEN_AI_KEY')
        client = OpenAI(api_key=open_ai_key)
        documents = []
        for product in products:
            str_representation = ''
            for key in product.__dict__.keys():
                value = getattr(product, key)
                if key == 'media' or key == 'size_chart':
                    continue
                str_representation += f'{key}: {value}, '
            documents.append(str_representation)
        print(documents)
        embeddings = [r.embedding for r in client.embeddings.create(input=documents, model="text-embedding-3-small").data]
        # Store embeddings in TiDB
        i=0
        for doc, emb in zip(documents, embeddings):
            emb_array = np.array(emb)
            print(emb_array.shape)
            embedding_obj = Embeddings(**{
                'embedding': emb_array.tobytes(),
                'product_id': products[i].id
            })
            db.add(embedding_obj)
            i+=1
        db.commit()
        return "OK"
    
    

    def create_faiss_index(self, db, index_path="faiss_index.index"):
        # Fetch embeddings from database
        result = db.execute(text("SELECT id, embedding FROM embeddings"))
        rows = result.fetchall()
        ids = np.array([row[0] for row in rows])
        
        # Convert embeddings to numpy array
        embedding_matrix = np.array([np.frombuffer(row[1]) for row in rows])
        print(embedding_matrix.shape, embedding_matrix.shape[1])
        
        # Create FAISS index
        dimension = embedding_matrix.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embedding_matrix)
        
        # Save the index to a file
        faiss.write_index(index, index_path)
        
        return 'OK'

    
    def load_faiss_index(self,index_path="faiss_index.index"):
        # Load the FAISS index from the file
        index = faiss.read_index(index_path)
        return index
    
    def get_recommendation(self,db:Session,query):
        print("final query",query)
        open_ai_key = os.getenv('OPEN_AI_KEY')
        client = OpenAI(api_key=open_ai_key)
        index = self.load_faiss_index()
        
        # Generate the query vector using the same model as the one used for index creation
        query_vector = client.embeddings.create(input=query, model="text-embedding-3-small").data[0].embedding
        
        # Convert query vector to numpy array and reshape it
        query_vector = np.array(query_vector, dtype=np.float32).reshape(1, -1)
        
        # Debug output
        print(f"Query vector shape: {query_vector.shape}")
        print(f"Index type: {type(index)}")
        
        try:
            # Search for nearest neighbors
            D, I = index.search(query_vector, k=5)  # k is the number of nearest neighbors to retrieve
            print(f"Distances shape: {D.shape}")
            print(f"Indices shape: {I.shape}")
            print(I)
            # Fetch and display results
            results = []
            for i in I[0]:
                result = get_product_by_id(db, i)  # Assuming you have a method to fetch products by ID
                embedding_id, product = result
                print(product)
                finalResult = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'url': product.url,
                    'media': product.media,
                    'product_id': product.product_id,
                    'image': product.media[0],
                    'price': product.price
                }
                if result:
                    results.append(finalResult)
            print(results)
            return results
        
        except Exception as e:
            print(f"An error occurred during FAISS search: {e}")
            return []
