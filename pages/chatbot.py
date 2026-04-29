"""
Crop Yield Prediction Chatbot Interface
Streamlit page for interactive agricultural advisory chatbot.
"""

import streamlit as st
from session_manager import get_session
from chatbot import create_chatbot, MockChatbot
from utils import predict_yield, get_model_metrics, get_recommendations


# Page configuration
st.set_page_config(
    page_title="🤖 Crop Yield Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Custom styling for chat
st.markdown("""
<style>
    .user-message {
        background-color: #e3f2fd;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid #1976d2;
    }
    .bot-message {
        background-color: #f5f5f5;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid #4caf50;
    }
    .quick-action-button {
        margin: 4px;
    }
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 16px;
        background-color: #fafafa;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Page header
st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🤖 Agricultural Advisor Chatbot</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Get expert guidance on crop yield predictions, farming practices, and optimization strategies</p>", unsafe_allow_html=True)


# Initialize chatbot and session
@st.cache_resource
def get_chatbot_instance():
    """Get or create chatbot instance."""
    bot = create_chatbot()
    if bot is None:
        # Use mock chatbot if API key not available
        st.warning("⚠️ Running in mock mode (demo). To enable real AI responses, add your OpenAI API key to `.streamlit/secrets.toml`")
        return MockChatbot()
    return bot


try:
    chatbot = get_chatbot_instance()
    session = get_session()
except Exception as e:
    st.error(f"Error initializing chatbot: {str(e)}")
    st.stop()


# Sidebar: Chat controls and context
with st.sidebar:
    st.markdown("### 📱 Chat Controls")
    
    # Session info
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            session.clear_history()
            st.rerun()
    
    with col2:
        if st.button("📋 Summary", use_container_width=True):
            st.info(f"**Chat Summary:** {session.get_conversation_summary()}")
    
    st.divider()
    
    # Context display
    st.markdown("### 🎯 Current Context")
    context = session.get_prediction_context()
    
    if context:
        st.success("✓ Prediction saved in context")
        with st.expander("View Details", expanded=False):
            st.write(f"**Crop:** {context.get('crop', 'N/A')}")
            st.write(f"**State:** {context.get('state', 'N/A')}")
            st.write(f"**Predicted Yield:** {context.get('predicted_yield', 'N/A')} kg/acre")
    else:
        st.info("💡 Go to 'Home - Predict Yield' to create a prediction that the chatbot can reference")
    
    st.divider()
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("💡 Get Farming Tip", use_container_width=True):
        if context:
            tip = chatbot.get_quick_tip(context.get('crop', 'Wheat'), context.get('state', 'Punjab'))
            st.info(f"📌 **Tip:** {tip}")
        else:
            st.warning("Make a prediction first to get crop-specific tips")
    
    if st.button("📊 Analyze Prediction", use_container_width=True):
        if context:
            analysis = chatbot.analyze_prediction(
                crop=context.get('crop', ''),
                state=context.get('state', ''),
                predicted_yield=context.get('predicted_yield', 0),
                inputs=context.get('features_dict', {})
            )
            st.info(f"📈 **Analysis:** {analysis}")
        else:
            st.warning("Make a prediction first to get analysis")


# Main chat area
st.markdown("### 💬 Conversation")

# Display chat history
chat_container = st.container()
with chat_container:
    history = session.get_chat_history()
    
    if not history:
        st.info("👋 Hello! I'm your agricultural advisor. Start by asking me about crop yields, farming practices, or how to improve your predictions!")
        
        # Suggested starter questions
        st.markdown("**Sample questions you can ask:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
- What factors affect crop yield?
- How do I increase fertilizer efficiency?
- What's the optimal pH for different crops?
- Explain crop rotation benefits
            """)
        
        with col2:
            st.markdown("""
- How does rainfall affect wheat?
- Best practices for soil management?
- When should I apply fertilizers?
- How to maximize profit margins?
            """)
    else:
        for msg in history:
            if msg["role"] == "user":
                st.markdown(f"""
<div class='user-message'>
    <strong>You:</strong> {msg['content']}
</div>
""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
<div class='bot-message'>
    <strong>🤖 Advisor:</strong> {msg['content']}
</div>
""", unsafe_allow_html=True)


# Chat input and processing
st.divider()
st.markdown("### 📨 Your Message")

# Use columns for better layout
col1, col2 = st.columns([5, 1])

with col1:
    user_input = st.text_input(
        label="Type your question or request:",
        placeholder="Ask about yield prediction, farming practices, fertilizer, weather...",
        label_visibility="collapsed",
        key="chat_input"
    )

with col2:
    send_button = st.button("Send", use_container_width=True, type="primary")


# Process user input
if send_button and user_input:
    # Add user message to history
    session.add_message("user", user_input)
    
    # Show typing indicator
    with st.spinner("🤖 Advisor is thinking..."):
        # Prepare context and get response
        system_prompt = session.get_system_prompt()
        messages = session.format_messages_for_api(user_input)
        context = session.get_prediction_context()
        
        # Get chatbot response
        bot_response = chatbot.process_user_input(
            user_message=user_input,
            conversation_history=messages[:-1],  # Exclude current user message
            system_prompt=system_prompt,
            prediction_data=context
        )
    
    # Add bot message to history
    session.add_message("assistant", bot_response)
    
    # Rerun to display new message
    st.rerun()


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.9em;'>
    <p>🌾 Powered by OpenAI GPT-3.5 | Agricultural ML Model</p>
    <p>Disclaimer: This advisor provides guidance based on data and models. Please verify with local agricultural experts before making major decisions.</p>
</div>
""", unsafe_allow_html=True)
