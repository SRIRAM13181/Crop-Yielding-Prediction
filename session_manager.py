"""
Session Manager for Crop Yield Prediction Chatbot
Handles conversation history and session context management.
"""

import streamlit as st
from typing import List, Dict
from datetime import datetime


class SessionManager:
    """Manages user sessions, conversation history, and context."""
    
    def __init__(self, session_id: str = "default"):
        """
        Initialize session manager.
        
        Args:
            session_id: Unique identifier for the session
        """
        self.session_id = session_id
        self.max_history = 10  # Keep last 10 exchanges for context
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize Streamlit session state for chat history."""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        if "session_id" not in st.session_state:
            st.session_state.session_id = self.session_id
        
        if "prediction_context" not in st.session_state:
            st.session_state.prediction_context = {}
    
    def add_message(self, role: str, content: str, metadata: Dict = None) -> None:
        """
        Add a message to conversation history.
        
        Args:
            role: "user" or "assistant"
            content: Message content
            metadata: Optional metadata (e.g., prediction data)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        st.session_state.chat_history.append(message)
        
        # Keep only last N exchanges to avoid token limits
        if len(st.session_state.chat_history) > self.max_history * 2:
            st.session_state.chat_history = st.session_state.chat_history[-self.max_history * 2:]
    
    def get_conversation_context(self) -> str:
        """
        Get formatted conversation context for OpenAI API.
        
        Returns:
            Formatted conversation string with last 5-10 exchanges
        """
        context = []
        for msg in st.session_state.chat_history[-10:]:  # Last 5 exchanges = 10 messages
            role = msg["role"].capitalize()
            context.append(f"{role}: {msg['content']}")
        
        return "\n".join(context)
    
    def get_chat_history(self) -> List[Dict]:
        """
        Get full chat history.
        
        Returns:
            List of all messages in conversation
        """
        return st.session_state.chat_history
    
    def clear_history(self) -> None:
        """Clear chat history and reset session."""
        st.session_state.chat_history = []
        st.session_state.prediction_context = {}
    
    def set_prediction_context(self, prediction_data: Dict) -> None:
        """
        Store current prediction context for reference in chat.
        
        Args:
            prediction_data: Dictionary with prediction details
                {
                    "features": [...],
                    "predicted_yield": float,
                    "crop": str,
                    "state": str,
                    "timestamp": str
                }
        """
        st.session_state.prediction_context = prediction_data
    
    def get_prediction_context(self) -> Dict:
        """Get current prediction context."""
        return st.session_state.prediction_context
    
    def get_system_prompt(self) -> str:
        """
        Get system prompt for OpenAI with app context.
        
        Returns:
            System prompt string
        """
        context = self.get_prediction_context()
        
        context_info = ""
        if context:
            context_info = f"""

Current Context:
- Recently predicted crop: {context.get('crop', 'N/A')}
- State: {context.get('state', 'N/A')}
- Predicted yield: {context.get('predicted_yield', 'N/A')} kg/acre
- Input features: {context.get('features', [])}

When users reference their recent prediction, use this context."""
        
        system_prompt = f"""You are an expert agricultural advisor specializing in crop yield prediction and sustainable farming practices in India.

Your role is to:
1. Help users predict crop yields by guiding them through input parameters
2. Provide agronomic advice based on optimal ranges for different crops and soils
3. Explain predictions in simple, actionable terms
4. Suggest improvements to increase yield and profitability
5. Answer questions about soil, fertilizers, rainfall, temperature, and crop selection
6. Compare different farming scenarios when asked

Key characteristics:
- Be conversational and step-by-step in your guidance
- Always provide reasoning behind your recommendations
- Reference specific crop/soil requirements when relevant
- Use metric units (kg/ha, °C, mm rainfall)
- Encourage sustainable farming practices
- If unsure about a specific question, acknowledge limitations and suggest consulting local agricultural extension offices

Supported crops: Wheat, Rice, Maize, Sugarcane
Supported soil types: Loamy, Clay, Sandy
Coverage: All 36 Indian states and union territories{context_info}"""
        
        return system_prompt
    
    def format_messages_for_api(self, user_message: str) -> List[Dict]:
        """
        Format conversation history for OpenAI API call.
        
        Args:
            user_message: Current user input
        
        Returns:
            List of messages formatted for API
        """
        messages = []
        
        # Add previous messages from history
        for msg in st.session_state.chat_history[-8:]:  # Last 4 exchanges
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def get_conversation_summary(self) -> str:
        """
        Get summary of conversation topics discussed.
        
        Returns:
            Brief summary string
        """
        if not st.session_state.chat_history:
            return "No conversation yet."
        
        topics = []
        keywords = ["yield", "crop", "fertilizer", "soil", "rainfall", "temperature", "profit", "prediction"]
        
        full_text = " ".join([msg["content"].lower() for msg in st.session_state.chat_history])
        
        for keyword in keywords:
            if keyword in full_text:
                topics.append(keyword)
        
        if not topics:
            return "General agricultural discussion"
        
        return f"Discussed: {', '.join(set(topics))}"


# Utility function for quick access
def get_session() -> SessionManager:
    """Get or create session manager instance."""
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager()
    return st.session_state.session_manager
