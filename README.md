# Dietary Advisor Chatbot

A simple LLM Powered Chatbot to provide dietary nutrition advice using data from USDA FoodData Central

## Setup Instructions

#### Prerequisites
- Python 3.8+
- USDA API Key
- Anthropic API Key

Installation
1. Clone this repository

2. Create a virtual environment (Optional)

3. Use requirements.txt and install dependencies

4. Setup the API keys as environment variables in a .env file
- "ANTHROPIC_API_KEY" for the Anthropic api key
- "API_KEY" for the USDA api key

5. Run the app using: python src/main.py


#### Drawback and Tradeoffs
- Using Anthropic can hit a rate limit
- The vector database only currently has 30 foods retrieved from USDA
- Often times users might not get many a better alternative