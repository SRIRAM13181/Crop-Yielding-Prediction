# Crop Yield Prediction & AI Advisory System

An intelligent **crop yield prediction system** with **AI-powered agricultural chatbot** using machine learning and conversational AI. Supports all 36 Indian states with real-time yield forecasting, financial analysis, and expert agronomic guidance.

---

## 🌟 Features

### **Core Prediction Capabilities**
- ✅ Multi-crop yield prediction (Wheat, Rice, Maize, Sugarcane)
- ✅ Pan-India support (36 states & union territories)
- ✅ Financial analysis (revenue, profit, cost breakdown)
- ✅ Feature importance visualization
- ✅ Scenario comparison & optimization

### **🤖 NEW: AI-Powered Agricultural Chatbot (Phase 1)**
- ✅ OpenAI GPT-3.5-turbo conversational AI
- ✅ Multi-turn dialogue with context awareness
- ✅ Step-by-step user guidance
- ✅ Crop-specific farming tips
- ✅ Prediction analysis & recommendations
- ✅ Mock mode (demo without API key)
- ✅ Conversation history & context tracking

### **Additional Pages**
- 📊 Model Analytics (R², MAE, RMSE, feature importance)
- 🔄 Scenario Comparison (side-by-side what-if analysis)
- 🎯 Yield Optimizer (find best parameter ranges)
- 💡 Recommendations (agronomic guidance by crop)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   cd CropYeildingPrediction_Python
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up OpenAI API key** (for chatbot)
   ```bash
   # Create .streamlit/secrets.toml
   # Copy from .streamlit/secrets.toml.example and replace with your API key
   
   # Get free API key: https://platform.openai.com/api-keys
   # Add to .streamlit/secrets.toml:
   OPENAI_API_KEY = "your-api-key-here"
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

5. **Access the web interface**
   - Opens at `http://localhost:8501`
   - Navigate between pages using the sidebar

---

## 📖 Usage Guide

### 🏠 Home - Predict Yield

1. **Enter Environmental Data**
   - Rainfall (mm), Temperature (°C), Humidity (%)

2. **Set Soil Nutrients**
   - Nitrogen, Phosphorus, Potassium (kg/ha)
   - Soil pH (0-14)

3. **Select Crop & Location**
   - Choose crop: Wheat, Rice, Maize, Sugarcane
   - Choose soil type: Loamy, Clay, Sandy
   - Select state from 36 options

4. **Input Economic Data**
   - Total acres
   - Market price (₹/kg)
   - Cost per acre

5. **Get Prediction**
   - Model predicts yield/acre
   - Shows total production, revenue, profit
   - Provides recommendations

6. **📱 Use with Chatbot**
   - Go to "🤖 AI Assistant ChatBot"
   - Your prediction context is pre-loaded
   - Ask follow-up questions to the AI advisor

---

### 🤖 AI Assistant ChatBot

#### **Chatbot Features**
- **Smart Q&A**: Ask about crops, yield prediction, farming practices
- **Context-Aware**: References your recent prediction automatically
- **Multi-turn Dialogue**: Follow-up questions maintain conversation history
- **Quick Actions**:
  - 💡 Get Farming Tip
  - 📊 Analyze Prediction
  - 📋 View Chat Summary

#### **Sample Questions**
```
"What factors affect crop yield?"
"How do I increase fertilizer efficiency for wheat?"
"What's the optimal pH for rice in Punjab?"
"Why did I get that yield prediction?"
"How can I improve my profit margin?"
"When should I apply nitrogen fertilizer?"
"What's the difference between crop rotation strategies?"
```

#### **Chat Management**
- 🗑️ **Clear Chat**: Start fresh conversation
- 📋 **Summary**: See topics discussed
- 🎯 **Context**: View current prediction details
- ⚡ **Quick Actions**: Get tips or analysis instantly

---

## 📊 Model Details

### **ML Model**
- **Algorithm**: Random Forest & Histogram Gradient Boosting (GridSearchCV)
- **Features**: 10 input parameters (environmental, soil, crop, location)
- **Output**: Predicted yield (kg/acre)
- **Metrics**: R², MAE, RMSE calculated on test set
- **Saved**: `models/yield_model.pkl`

### **Input Features**
1. Rainfall (mm)
2. Temperature (°C)
3. Humidity (%)
4. Nitrogen (kg/ha)
5. Phosphorus (kg/ha)
6. Potassium (kg/ha)
7. Soil pH
8. Soil Type (Loamy=0, Clay=1, Sandy=2)
9. Crop (Wheat=0, Rice=1, Maize=2, Sugarcane=3)
10. State (0-35 encoded)

---

## 🔧 Configuration

### `.streamlit/config.toml`
- UI theme (green color: #2E7D32)
- Font, display mode, logging level

### `.streamlit/secrets.toml` (Git-ignored)
```toml
OPENAI_API_KEY = "sk-..."
# Add other API keys here as needed
```

### `.gitignore`
- Prevents accidental commit of API keys
- Excludes model backups, logs, virtual environments

---

## 📁 Project Structure

```
CropYeildingPrediction_Python/
├── app.py                          # Main Streamlit app (Home + 5 pages)
├── pages/
│   └── chatbot.py                  # Chatbot page (auto-loaded by Streamlit)
├── chatbot.py                      # OpenAI chatbot integration
├── session_manager.py              # Conversation history & context
├── utils.py                        # Prediction & recommendation functions
├── preprocessor.py                 # Data preprocessing
├── train_model.py                  # Model training script
├── system.py / system_utils.py     # Utility functions
├── models/
│   ├── yield_model.pkl             # Trained ML model
│   ├── model_metrics.json          # Model performance metrics
│   ├── feature_importance.json     # Feature importance scores
│   └── data/
│       └── crop_data.csv           # Training dataset
├── .streamlit/
│   ├── config.toml                 # Streamlit configuration
│   ├── secrets.toml                # API keys (git-ignored)
│   └── secrets.toml.example        # Template for secrets
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git exclusions
└── README.md                       # This file
```

---

## 🔐 API Keys & Security

### OpenAI API Setup
1. Go to [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Copy and paste into `.streamlit/secrets.toml`:
   ```toml
   OPENAI_API_KEY = "sk-proj-..."
   ```

### Security Best Practices
- ✅ Never commit `secrets.toml` (use `.gitignore`)
- ✅ Use `secrets.toml.example` as template
- ✅ Recreate `secrets.toml` on each machine
- ✅ For Streamlit Cloud, add secrets via web UI

### Streamlit Cloud Deployment
1. Push code to GitHub (without secrets.toml)
2. Connect Streamlit Cloud to GitHub repo
3. Add secrets via "Settings → Secrets"
4. Deploy

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | latest | Web UI framework |
| pandas | latest | Data manipulation |
| numpy | latest | Numerical computing |
| scikit-learn | latest | ML models |
| joblib | latest | Model serialization |
| plotly | latest | Interactive charts |
| openai | ≥1.0.0 | ChatGPT API |
| streamlit-chat | ≥0.1.0 | Chat UI component |

---

## 🧪 Testing the Chatbot

### **Without API Key (Mock Mode)**
- App auto-detects missing key
- Chatbot enters "mock mode" with predefined responses
- Perfect for demo/testing

### **With API Key (Real AI)**
1. Add `OPENAI_API_KEY` to `.streamlit/secrets.toml`
2. Restart Streamlit
3. Chatbot now uses real GPT-3.5-turbo

### **Testing Workflow**
1. Go to "🏠 Home - Predict Yield"
2. Enter sample data (use defaults)
3. Click "🔍 Predict Yield"
4. Go to "🤖 AI Assistant ChatBot"
5. Ask: "Why did I get that yield?"
6. Bot should reference your prediction context

---

## 🚀 Future Enhancements (Phases 2-7)

- [ ] **Phase 2**: User authentication & prediction history database
- [ ] **Phase 3**: CSV/PDF/Excel export functionality
- [ ] **Phase 4**: Real-time weather API integration (OpenWeatherMap)
- [ ] **Phase 5**: Batch CSV upload & prediction
- [ ] **Phase 6**: Mobile-responsive UI & advanced dashboards
- [ ] **Phase 7**: Streamlit Cloud deployment & CI/CD

---

## 📞 Support & Troubleshooting

### **Chatbot not responding?**
- Check API key in `.streamlit/secrets.toml`
- Verify internet connection
- Check OpenAI account quota/billing

### **Model predictions seem off?**
- Ensure `models/yield_model.pkl` exists
- Retrain if using new data (run `train_model.py`)
- Verify input feature ranges

### **Streamlit not starting?**
```bash
# Clear cache
streamlit cache clear

# Run with verbose output
streamlit run app.py --logger.level=debug
```

---

## 📄 License

[Your License Here]

---

## 👨‍💻 Development Notes

- **Framework**: Streamlit (no React/Angular needed)
- **ML**: Scikit-learn (production-ready models)
- **NLP**: OpenAI API (enterprise-grade LLM)
- **Storage**: SQLite for future user sessions
- **Deployment**: Streamlit Cloud (free tier available)

---

## 🎯 Roadmap Summary

| Phase | Feature | Timeline | Status |
|-------|---------|----------|--------|
| 1 | AI Chatbot | Week 1-2 | ⏳ Planned |
| 2 | User Auth & History | Week 2-3 | ⏳ Planned |
| 3 | Data Export | Week 3-4 | ⏳ Planned |
| 4 | Weather Integration | Week 4-5 | ⏳ Planned |
| 5 | Batch Upload | Week 5 | ⏳ Planned |
| 6 | Mobile UI & Dashboards | Week 6-7 | ⏳ Planned |
| 7 | Deployment | Week 8 | ⏳ Planned |

---

## 🙏 Acknowledgments

Built with ❤️ using **Streamlit**, **Scikit-learn**, and **OpenAI GPT-3.5-turbo**

Happy farming! 🌾🤖

# Crop-Yielding-Prediction
