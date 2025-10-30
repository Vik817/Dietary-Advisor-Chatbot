from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class NutritionScore:
    """Score regarding how good an alternative is"""
    protein_diff: float
    carb_diff: float
    fat_diff: float
    overall_score: float
    reasoning: str

class NutritionAnalyzer:
    """
    Analyzes and compares different nutritional information and content
    Compares and filters alternatives
    """

    def __init__(
            self,
            min_protein_increase: float = 3.0,
            max_carb_ratio: float = 0.8,
            max_fat_ratio: float = 0.8
    ):
        """
        Initialize nutrition analyzer with the specified criteria

        Args:
            min_protein_increase: Minimum protein increase needed to be considered a better alternative (grams)
            max_carb_ratio: Maximum carbs as a ratio of the original
            max_fat_ratio: Maximum fat as a ratio of the original
        """
        self.min_protein_increase = min_protein_increase
        self.max_carb_ratio = max_carb_ratio
        self.max_fat_ratio = max_fat_ratio

    def is_better(
            self,
            original: Dict[str, float],
            alternative: Dict[str, float]
    ) -> bool:
        """
        Check if one food is a better alternative than the original food

        Args:
            original: Original food nutrition data
            alternative: Alternative food nutrition data

        Returns:
            True if alternative is better, False if not
        """

        # Get values
        orig_protein = original.get('protein', 0)
        orig_carbs = original.get('carbs', 0)
        orig_fat = original.get('fat', 0)
        
        alt_protein = alternative.get('protein', 0)
        alt_carbs = alternative.get('carbs', 0)
        alt_fat = alternative.get('fat', 0)

        protein_increase = alt_protein - orig_protein
        if protein_increase < self.min_protein_increase:
            return False
        
        if orig_carbs > 0:
            carb_ratio = alt_carbs / orig_carbs
            if carb_ratio > self.max_carb_ratio:
                return False
        
        if orig_fat > 0:
            fat_ratio = alt_fat / orig_fat
            if fat_ratio > self.max_fat_ratio:
                return False
        
        return True
    
    def score_alternative(
        self,
        original: Dict[str, float],
        alternative: Dict[str, float]
    ) -> NutritionScore:
        """
        Score how much better an alternative is
        
        Args:
            original: Original food nutrition data
            alternative: Alternative food nutrition data
            
        Returns:
            NutritionScore object with improvements and reasoning
        """
        orig_protein = original.get('protein', 0)
        orig_carbs = original.get('carbs', 0)
        orig_fat = original.get('fat', 0)
        
        alt_protein = alternative.get('protein', 0)
        alt_carbs = alternative.get('carbs', 0)
        alt_fat = alternative.get('fat', 0)
        
        # More protein is better
        protein_improvement = alt_protein - orig_protein

        # Less fats and carbs is better
        carb_improvement = orig_carbs - alt_carbs
        fat_improvement = orig_fat - alt_fat
        
        # Protein: 40%, Carbs: 30%, Fat: 30%
        protein_score = (protein_improvement / max(orig_protein, 1)) * 0.4
        carb_score = (carb_improvement / max(orig_carbs, 1)) * 0.3
        fat_score = (fat_improvement / max(orig_fat, 1)) * 0.3
        
        overall_score = protein_score + carb_score + fat_score

        # An overall score of 0.0 shows no improvement
        # Scores above 1.0 show great improvement
        
        # Generate reasoning
        reasons = []
        if protein_improvement > 0:
            reasons.append(f"+{protein_improvement}g protein")
        if carb_improvement > 0:
            reasons.append(f"-{carb_improvement}g carbs")
        if fat_improvement > 0:
            reasons.append(f"-{fat_improvement}g fat")
        
        reasoning = ", ".join(reasons) if reasons else "Similar nutrition"
        
        return NutritionScore(
            protein_diff=protein_improvement,
            carb_diff=carb_improvement,
            fat_diff=fat_improvement,
            overall_score=overall_score,
            reasoning=reasoning
        )
    
    def top_n_alternatives(self, original: Dict[str, float], candidates: List[Dict[str, float]], top_n: int = 5) -> List[Dict]:
        """
        Filter the potential candidates and get the top n best alternatives

        Args:
            original: Original food nutrition
            candidates: List of alternatives
            top_n: Number of top alternatives to return
        """

        alternatives = []

        for candidate in candidates:
            if self.is_better(original, candidate):
                score = self.score_alternative(original, candidate)

                alternatives.append({
                    'food': candidate,
                    'nutritionScore': score,
                    'overall_score': score.overall_score
                })
            
        alternatives.sort(key=lambda x: x['overall_score'], reverse=True)

        return alternatives[:top_n]
    
if __name__ == "__main__":
    analyzer = NutritionAnalyzer()
# Original food
    pizza = {
        'name': 'Pepperoni Pizza',
        'protein': 12,
        'carbs': 33,
        'fat': 10,
        'calories': 266,
        'fiber': 2
    }
    
    # Alternatives
    alternatives = [
        {
            'name': 'Grilled Chicken Wrap',
            'protein': 25,
            'carbs': 28,
            'fat': 6,
            'calories': 254,
            'fiber': 3
        },
        {
            'name': 'Cauliflower Crust Pizza',
            'protein': 20,
            'carbs': 15,
            'fat': 7,
            'calories': 195,
            'fiber': 4
        },
        {
            'name': 'Turkey Sandwich',
            'protein': 8,
            'carbs': 35,
            'fat': 12,
            'calories': 280,
            'fiber': 2
        },
        {
            'name': 'Chicken Caesar Salad',
            'protein': 30,
            'carbs': 10,
            'fat': 8,
            'calories': 240,
            'fiber': 3
        }
    ]
    
    # Filter and rank
    ranked = analyzer.top_n_alternatives(pizza, alternatives, top_n=3)
    print(ranked)

    print("Original Food:")
    print(f"{pizza['name']}: {pizza['protein']}g protein, {pizza['carbs']}g carbs, {pizza['fat']}g fat")
    print("\n" + "="*50 + "\n")
    
    print("Better Alternatives:")
    for i, alt in enumerate(ranked, 1):
        print(f"\n{i}. {alt['food']['name']}")
        print(f"   Score: {alt['overall_score']:.2f}")
        print(f"   Improvements: {alt['nutritionScore'].reasoning}")


