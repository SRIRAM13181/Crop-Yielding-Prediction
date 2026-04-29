import streamlit as st
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
from plotly.subplots import make_subplots  # type: ignore
import pandas as pd
import numpy as np
from datetime import datetime

from utils import (
    predict_yield,
    get_model_metrics,
    get_feature_importance,
    get_recommendations,
)
from session_manager import get_session
from auth import initialize_auth, show_login_page, UserDatabase
from export_utils import export_to_csv, export_to_excel, export_to_pdf, get_export_filename

# Initialize authentication
initialize_auth()

# Page setup
st.set_page_config(
    page_title="Crop Yield Predictor",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling
st.markdown(
    """
    <style>
        .main-header {font-size: 3rem; font-weight: 700; color: #2E7D32; text-align: center;}
        .metric-card {background: #f6f9fc; padding: 1rem; border-radius: .65rem;}
        .stButton>button {background-color:#2E7D32;color:white;font-weight:600;border-radius:.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Check authentication
if not st.session_state.authenticated:
    show_login_page()
    st.stop()

# Sidebar: User info and logout
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state.username}")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_id = None
        st.rerun()
    st.divider()

# Sidebar navigation
st.sidebar.title("🌾 Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Home - Predict Yield",
        "🤖 AI Assistant ChatBot",
        "📊 History & Export",
        "📤 Batch Upload",
        "📊 Model Analytics",
        "🔄 Compare Scenarios",
        "🎯 Yield Optimizer",
        "💡 Recommendations",
    ],
)

# Lookup maps
soil_map = {"Loamy": 0, "Clay": 1, "Sandy": 2}
crop_map = {"Wheat": 0, "Rice": 1, "Maize": 2, "Sugarcane": 3}

indian_states = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
]
state_map = {state: idx for idx, state in enumerate(indian_states)}

# Session state for history
if "predictions_history" not in st.session_state:
    st.session_state.predictions_history = []

# Initialize session manager for chatbot
session = get_session()

if page == "🏠 Home - Predict Yield":
    st.markdown('<h1 class="main-header">🌾 Crop Yield Prediction System</h1>', unsafe_allow_html=True)
    st.info(
        "🌍 Supports all 36 Indian states and union territories. Retrain your model with pan-India data for best accuracy."
    )
    st.markdown("### Enter details to predict yield and profitability")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🌦️ Environment")
        rainfall = st.number_input("📨 Rainfall (mm)", min_value=0.0, step=0.1, value=100.0)
        temperature = st.number_input("🌡️ Temperature (°C)", min_value=-10.0, step=0.1, value=26.0)
        humidity = st.number_input("💧 Humidity (%)", min_value=0.0, max_value=100.0, step=0.1, value=65.0)

        st.subheader("🧪 Soil Nutrients")
        N = st.number_input("Nitrogen (kg/ha)", min_value=0.0, step=0.1, value=35.0)
        P = st.number_input("Phosphorus (kg/ha)", min_value=0.0, step=0.1, value=20.0)
        K = st.number_input("Potassium (kg/ha)", min_value=0.0, step=0.1, value=25.0)
        pH = st.number_input("Soil pH", min_value=0.0, max_value=14.0, step=0.1, value=6.5)

    with col2:
        st.subheader("🌱 Crop & Location")
        crop = st.selectbox("Crop", list(crop_map.keys()))
        soil_type = st.selectbox("Soil Type", list(soil_map.keys()))
        state = st.selectbox("State / Union Territory", indian_states, index=indian_states.index("Maharashtra"))

        st.subheader("💰 Economics")
        acres = st.number_input("Total Acres", min_value=0.1, step=0.1, value=2.0)
        market_price = st.number_input("Market Price (₹/kg)", min_value=1.0, step=1.0, value=45.0)
        cost_per_acre = st.number_input("Cost per Acre (₹)", min_value=0.0, step=100.0, value=12000.0)

    predict_btn = st.button("🔍 Predict Yield", use_container_width=True)

    if predict_btn:
        try:
            features = [
                rainfall,
                temperature,
                humidity,
                N,
                P,
                K,
                pH,
                soil_map[soil_type],
                crop_map[crop],
                state_map[state],
            ]

            yield_per_acre = float(predict_yield(features))
            total_production = yield_per_acre * acres
            total_revenue = total_production * market_price
            total_cost = cost_per_acre * acres
            total_profit = total_revenue - total_cost
            profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0

            st.session_state.predictions_history.append(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "crop": crop,
                    "state": state,
                    "yield_per_acre": yield_per_acre,
                    "total_profit": total_profit,
                }
            )

            # Save to database
            if st.session_state.authenticated and st.session_state.user_id:
                try:
                    st.session_state.db.save_prediction(
                        user_id=st.session_state.user_id,
                        crop=crop,
                        state=state,
                        rainfall=rainfall,
                        temperature=temperature,
                        humidity=humidity,
                        nitrogen=N,
                        phosphorus=P,
                        potassium=K,
                        pH=pH,
                        soil_type=soil_type,
                        predicted_yield=yield_per_acre,
                        total_acres=acres,
                        market_price=market_price,
                        cost_per_acre=cost_per_acre,
                        total_profit=total_profit
                    )
                except Exception as e:
                    st.warning(f"⚠️ Could not save to database: {str(e)}")

            # Save prediction context for chatbot
            session.set_prediction_context({
                "crop": crop,
                "state": state,
                "predicted_yield": yield_per_acre,
                "total_production": total_production,
                "total_profit": total_profit,
                "market_price": market_price,
                "features_dict": {
                    "rainfall": rainfall,
                    "temperature": temperature,
                    "humidity": humidity,
                    "nitrogen": N,
                    "phosphorus": P,
                    "potassium": K,
                    "pH": pH,
                    "soil_type": soil_type,
                }
            })

            st.markdown("### 📊 Prediction Summary")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Yield / Acre", f"{yield_per_acre:.2f} kg")
            m2.metric("Total Production", f"{total_production:,.2f} kg")
            m3.metric("Net Profit", f"₹{total_profit:,.0f}", delta=f"{profit_margin:.1f}% margin")
            m4.metric("Total Revenue", f"₹{total_revenue:,.0f}")

            st.markdown("### 💼 Financial Breakdown")
            breakdown = pd.DataFrame(
                {
                    "Metric": ["Total Acres", "Market Price (₹/kg)", "Cost per Acre", "Total Cost", "Net Profit"],
                    "Value": [
                        f"{acres:.1f}",
                        f"₹{market_price:.2f}",
                        f"₹{cost_per_acre:,.0f}",
                        f"₹{total_cost:,.0f}",
                        f"₹{total_profit:,.0f}",
                    ],
                }
            )
            st.dataframe(breakdown, use_container_width=True, hide_index=True)

            st.markdown("### 📈 Visual Insights")
            crops = ["Wheat", "Rice", "Maize", "Sugarcane"]
            base_yields = [45, 60, 50, 80]
            if crop in crops:
                base_yields[crops.index(crop)] = yield_per_acre

            # Yield comparison bar
            fig_yield = go.Figure(
                data=[
                    go.Bar(
                        x=crops,
                        y=base_yields,
                        marker=dict(color=["#4ECDC4" if c != crop else "#FF6B6B" for c in crops]),
                        text=[f"{val:.1f} kg" for val in base_yields],
                        textposition="outside",
                    )
                ]
            )
            fig_yield.update_layout(title="Yield Comparison", yaxis_title="kg/acre", height=400, showlegend=False)
            st.plotly_chart(fig_yield, use_container_width=True)

            # Financial breakdown pie
            fig_fin = go.Figure(
                data=[
                    go.Pie(
                        labels=["Revenue", "Cost", "Profit"],
                        values=[max(total_revenue, 0), max(total_cost, 0), max(total_profit, 0)],
                        hole=0.45,
                        marker=dict(colors=["#1f77b4", "#ff7f0e", "#2ca02c"]),
                    )
                ]
            )
            fig_fin.update_layout(title="Financial Breakdown", height=400)
            st.plotly_chart(fig_fin, use_container_width=True)

            st.markdown("### 💡 Recommendations")
            tips = get_recommendations(features, yield_per_acre, crop)
            for idx, tip in enumerate(tips, start=1):
                st.info(f"**{idx}.** {tip}")

            # Download CSV report
            report_df = pd.DataFrame(
                {
                    "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "Crop": [crop],
                    "State": [state],
                    "Yield_per_Acre": [yield_per_acre],
                    "Total_Production": [total_production],
                    "Total_Revenue": [total_revenue],
                    "Total_Cost": [total_cost],
                    "Net_Profit": [total_profit],
                    "Profit_Margin_%": [profit_margin],
                }
            )
            st.download_button(
                "📥 Download report",
                report_df.to_csv(index=False),
                file_name=f"crop_yield_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")

elif page == "🤖 AI Assistant ChatBot":
    # Import chatbot modules
    from chatbot import create_chatbot, MockChatbot
    
    # Page header
    st.markdown('<h1 style="text-align: center; color: #2E7D32;">🤖 Agricultural Advisor Chatbot</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Get expert guidance on crop yield predictions, farming practices, and optimization strategies</p>', unsafe_allow_html=True)
    
    # Initialize chatbot
    @st.cache_resource
    def get_chatbot_instance():
        bot = create_chatbot()
        if bot is None:
            st.warning("⚠️ Running in mock mode (demo). To enable real AI responses, add your OpenAI API key to `.streamlit/secrets.toml`")
            return MockChatbot()
        return bot
    
    try:
        chatbot = get_chatbot_instance()
    except Exception as e:
        st.error(f"Error initializing chatbot: {str(e)}")
        chatbot = None
    
    # Sidebar controls
    with st.sidebar:
        st.markdown("### 📱 Chat Controls")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                session.clear_history()
                st.rerun()
        with col2:
            if st.button("📋 Summary", use_container_width=True):
                st.info(f"**Chat Summary:** {session.get_conversation_summary()}")
        
        st.divider()
        
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
        
        st.markdown("### ⚡ Quick Actions")
        if st.button("💡 Get Farming Tip", use_container_width=True):
            if chatbot and context:
                tip = chatbot.get_quick_tip(context.get('crop', 'Wheat'), context.get('state', 'Punjab'))
                st.info(f"📌 **Tip:** {tip}")
            elif chatbot:
                st.warning("Make a prediction first to get crop-specific tips")
        
        if st.button("📊 Analyze Prediction", use_container_width=True):
            if chatbot and context:
                analysis = chatbot.analyze_prediction(
                    crop=context.get('crop', ''),
                    state=context.get('state', ''),
                    predicted_yield=context.get('predicted_yield', 0),
                    inputs=context.get('features_dict', {})
                )
                st.info(f"📈 **Analysis:** {analysis}")
            elif chatbot:
                st.warning("Make a prediction first to get analysis")
    
    # Chat area
    st.markdown("### 💬 Conversation")
    
    history = session.get_chat_history()
    if not history:
        st.info("👋 Hello! I'm your agricultural advisor. Start by asking me about crop yields, farming practices, or how to improve your predictions!")
        st.markdown("**Sample questions:**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
- What factors affect crop yield?
- How do I increase fertilizer efficiency?
- What's the optimal pH for different crops?
            """)
        with col2:
            st.markdown("""
- How does rainfall affect wheat?
- Best practices for soil management?
- When should I apply fertilizers?
            """)
    else:
        for msg in history:
            if msg["role"] == "user":
                st.markdown(f'<div style="background-color: #e3f2fd; padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #1976d2;"><strong>You:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div style="background-color: #f5f5f5; padding: 12px 16px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #4caf50;"><strong>🤖 Advisor:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### 📨 Your Message")
    
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Type your question or request:",
            placeholder="Ask about yield prediction, farming practices, fertilizer, weather...",
            key="chat_input"
        )
    
    with col2:
        send_button = st.button("Send", use_container_width=True, type="primary")
    
    if send_button and user_input and chatbot:
        session.add_message("user", user_input)
        with st.spinner("🤖 Advisor is thinking..."):
            system_prompt = session.get_system_prompt()
            messages = session.format_messages_for_api(user_input)
            context = session.get_prediction_context()
            
            bot_response = chatbot.process_user_input(
                user_message=user_input,
                conversation_history=messages[:-1],
                system_prompt=system_prompt,
                prediction_data=context
            )
        
        session.add_message("assistant", bot_response)
        st.rerun()

elif page == "📊 Model Analytics":
    st.title("📊 Model Analytics & Feature Insights")
    try:
        metrics = get_model_metrics()
        fi = get_feature_importance()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("R² Score", f"{metrics.get('r2_score', 0):.3f}")
        c2.metric("MAE", f"{metrics.get('mae', 0):.2f}")
        c3.metric("RMSE", f"{metrics.get('rmse', 0):.2f}")
        c4.metric("Training Samples", str(metrics.get("n_samples", "N/A")))

        if fi:
            st.markdown("### 🔍 Feature Importance")
            fi_df = pd.DataFrame({"feature": list(fi.keys()), "importance": list(fi.values())})
            fig_fi = px.bar(fi_df, x="importance", y="feature", orientation="h", color="importance", color_continuous_scale="Greens")
            fig_fi.update_layout(height=500)
            st.plotly_chart(fig_fi, use_container_width=True)
        else:
            st.warning("No feature importance data available. Train the model to refresh metrics.")
    except Exception as exc:  # pragma: no cover
        st.error(f"Unable to load analytics: {exc}")

elif page == "🔄 Compare Scenarios":
    st.title("🔄 Scenario Comparison")
    st.caption("Configure up to 4 what-if scenarios to identify best inputs.")
    scenario_count = st.slider("Number of scenarios", 2, 4, 2)
    scenarios = []
    for i in range(scenario_count):
        with st.expander(f"Scenario {i+1}", expanded=(i == 0)):
            c1, c2 = st.columns(2)
            with c1:
                s_rainfall = st.number_input(f"Rainfall (mm) #{i+1}", value=100.0, step=1.0, key=f"r{i}")
                s_temp = st.number_input(f"Temperature (°C) #{i+1}", value=26.0, step=0.5, key=f"t{i}")
                s_hum = st.number_input(f"Humidity (%) #{i+1}", value=65.0, step=0.5, key=f"h{i}")
                s_N = st.number_input(f"N (kg/ha) #{i+1}", value=35.0, step=0.5, key=f"n{i}")
                s_P = st.number_input(f"P (kg/ha) #{i+1}", value=20.0, step=0.5, key=f"p{i}")
                s_K = st.number_input(f"K (kg/ha) #{i+1}", value=25.0, step=0.5, key=f"k{i}")
                s_pH = st.number_input(f"Soil pH #{i+1}", value=6.5, step=0.1, key=f"ph{i}")
            with c2:
                s_crop = st.selectbox(f"Crop #{i+1}", list(crop_map.keys()), key=f"c{i}")
                s_soil = st.selectbox(f"Soil type #{i+1}", list(soil_map.keys()), key=f"s{i}")
                s_state = st.selectbox(f"State #{i+1}", indian_states, key=f"st{i}")
                s_acres = st.number_input(f"Acres #{i+1}", value=2.0, step=0.5, key=f"a{i}")
                s_price = st.number_input(f"Market Price (₹/kg) #{i+1}", value=45.0, step=1.0, key=f"mp{i}")

            scenarios.append(
                {
                    "features": [
                        s_rainfall,
                        s_temp,
                        s_hum,
                        s_N,
                        s_P,
                        s_K,
                        s_pH,
                        soil_map[s_soil],
                        crop_map[s_crop],
                        state_map[s_state],
                    ],
                    "crop": s_crop,
                    "acres": s_acres,
                    "price": s_price,
                    "name": f"Scenario {i+1}",
                }
            )

    if st.button("Compare scenarios"):
        results = []
        for scenario in scenarios:
            try:
                yld = float(predict_yield(scenario["features"]))
                prod = yld * scenario["acres"]
                rev = prod * scenario["price"]
                results.append(
                    {
                        "Scenario": scenario["name"],
                        "Crop": scenario["crop"],
                        "Yield (kg/acre)": yld,
                        "Total Production (kg)": prod,
                        "Revenue (₹)": rev,
                    }
                )
            except Exception as exc:
                st.error(f"{scenario['name']} failed: {exc}")

        if results:
            df_results = pd.DataFrame(results)
            st.dataframe(df_results, use_container_width=True)

            fig_compare = make_subplots(
                rows=1,
                cols=2,
                subplot_titles=("Yield per Acre", "Total Revenue"),
                specs=[[{"type": "bar"}, {"type": "bar"}]],
            )
            fig_compare.add_trace(
                go.Bar(x=df_results["Scenario"], y=df_results["Yield (kg/acre)"], marker=dict(color="#4ECDC4")), row=1, col=1
            )
            fig_compare.add_trace(
                go.Bar(x=df_results["Scenario"], y=df_results["Revenue (₹)"], marker=dict(color="#FF6B6B")), row=1, col=2
            )
            fig_compare.update_layout(height=450, showlegend=False)
            st.plotly_chart(fig_compare, use_container_width=True)

elif page == "🎯 Yield Optimizer":
    st.title("🎯 Yield Optimizer")
    st.caption("Use the trained model to explore thousands of what-if combinations and surface the most profitable setup.")

    col_goal, col_samples, col_seed = st.columns(3)
    with col_goal:
        optimize_for = st.selectbox("Optimization Goal", ["Maximize Yield", "Maximize Profit"])
    with col_samples:
        sample_count = st.number_input("Sample Size", min_value=100, max_value=5000, step=100, value=1000,
                                       help="Higher sample size explores more combinations but takes longer.")
    with col_seed:
        random_seed = st.number_input("Random Seed", min_value=0, max_value=9999, value=42, step=1)

    st.markdown("#### Input Ranges")
    r1, r2, r3 = st.columns(3)
    rainfall_range = r1.slider("Rainfall (mm)", 20.0, 400.0, (80.0, 200.0))
    temp_range = r2.slider("Temperature (°C)", 5.0, 45.0, (20.0, 32.0))
    humidity_range = r3.slider("Humidity (%)", 10.0, 100.0, (40.0, 85.0))

    n1, n2, n3 = st.columns(3)
    N_range = n1.slider("Nitrogen (kg/ha)", 5.0, 80.0, (25.0, 45.0))
    P_range = n2.slider("Phosphorus (kg/ha)", 5.0, 60.0, (15.0, 35.0))
    K_range = n3.slider("Potassium (kg/ha)", 5.0, 60.0, (15.0, 35.0))

    misc_col1, misc_col2 = st.columns(2)
    with misc_col1:
        optimizer_crop = st.selectbox("Target Crop", list(crop_map.keys()))
        optimizer_soil = st.selectbox("Soil Type Preference", list(soil_map.keys()))
        optimizer_state = st.selectbox("State / UT Focus", indian_states)
    with misc_col2:
        optimizer_acres = st.number_input("Acres under cultivation", min_value=0.5, step=0.5, value=5.0)
        optimizer_price = st.number_input("Expected Market Price (₹/kg)", min_value=1.0, step=1.0, value=50.0)
        optimizer_cost = st.number_input("Cost per Acre (₹)", min_value=0.0, step=500.0, value=15000.0)

    if st.button("🚀 Run Optimizer"):
        rng = np.random.default_rng(int(random_seed))
        soils = list(soil_map.keys())

        results = []
        for _ in range(int(sample_count)):
            rainfall = float(rng.uniform(*rainfall_range))
            temp = float(rng.uniform(*temp_range))
            hum = float(rng.uniform(*humidity_range))
            nitrogen = float(rng.uniform(*N_range))
            phos = float(rng.uniform(*P_range))
            pot = float(rng.uniform(*K_range))
            ph = float(rng.uniform(5.0, 7.5))
            soil_choice = optimizer_soil if rng.random() < 0.5 else rng.choice(soils)
            state_choice = optimizer_state if rng.random() < 0.5 else rng.choice(indian_states)
            crop_choice = optimizer_crop if rng.random() < 0.4 else rng.choice(list(crop_map.keys()))

            features = [
                rainfall,
                temp,
                hum,
                nitrogen,
                phos,
                pot,
                ph,
                soil_map[soil_choice],
                crop_map[crop_choice],
                state_map[state_choice],
            ]
            try:
                yld = float(predict_yield(features))
            except Exception:
                continue
            production = yld * optimizer_acres
            revenue = production * optimizer_price
            profit = revenue - (optimizer_acres * optimizer_cost)

            results.append(
                {
                    "Crop": crop_choice,
                    "State": state_choice,
                    "Soil": soil_choice,
                    "Rainfall": rainfall,
                    "Temperature": temp,
                    "Humidity": hum,
                    "N": nitrogen,
                    "P": phos,
                    "K": pot,
                    "pH": ph,
                    "Yield (kg/acre)": yld,
                    "Total Profit (₹)": profit,
                }
            )

        if not results:
            st.error("Optimizer could not generate valid scenarios. Try adjusting the ranges.")
        else:
            df = pd.DataFrame(results)
            sort_col = "Yield (kg/acre)" if optimize_for == "Maximize Yield" else "Total Profit (₹)"
            df_sorted = df.sort_values(sort_col, ascending=False)

            st.subheader("Top Recommended Strategies")
            st.dataframe(df_sorted.head(10), use_container_width=True)

            st.markdown("#### Yield vs Rainfall (Top 200 Scenarios)")
            top_plot_df = df_sorted.head(200).copy()
            top_plot_df["size_metric"] = (top_plot_df["Total Profit (₹)"].clip(lower=0) + 1).astype(float)
            fig_opt = px.scatter(
                top_plot_df,
                x="Rainfall",
                y="Yield (kg/acre)",
                color="Total Profit (₹)",
                size="size_metric",
                hover_data=["Crop", "State", "N", "P", "K", "pH"],
                color_continuous_scale="Viridis",
                size_max=24,
            )
            fig_opt.update_layout(height=450)
            st.plotly_chart(fig_opt, use_container_width=True)

            st.download_button(
                "⬇️ Download all optimizer results",
                df_sorted.to_csv(index=False),
                file_name="optimizer_results.csv",
                mime="text/csv",
            )

elif page == "💡 Recommendations":
    st.title("💡 Smart Recommendations")
    st.caption("Enter current conditions to receive actionable agronomy tips.")

    c1, c2 = st.columns(2)
    with c1:
        rec_rain = st.number_input("Rainfall (mm)", value=90.0, step=1.0)
        rec_temp = st.number_input("Temperature (°C)", value=27.0, step=0.5)
        rec_hum = st.number_input("Humidity (%)", value=60.0, step=0.5)
        rec_N = st.number_input("Nitrogen (kg/ha)", value=32.0, step=0.5)
        rec_P = st.number_input("Phosphorus (kg/ha)", value=18.0, step=0.5)
        rec_K = st.number_input("Potassium (kg/ha)", value=22.0, step=0.5)
        rec_pH = st.number_input("Soil pH", value=6.3, step=0.1)
    with c2:
        rec_crop = st.selectbox("Crop", list(crop_map.keys()))
        rec_soil = st.selectbox("Soil type", list(soil_map.keys()))
        rec_state = st.selectbox("State / UT", indian_states)

    if st.button("Get recommendations"):
        feats = [
            rec_rain,
            rec_temp,
            rec_hum,
            rec_N,
            rec_P,
            rec_K,
            rec_pH,
            soil_map[rec_soil],
            crop_map[rec_crop],
            state_map[rec_state],
        ]
        try:
            current_yield = float(predict_yield(feats))
            st.success(f"Predicted yield: **{current_yield:.2f} kg/acre**")
            recs = get_recommendations(feats, current_yield, rec_crop)
            for idx, tip in enumerate(recs, start=1):
                st.write(f"**{idx}.** {tip}")
        except Exception as exc:
            st.error(f"Couldn't generate recommendations: {exc}")

st.sidebar.markdown("---")
st.sidebar.markdown("### Recent Predictions")
if st.session_state.predictions_history:
    for entry in st.session_state.predictions_history[-5:]:
        st.sidebar.text(f"{entry['crop']} ({entry['state']}) → {entry['yield_per_acre']:.1f} kg/acre")
else:
    st.sidebar.caption("Predict yield to populate history.")

st.sidebar.markdown("---")
st.sidebar.caption("🌱 Smart Farming using AI 🚜")
