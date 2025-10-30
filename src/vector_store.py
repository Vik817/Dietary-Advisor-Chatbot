import os
from typing import List, Dict, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


class VectorStore:

    def __init__(
            self,
            collection_name: str = "nutrition_knowledge",
            persist_directory: str = "./data/chroma_db",
    ):
        """Initialize Vector Store
        
        Args:
            collection_name: Name for the vector collection
            persist_directory: Where to store the database
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )
    
    def add_food_data(self, food_items: List[Dict]):
        """
        Helper method to add food data to the ChromaDB

        Args:
            food_items: List of food dictionaries from the USDA API
        """
        documents = []

        for food in food_items:
            content = f"""
            Food: {food['name']}
            Category: {food.get('category', 'General')}
            Description: {food.get('description', '')}
            
            Nutrition per 100g:
            - Protein: {food.get('protein', 0)}g
            - Carbohydrates: {food.get('carbs', 0)}g
            - Fat: {food.get('fat', 0)}g
            - Calories: {food.get('calories', 0)}
            - Fiber: {food.get('fiber', 0)}g
            
            Tags: {', '.join(food.get('tags', []))}
            """
            metadata = {
                'fdc_id': food.get('fdc_id'),
                'name': food['name'],
                'category': food.get('category', 'General'),
                'protein': food.get('protein', 0),
                'carbs': food.get('carbs', 0),
                'fat': food.get('fat', 0),
                'calories': food.get('calories', 0),
                'type': 'food_item'
            }
            
            documents.append(Document(
                page_content=content,
                metadata=metadata
            ))
        
        # Add to ChromaDB
        self.vectorstore.add_documents(documents)
    
    def get_retriever(self, search_kwargs: Optional[Dict] = None):
        """
        Get a Retriver to use in RAG

        Args: search_kwargs: Arguments for retriver

        Returns: langchain retriever
        """
        search_kwargs = search_kwargs or {"k": 5}
        return self.vectorstore.as_retriever(search_kwargs=search_kwargs)
    
if __name__ == "__main__":
    vs_manager = VectorStore()
    
    print("ChromaDB Vector Store initialized!")
    print(f"Location: {vs_manager.persist_directory}")
    print(f"Collection: {vs_manager.collection_name}")
    print()
    
    # Add some sample food data
    foods = [
        {
            'fdc_id': 171477,
            'name': 'Chicken breast, skinless',
            'category': 'Poultry',
            'description': 'Lean protein source',
            'protein': 31,
            'carbs': 0,
            'fat': 3.6,
            'calories': 165,
            'fiber': 0,
            'tags': ['high-protein', 'low-carb', 'lean']
        },
        {
            'fdc_id': 168878,
            'name': 'Brown rice, cooked',
            'category': 'Grains',
            'description': 'Whole grain with fiber',
            'protein': 2.6,
            'carbs': 23,
            'fat': 0.9,
            'calories': 112,
            'fiber': 1.8,
            'tags': ['whole-grain', 'fiber']
        },
        {
            'fdc_id': 170567,
            'name': 'Salmon, Atlantic, cooked',
            'category': 'Fish',
            'description': 'Fatty fish rich in omega-3',
            'protein': 25,
            'carbs': 0,
            'fat': 13,
            'calories': 206,
            'fiber': 0,
            'tags': ['high-protein', 'omega-3', 'fatty-fish']
        }
    ]
    
    print("Adding foods to vector database...")
    vs_manager.add_food_data(foods)
    print(f"Added {len(foods)} foods to ChromaDB")
    print()
    
    # Get retriever for use in chains
    retriever = vs_manager.get_retriever(search_kwargs={"k": 3})
    print("Retriever ready for RAG chain")
    print()
    
    # Test retrieval
    print("Testing retrieval: 'high protein alternatives'")
    results = retriever.invoke("high protein alternatives")
    
    print(f"Found {len(results)} results:")
    for i, doc in enumerate(results, 1):
        name = doc.metadata.get('name', 'Unknown')
        protein = doc.metadata.get('protein', 0)
        print(f"  {i}. {name} ({protein}g protein)")
