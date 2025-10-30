import os
from dotenv import load_dotenv
import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from diskcache import Cache

@dataclass
class FoodInfo:
    """Specific information for a selected food"""
    name: str
    amount: float
    unit: str

@dataclass
class FoodNutrients:
    """Nutrition data for a selected food"""
    fdc_id: int
    description: str
    data_type: str
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    calories: float = 0.0
    fiber: float = 0.0
    sugar: float = 0.0
    nutrients: Dict[str, FoodInfo] = None

    def __post_init__(self):
        if self.nutrients is None:
            self.nutrients = {}

class APIClient:
    """
    Client used to handle the actual USDA FoodData Central API
    Search, retrieval, and caching handled here
    """

    URL = "https://api.nal.usda.gov/fdc/v1"


    # Specific nutrient identifiers
    NUTRIENT_IDENTIFIERS = {
        'protein': '203',
        'carbs': '205',
        'fat': '204',
        'calories': '208',
        'fiber': '291',
        'sugar': '269'
    }

    def __init__(self, cache_dir: str = "../data/cache"):
        self.api_key = os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API Key Required. Set API_KEY env variable")
        self.cache = Cache(cache_dir)
        self.session = requests.Session()
        self.last_request_time = 0
        self.rate_limit_delay = 0.1

    def make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """
        Make API request given an endpoint

        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method

        Returns:
            API response in dict format
        """

        url = f"{self.URL}/{endpoint}"
        params = params or {}
        params['api_key'] = self.api_key
        
        # Check the cache
        cache_key = f"{endpoint}:{str(params)}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached
        
        # For our case, method always = GET
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            self.cache.set(cache_key, data)
            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")


    def search_foods(self, query: str, page_size: int = 5, data_type: str = "Survey (FNDDS)") -> List[Dict]:
        """
        Search for a specific food by name

        Args:
            query: Search term of food
            page_size: Number of results to return
            data_type: Type of food data

        Returns:
            List of food search results
        """
        params = {
            'query': query,
            'pageSize': page_size,
            'data_type': [data_type]
        }

        response = self.make_request('foods/search', params)

        # Return the "foods" portion of the data in the json response
        return response.get('foods', [])

    def parse_food(self, data: Dict) -> FoodNutrients:
        """
        Parse through the data from an API response and create a FoodNutrients object for a specific food

        Args:
            data: API response in json
        
        Returns:
            Parsed FoodNutrients object
        """

        nutrients = {}

        food_nutrients = data.get('foodNutrients', [])

        protein = 0.0
        carbs = 0.0
        fat = 0.0
        calories = 0.0
        fiber = 0.0
        sugar = 0.0
        
        # Store the nutrients in the dictionary
        for nutrient in food_nutrients: 
            nutrient_info = nutrient.get('nutrient', {})
            nutrient_num = nutrient_info.get('number', '')
            nutrient_name = nutrient_info.get('name', '')
            amount = nutrient.get('amount', 0.0)
            unit = nutrient_info.get('unitName', 'g')

            nutrients[nutrient_name] = FoodInfo(
                name = nutrient_name,
                amount = amount,
                unit = unit
            )

            if nutrient_num == self.NUTRIENT_IDENTIFIERS['protein']:
                protein = amount
            elif nutrient_num == self.NUTRIENT_IDENTIFIERS['carbs']:
                carbs = amount
            elif nutrient_num == self.NUTRIENT_IDENTIFIERS['fat']:
                fat = amount
            elif nutrient_num == self.NUTRIENT_IDENTIFIERS['calories']:
                calories = amount
            elif nutrient_num == self.NUTRIENT_IDENTIFIERS['fiber']:
                fiber = amount
            elif nutrient_num == self.NUTRIENT_IDENTIFIERS['sugar']:
                sugar = amount
        
        return FoodNutrients(
            fdc_id=data.get('fdcId'),
            description=data.get('description', ''),
            data_type=data.get('dataType', ''),
            protein=protein,
            carbs=carbs,
            fat=fat,
            calories=calories,
            fiber=fiber,
            sugar=sugar,
            nutrients=nutrients
        )

    def get_food_details(self, fdc_id: int) -> FoodNutrients:
        """
        Get detailed nutrition information for a food
        
        Args:
            fdc_id: FoodData Central ID
            
        Returns:
            FoodItem object with complete nutrition data
        """
        data = self.make_request(f'food/{fdc_id}')

        return self.parse_food(data)
    
    def clear_cache(self):
        """Clear API response cache"""
        self.cache.clear()


if __name__ == "__main__":
    # Initialize client
    load_dotenv()
    client = APIClient()
    
    # Search for a food
    print("Searching for 'apple'...")
    results = client.search_foods("apple")
    
    for food in results:
        print(f"- {food['description']} (FDC ID: {food['fdcId']})")
    
    # Get detailed info
    if results:
        #print(results[0]['foodNutrients'])
        food_item = client.get_food_details(results[0]['fdcId'])
        print(f"\nNutrition for {food_item.description}:")
        print(f"  Protein: {food_item.protein}g")
        print(f"  Carbs: {food_item.carbs}g")
        print(f"  Fat: {food_item.fat}g")
        print(f"  Calories: {food_item.calories}")
        print(f"  Fiber: {food_item.fiber}g")
        print(f"  Sugar: {food_item.sugar}g")