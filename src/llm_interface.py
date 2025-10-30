import os
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Optional
from dotenv import load_dotenv

class LLMInterface:
    """
    Helps set up LLM and create specific prompt templates
    """

    def __init__(self, temperature: float = 0.7):
        """
        Initialize LLM Interface

        Args:
            provider: LLM provider (anthropic)
            model: Specific model
            temperature: randomness of response
        """
        self.temperature = temperature
        self.llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            temperature=temperature,
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
    
    def get_llm(self):
        return self.llm
    
    def generate(self, prompt: str, system_msg: str = None) -> str:
        messages = []

        if system_msg:
            messages.append(SystemMessage(content=system_msg))

        messages.append(HumanMessage(content=prompt))
        response = self.llm.invoke(messages)
        
        return response.content
    
    def generate_with_template(self, template: str, **kwargs) -> str:
        prompt = PromptTemplate.from_template(template)
        formatted_prompt = prompt.format(**kwargs)

        response = self.llm.invoke([HumanMessage(content=formatted_prompt)])
        return response.content
    

if __name__ == "__main__":
    load_dotenv()
    handler = LLMInterface()
    
    response = handler.generate(
        prompt="What are the health benefits of chicken breast?",
        system_msg="You are a nutrition expert."
    )
    print(response)
    
    template = """
    Analyze the following diet:
    Foods: {foods}
    
    Provide nutritional insights and suggestions.
    """
    
    response = handler.generate_with_template(
        template=template,
        foods="chicken breast, white rice, broccoli"
    )
    print(response)