import os
from dotenv import load_dotenv

from nutrition_api import APIClient
from llm_interface import LLMInterface
from nutrition_analyzer import NutritionAnalyzer
from vector_store import VectorStore
from llm_rag_pipeline import RAGChain

# Load environment variables
load_dotenv()

def load_vector_db(vs, usda):
    """
    Quick setup: Set up vector DB if it is empty
    Only runs once on first use
    """
    # Check if DB has data by trying a search
    try:
        test_results = vs.vectorstore.similarity_search("protein", k=1)
        if test_results:
            return  # Already has data
    except:
        pass
    
    print("Vector DB is empty. Loading a list of sample foods")
    
    sample_foods = foods = [
    "chicken breast",
    "turkey breast",
    "salmon",
    "tuna",
    "cod",
    "ground beef",
    "ground turkey",
    "pork chop",
    "shrimp",
    "eggs",
    "greek yogurt",
    "cottage cheese",
    "tofu",
    
    "white rice",
    "brown rice",
    "quinoa",
    "oatmeal",
    "whole wheat bread",
    "pasta",
    "sweet potato",
    "potato",
    
    "broccoli",
    "spinach",
    "kale",
    "cauliflower",
    "carrots",
    "bell peppers",
    "zucchini",
    
    "avocado",
    "almonds"
]
    
    for food_name in sample_foods:
        try:
            results = usda.search_foods(food_name, page_size=1)
            if results:
                food = usda.get_food_details(results[0]['fdcId'])
                vs.add_food_data([{
                    'fdc_id': food.fdc_id,
                    'name': food.description,
                    'protein': food.protein,
                    'carbs': food.carbs,
                    'fat': food.fat,
                    'calories': food.calories,
                    'fiber': food.fiber,
                    'tags': []
                }])
                print(f"{food_name}")
        except:
            pass
    
    print("Vector DB ready!\n")


def main():
    """Simple nutrition chatbot"""
    
    print("=" * 60)
    print("NUTRITION ASSISTANT")
    print("=" * 60)
    
    print("\nInitializing...")
    try:
        usda = APIClient()
        llm = LLMInterface()
        vs = VectorStore()

        load_vector_db(vs, usda)

        rag = RAGChain(llm.get_llm(), vs.get_retriever())
        analyzer = NutritionAnalyzer()
        print("Ready!\n")
    except Exception as e:
        print(f"Setup failed: {e}")
        print("\nMake sure you have:")
        print("  - API_KEY in .env")
        print("  - ANTHROPIC_API_KEY in .env")
        return
    
    location = input("Your location: ").strip() or "United States"
    
    print("\nEnter 3 foods you eat:")
    foods = []
    for i in range(3):
        food = input(f"  Food {i+1}: ").strip()
        if food:
            foods.append(food)
    
    if len(foods) < 3:
        print("Please provide at least 3 foods")
        return
    
    print(f"\nLocation: {location}")
    print(f"Foods: {', '.join(foods)}\n")
    
    all_foods = []
    
    for food_name in foods:
        print(f"--- {food_name} ---")
        
        try:
            # Search USDA for the specific food
            results = usda.search_foods(food_name, page_size=1)
            if not results:
                print(f"Food not found, skipping\n")
                continue
            
            # Get nutrition
            food = usda.get_food_details(results[0]['fdcId'])
            print(f"Found: {food.description}")
            print(f"Protein: {food.protein}g | Carbs: {food.carbs}g | Fat: {food.fat}g")
            
            all_foods.append({
                'name': food.description,
                'protein': food.protein,
                'carbs': food.carbs,
                'fat': food.fat,
                'calories': food.calories,
                'fiber': food.fiber
            })
            
            # Find alternatives
            print("Finding alternatives...")
            try:
                rag_results = rag.find_alternatives(
                    food_name=food.description,
                    criteria="higher protein, lower carbs, lower fat"
                )
                
                # Filter with analyzer
                better = analyzer.top_n_alternatives(
                    original=all_foods[-1],
                    candidates=[{
                        'name': r['name'],
                        'protein': r['nutrition']['protein'],
                        'carbs': r['nutrition']['carbs'],
                        'fat': r['nutrition']['fat'],
                        'calories': r['nutrition']['calories']
                    } for r in rag_results],
                    top_n=2
                )
                
                if better:
                    print("Better alternatives:")
                    for alt in better:
                        print(f"  • {alt['food']['name']}: {alt['score'].reasoning}")
                else:
                    print("  (No better alternatives found - this food is already great!)")
                    
            except Exception as e:
                print(f"Could not find alternatives: {e}")
            
            print()
            
        except Exception as e:
            print(f"Error processing '{food_name}': {e}\n")
    
    if all_foods:
        print("=" * 60)
        print("OVERALL ANALYSIS")
        print("=" * 60)
        print("\nGenerating personalized recommendations...")
        
        try:
            result = rag.analyze_diet(
                location=location,
                foods=all_foods,
                user_goals="improve nutrition"
            )
            print("\n" + result['analysis'])
        except Exception as e:
            print(f"\nCould not generate analysis: {e}")
    
    print("\n" + "=" * 60)
    print("Thanks for using Nutrition Assistant!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBye!")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("\nIf you're stuck, check:")
        print("  1. All files are in the right place")
        print("  2. .env file has your API keys")
        print("  3. You ran: pip install -r requirements.txt")