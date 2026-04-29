"""
OpenAI Chatbot Integration for Crop Yield Prediction
Handles conversational AI for agricultural advisory.
"""

import streamlit as st
from typing import Optional, Dict, List
import os
import time
from openai import OpenAI, RateLimitError


class CropAdvisoryBot:
    """Crops yield prediction chatbot powered by OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the chatbot.
        
        Args:
            api_key: OpenAI API key. If None, will try to get from Streamlit secrets.
        
        Raises:
            ValueError: If API key is not provided and not found in secrets.
        """
        if api_key is None:
            api_key = st.secrets.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set OPENAI_API_KEY in .streamlit/secrets.toml"
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 1000
        self.temperature = 0.7  # Balance between creativity and accuracy
    
    def get_response(
        self,
        messages: List[Dict],
        system_prompt: str,
        temperature: Optional[float] = None,
        max_retries: int = 3
    ) -> str:
        """
        Get response from OpenAI API with retry logic for rate limits.
        
        Args:
            messages: List of message dicts with "role" and "content"
            system_prompt: System instructions for the model
            temperature: Sampling temperature (0-2)
            max_retries: Number of retries on rate limit
        
        Returns:
            Assistant response text
        
        Raises:
            Exception: If API call fails after retries
        """
        try:
            temp = temperature if temperature is not None else self.temperature
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *messages
                ],
                temperature=temp,
                max_tokens=self.max_tokens,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].message.content
        
        except RateLimitError as e:
            # Retry with exponential backoff
            for attempt in range(max_retries):
                wait_time = 2 ** attempt  # 1 sec, 2 sec, 4 sec
                st.info(f"⏳ Rate limited. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            *messages
                        ],
                        temperature=temp,
                        max_tokens=self.max_tokens
                    )
                    return response.choices[0].message.content
                except RateLimitError:
                    continue
            
            return "⏳ Rate limit exceeded. Please try again in a few moments. The chatbot is experiencing high demand."
        
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg:
                return "❌ API Error: Invalid API key. Please check your OPENAI_API_KEY in secrets.toml"
            elif "429" in error_msg:
                return "⏳ Rate limit exceeded. Please try again in a moment."
            elif "500" in error_msg:
                return "🔧 OpenAI service temporarily unavailable. Please try again later."
            else:
                return f"❌ Error: {error_msg[:200]}"
    
    def process_user_input(
        self,
        user_message: str,
        conversation_history: List[Dict],
        system_prompt: str,
        prediction_data: Optional[Dict] = None
    ) -> str:
        """
        Process user input and return chatbot response.
        
        Args:
            user_message: User's text input
            conversation_history: Previous messages (last 8 for context)
            system_prompt: System instructions
            prediction_data: Optional dict with recent prediction context
        
        Returns:
            Chatbot response
        """
        # Add context injection for prediction references
        enriched_message = user_message
        
        if prediction_data and ("prediction" in user_message.lower() or "yield" in user_message.lower()):
            if not any(keyword in user_message.lower() for keyword in ["general", "example", "typical"]):
                enriched_message += f"\n[Context: User recently predicted {prediction_data.get('crop', '')} yield of {prediction_data.get('predicted_yield', 'N/A')} kg/acre in {prediction_data.get('state', '')}]"
        
        # Format messages for API
        messages = [*conversation_history, {"role": "user", "content": enriched_message}]
        
        # Get response
        response = self.get_response(
            messages=messages,
            system_prompt=system_prompt
        )
        
        return response
    
    def get_quick_tip(self, crop: str, state: str) -> str:
        """
        Get a quick farming tip for a specific crop and state.
        
        Args:
            crop: Crop name (Wheat, Rice, Maize, Sugarcane)
            state: Indian state name
        
        Returns:
            Quick tip string
        """
        try:
            messages = [
                {
                    "role": "user",
                    "content": f"Give me 1 concise farming tip (1-2 sentences) for growing {crop} in {state}. Focus on practical, actionable advice."
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise agricultural advisor. Provide brief, practical tips."
                    },
                    *messages
                ],
                temperature=0.6,
                max_tokens=150
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Unable to fetch tip: {str(e)[:50]}"
    
    def analyze_prediction(
        self,
        crop: str,
        state: str,
        predicted_yield: float,
        inputs: Dict
    ) -> str:
        """
        Generate detailed analysis of a prediction.
        
        Args:
            crop: Crop name
            state: State name
            predicted_yield: Predicted yield in kg/acre
            inputs: Dictionary of input features
        
        Returns:
            Analysis string
        """
        try:
            analysis_prompt = f"""
The model predicted a yield of {predicted_yield} kg/acre for {crop} in {state}.
Input conditions: Rainfall={inputs.get('rainfall')}mm, Temperature={inputs.get('temperature')}°C, 
Humidity={inputs.get('humidity')}%, N={inputs.get('nitrogen')}kg/ha, P={inputs.get('phosphorus')}kg/ha, 
K={inputs.get('potassium')}kg/ha, pH={inputs.get('pH')}, Soil type={inputs.get('soil_type')}

Provide a 2-3 sentence analysis explaining:
1. Whether this yield is typical for these conditions
2. The main limiting or optimizing factors
3. One suggestion for improvement
Keep it practical and farmer-friendly."""
            
            messages = [{"role": "user", "content": analysis_prompt}]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert agricultural scientist explaining ML predictions."
                    },
                    *messages
                ],
                temperature=0.5,
                max_tokens=300
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            return f"Unable to generate analysis: {str(e)[:50]}"


def create_chatbot() -> CropAdvisoryBot:
    """Factory function to create chatbot instance with error handling."""
    try:
        return CropAdvisoryBot()
    except ValueError as e:
        st.error(f"⚠️ Chatbot Setup Error: {str(e)}")
        st.info("📝 To use the chatbot, add your OpenAI API key:\n"
                "1. Go to https://platform.openai.com/api-keys\n"
                "2. Copy your API key\n"
                "3. Create `.streamlit/secrets.toml` with: `OPENAI_API_KEY = 'your-key-here'`")
        return None
    except Exception as e:
        # If any other error (like rate limit), show warning but return mock
        st.warning(f"⚠️ Using Mock Chatbot (Demo Mode)\nError: {str(e)[:100]}")
        return None


# Test/Demo mode without API key (for development)
class MockChatbot:
    """Mock chatbot for testing without API key."""
    
    def get_response(
        self,
        messages: List[Dict],
        system_prompt: str,
        temperature: Optional[float] = None
    ) -> str:
        """Return mock response for testing."""
        user_msg = messages[-1]["content"].lower() if messages else ""
        
        mock_responses = {
            "yield": "Based on your inputs, this yield prediction seems reasonable. The nitrogen levels are good, and rainfall is adequate.",
            "better": "Try increasing phosphorus by 10-15 kg/ha and ensure pH is between 6.0-7.5 for optimal nutrient absorption.",
            "soil": "For your soil type, ensure proper drainage and organic matter content (2-3%). Consider crop rotation.",
            "fertilizer": "Apply half the nitrogen at planting and half at mid-season for better uptake.",
            "weather": "Monitor rainfall patterns 30-45 days before harvest to minimize moisture issues.",
        }
        
        for key, response in mock_responses.items():
            if key in user_msg:
                return response
        
        return "That's a great question about crop yield prediction. Could you be more specific about what aspect interests you? (yield factors, fertilizer, weather, soil, etc.)"
    
    def get_quick_tip(self, crop: str, state: str) -> str:
        return f"For {crop} in {state}: Monitor soil moisture regularly and apply balanced fertilizer in 2-3 splits."
    
    def analyze_prediction(self, crop: str, state: str, predicted_yield: float, inputs: Dict) -> str:
        return f"The predicted yield of {predicted_yield} kg/acre is reasonable for {crop} given the current conditions. Focus on optimizing nitrogen timing."
