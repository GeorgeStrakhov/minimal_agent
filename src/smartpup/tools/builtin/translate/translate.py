from smartpup.tools.base import BaseTool
from smartpup.tools.env import EnvVar, ToolEnv
from pydantic import BaseModel, Field
from openai import OpenAI
import os
from typing import Optional

class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language to translate to")
    source_language: Optional[str] = Field(None, description="Source language (if known)")

class TranslateTool(BaseTool):
    name = "translate"
    description = "Translate text from one language to another"
    
    env = ToolEnv(vars=[
        EnvVar(
            name="OPENROUTER_API_KEY",
            description="OpenRouter API key for translation",
            required=True
        ),
        EnvVar(
            name="OPENROUTER_BASE_URL",
            description="OpenRouter base URL",
            required=True
        )
    ])
    
    async def execute(
        self,
        text: str,
        target_language: str,
        source_language: str = None
    ) -> str:
        """
        Translate text to target language
        
        Args:
            text: Text to translate
            target_language: Language to translate to (e.g. 'Spanish', 'French')
            source_language: Source language (optional)
            
        Returns:
            Translated text
        """
        request = TranslateRequest(
            text=text,
            target_language=target_language,
            source_language=source_language
        )
        
        client = OpenAI(
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )
        
        # Construct system prompt
        system_prompt = (
            f"You are a translator. Translate the following text to {request.target_language}. "
            "Respond with ONLY the translated text, no explanations."
        )
        if request.source_language:
            system_prompt += f" The source language is {request.source_language}."
            
        try:
            completion = client.chat.completions.create(
                model="anthropic/claude-3.5-haiku",  # Fast and cheap for translation
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.text}
                ]
            )
            
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Translation failed: {str(e)}" 