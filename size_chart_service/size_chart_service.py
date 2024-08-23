import requests
from sqlalchemy.orm import Session
from datetime import datetime

from interfaces.api_interface import Preferences
from models.db_models import Product

class SizeChartService:

    def fetch_size_guide(self, store_id, product_id, description):
        current_time = datetime.utcnow()
        url = f"https://www.zara.com/itxrest/3/catalog/store/{store_id}/product/{product_id}/size-measure-guide?locale=en_GB"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        print(response)
        if response.status_code != 200:
            return {
                "error": "Non 200 response"
            }
        data = response.json()
        size_chart = self.transform_size_guide(data)
        product_info = {
            "name": description,
            "description": description,
            "created_at": current_time,
            "updated_at": current_time,
            "size_chart": size_chart,
            "source": "zara",
        }
        return product_info
    
    
    def transform_size_guide(self,data: dict[str, any]) -> list[dict[str, dict[str, float]]]:
        size_guide_info = data.get("sizeGuideInfo")
        measure_guide_info = data.get("measureGuideInfo")
        
        if not size_guide_info and not measure_guide_info:
            raise Exception("No size or measure guide info found in the response.")
        
        sizes_data = []
        
        if size_guide_info:
            sizes = size_guide_info.get("sizes", [])
            for size in sizes:
                size_name = size.get("name").lower()
                measures = size.get("measures", [])
                measurements = {}
                for i, measure in enumerate(measures):
                    if i == 0:
                        measurements["shoulder"] = float(measure["dimensions"][0]["value"])
                    elif i == 1:
                        measurements["chest"] = float(measure["dimensions"][0]["value"])
                sizes_data.append({size_name: measurements})
        
        elif measure_guide_info:
            sizes = measure_guide_info.get("sizes", [])
            for size in sizes:
                size_name = size.get("name").lower()
                measures = size.get("measures", [])
                measurements = {}
                for measure in measures:
                    zone = measure["tableTitleZone"]
                    dimension = next((dim for dim in measure["dimensions"] if dim["unitId"] == "cm"), None)
                    if dimension:
                        if "chest" in zone:
                            measurements["chest"] = float(dimension["value"])
                        elif "front-length" in zone:
                            measurements["front"] = float(dimension["value"])
                        elif "sleeve-length" in zone:
                            measurements["sleeve"] = float(dimension["value"])
                        elif "back-width" in zone:
                            measurements["back"] = float(dimension["value"])
                        elif "arm-width" in zone:
                            measurements["arm"] = float(dimension["value"])
                sizes_data.append({size_name: measurements})
        
        return sizes_data


    def get_vibe_check(self,size_data,recommendation,preferences:Preferences,product:Product):
        product_info = {
           'color':product.color,
           'ocassion':product.ocassion
        }
        size_rating = self.get_size_rating(size_data=size_data,recommendation=recommendation)
        preference_score = 0
        product_info['fitting'] = self.find_fitting(product.description)
        print(product_info['fitting'])
        if preferences and preferences.fitting and preferences.color:
            preference_score = self.estimate_preference_score(product_info,preferences)
        print(size_rating,preference_score)
        return (size_rating + preference_score) / 2




    def get_size_rating(self,size_data,recommendation):
        recommended_size = recommendation["recommended_size"].lower()
        estimated_chest = recommendation["estimated_chest_length"]
        estimated_shoulder = recommendation["estimated_shoulder_length"]
        
        actual_measurements = next((size[recommended_size] for size in size_data if recommended_size in size), None)
        print(recommended_size,actual_measurements)
        if actual_measurements == None:
            return 0
        if 'back' in actual_measurements:
            actual_measurements["chest"] += actual_measurements["back"]
        
        if not actual_measurements:
            return 0  # If size is not found, return 0 (no fit)
        
        chest_diff = abs(actual_measurements["chest"] - estimated_chest)
        shoulder_diff = abs(actual_measurements["shoulder"] - estimated_shoulder) if 'shoulder' in actual_measurements else 0
        
        max_chest_diff = 55
        max_shoulder_diff = 25
        
        chest_score = max(0, 100 - (chest_diff / max_chest_diff) * 100)
        shoulder_score = max(0, 100 - (shoulder_diff / max_shoulder_diff) * 100)
        
        overall_score = (chest_score + shoulder_score) / 2
        
        return round(overall_score)

    def estimate_preference_score(self,description:any, preferences:Preferences):

        garment_fitting = description["fitting"].lower()
        garment_color = description["color"].lower()
        garment_ocassion = description["ocassion"].lower()
        

        preferred_fitting = preferences.fitting.lower()
        preferred_color = preferences.color.lower()
        preferred_ocassion = preferences.ocassion.lower()
        

        fitting_score = 0
        color_score = 0
        ocassion_score = 0
        

        if garment_fitting == preferred_fitting:
            fitting_score = 100
        else:
            fitting_score = 50  # Partial match if fitting is different
        

        if garment_color == preferred_color:
            color_score = 100
        else:
            color_score = 0  # No match if color is different
        

        if garment_ocassion == preferred_ocassion:
            ocassion_score = 100
        else:
            ocassion_score = 0  # No match if occasion is different
        

        overall_score = (fitting_score + color_score + ocassion_score) / 3
        
        return round(overall_score)

    def find_fitting(self,description):
        # Convert the description to lowercase to ensure case-insensitive matching
        description = description.lower() if description else ""

        # Define keywords associated with different fitting types
        fitting_keywords = {
            "baggy": ["baggy"],
            "oversize": ["oversize", "oversized"],
            "slim": ["slim", "slim fit", "skinny"],
            "regular": ["regular", "regular fit"]
        }

        # Check for each fitting type in the description
        for fitting_type, keywords in fitting_keywords.items():
            for keyword in keywords:
                if keyword in description:
                    return fitting_type.capitalize()

        # Default to 'Regular' if no specific fitting is found
        return "Regular"