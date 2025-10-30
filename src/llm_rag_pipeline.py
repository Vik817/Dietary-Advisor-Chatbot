from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from typing import List, Dict

class RAGChain:

    def __init__(self, llm, retriever):
        """
        Initizliing RAG chain using LCEL

        Args:
            llm: LLM instance
            retriver: Retriever instance
        """
        self.llm = llm
        self.retriever = retriever
        self.chain = self.create_chain()
    
    def create_chain(self):
        prompt = ChatPromptTemplate.from_template(
        """
        You are a professional nutritionalist analyzing a person's dinner.
        
        Context from knowledge base regarding nutrition information:
        {context}

        User Information:
            Location: {location}
            Foods: {current_foods}
        
        Nutrition Data:
        {nutrition_data}

        Goal:
        1. Analyze the nutritional content of the user's typical dinner
        2. Use the context to provide recommendations for:
            -Lower-carb alternatives
            -Higher-protein options
            -Lower-fat alternatives
        3. Present the reccomendations/alternatives that are better and explain why
        4. Present recommendations in a clear, friendly manner
                                                  """)
        
        chain = (
            RunnableParallel(
                {
                    "context": lambda x: self.format_docs(
                        self.retriever.invoke(x["query"])
                    ),
                    "location": lambda x: x.get("location", "Unknown"),
                    "current_foods": lambda x: x.get("current_foods", ""),
                    "nutrition_data": lambda x: x.get("nutrition_data", ""),
                }
            )
            # Pass this context to the prompt
            | prompt
            # Invoke the LLM with the new context in the prompt
            | self.llm
            # Parse output and return it as a string
            | StrOutputParser()
        )
        
        return chain
    
    def format_docs(self, docs: List[Document]):
        """Format the documents into information that can be passed into the prompt"""
        if not docs:
            return "No relevant information"
        
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            content = doc.page_content.strip()
            formatted_docs.append(f"[Source {i}]\n{content}")

        return "\n\n".join(formatted_docs)
    
    def analyze_diet(self, location: str, foods: List[Dict], user_goals: str = "diet and health") -> Dict:
        """
        Analyze a user's diet and give them reccomendations

        Args:
            location: User's location
            foods: List of food items with nutrition data
            user_goals: User's dietary goals
            
        Returns:
            Dictionary with analysis
        """
        current_foods_str = ", ".join([f['name'] for f in foods])
        nutrition_summary = self.format_nutrition_data(foods)
        search_query = self.create_query(foods, user_goals)

        result = self.chain.invoke({
            "query": search_query,
            "locatino": location,
            "current_foods": current_foods_str,
            "nutrition_data": nutrition_summary
        })

        return {
            "analysis": result,
            "foods_analyzed": foods
        }
    
    def format_nutrition_data(self, foods: List[Dict]) -> str:

        output = []
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        total_calories = 0
        
        for food in foods:
            output.append(f"\n{food['name']}:")
            output.append(f"  - Protein: {food.get('protein', 0)}g")
            output.append(f"  - Carbs: {food.get('carbs', 0)}g")
            output.append(f"  - Fat: {food.get('fat', 0)}g")
            output.append(f"  - Calories: {food.get('calories', 0)}")
            
            total_protein += food.get('protein', 0)
            total_carbs += food.get('carbs', 0)
            total_fat += food.get('fat', 0)
            total_calories += food.get('calories', 0)
        
        output.append(f"\nTotal Daily Intake:")
        output.append(f"  - Protein: {total_protein}g")
        output.append(f"  - Carbs: {total_carbs}g")
        output.append(f"  - Fat: {total_fat}g")
        output.append(f"  - Calories: {total_calories}")
        
        return "\n".join(output)
    
    def find_alternatives(
        self,
        food_name: str,
        criteria: str = "healthier"
    ) -> List[Dict]:
        """
        Find alternative foods using LCEL retrieval
        
        Args:
            food_name: Current food to replace
            criteria: What to optimize
            
        Returns:
            List of alternative foods with context
        """
        query = f"{criteria} alternatives to {food_name}"
        
        # Using the retriever directly
        results = self.retriever.invoke(query)
        
        alternatives = []
        for doc in results:
            if doc.metadata.get('type') == 'food_item':
                alternatives.append({
                    'name': doc.metadata.get('name'),
                    'nutrition': {
                        'protein': doc.metadata.get('protein'),
                        'carbs': doc.metadata.get('carbs'),
                        'fat': doc.metadata.get('fat'),
                        'calories': doc.metadata.get('calories')
                    },
                    'reason': doc.page_content[:200]
                })
        
        return alternatives
    
    def create_query(self, foods: List[Dict], goals: str) -> str:
        """Create optimized search query for retrieval"""
        avg_protein = sum(food.get('protein', 0) for food in foods) / len(foods)
        avg_carbs = sum(food.get('carbs', 0) for food in foods) / len(foods)
        
        query_parts = []
        
        if avg_protein < 15:
            query_parts.append("high protein alternatives")
        if avg_carbs > 30:
            query_parts.append("low carb substitutes")
        
        query_parts.append(goals)
        
        food_names = " ".join([f['name'] for f in foods])
        query_parts.append(f"alternatives to {food_names}")
        
        return " ".join(query_parts)
    
def create_simple_nutrition_chain(llm, retriever):
    """
    Create a simple LCEL chain for quick nutrition queries

    Usage: For test cases
    """
    prompt = ChatPromptTemplate.from_template(
        "Context: {context}\n\nQuestion: {question}\n\nAnswer:"
    )
    
    chain = (
        {
            "context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain


# Example usage
if __name__ == "__main__":
    from llm_interface import LLMInterface
    from vector_store import VectorStore
    from dotenv import load_dotenv
    load_dotenv()
    
    llm_interface = LLMInterface()
    vs_manager = VectorStore()
    
    rag_chain = RAGChain(
        llm=llm_interface.get_llm(),
        retriever=vs_manager.get_retriever()
    )
    

    user_foods = [
        {
            'name': 'white rice',
            'protein': 2.7,
            'carbs': 28,
            'fat': 0.3,
            'calories': 130
        },
        {
            'name': 'ground beef',
            'protein': 26,
            'carbs': 0,
            'fat': 20,
            'calories': 280
        }
    ]
    
    print("Analyzing diet with LCEL chain...")
    result = rag_chain.analyze_diet(
        location="Austin, TX",
        foods=user_foods,
        user_goals="lose weight and build muscle"
    )
    
    print("\nAnalysis:")
    print(result['analysis'])
    

    print("\n" + "="*50)
    print("Testing simple LCEL chain...")
    simple_chain = create_simple_nutrition_chain(
        llm_interface.get_llm(),
        vs_manager.get_retriever()
    )
    
    response = simple_chain.invoke("What are good sources of protein?")
    print(response)