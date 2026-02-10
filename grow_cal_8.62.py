import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Master Grow Logic", page_icon="🧪", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #d0d0d0; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 8px; border: 1px solid #374151; }
    div[data-testid="stExpander"] { background-color: #1f2937; border-radius: 8px; }
    h1, h2, h3 { color: #10b981; }
    .big-font { font-size: 20px !important; font-weight: bold; color: #10b981; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: GLOBAL SETTINGS ---
with st.sidebar:
    st.title("⚙️ Global Config")
    currency_symbol = st.text_input("Currency Symbol", "$")
    kwh_cost = st.number_input("Electricity Cost (per kWh)", value=0.14, format="%.3f")
    grower_skill = st.slider("Grower Skill Level", 0.5, 1.5, 1.0, help="0.5=Newbie, 1.0=Average, 1.5=Master Grower")
    
    st.markdown("---")
    st.caption("Advanced Calibration")
    # Calibration variables for the logic engine
    GRAMS_PER_WATT_LED = st.number_input("Ref: Max LED Efficiency (g/w)", value=2.2)
    MAX_G_PER_SQFT = st.number_input("Ref: Max Density (g/sqft)", value=65.0)

# --- TAB STRUCTURE ---
tab_yield, tab_power, tab_extract, tab_reverse = st.tabs([
    "🧪 Yield Simulator", "⚡ Precision Energy", "🍯 Hash & Rosin", "🎯 Reverse Engineer"
])

# ==========================================
# TAB 1: YIELD SIMULATOR (LIEBIG'S LAW)
# ==========================================
with tab_yield:
    st.header("Yield Prediction Engine")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("1. Environment")
        length = st.number_input("Tent Length (ft)", 1, 20, 4)
        width = st.number_input("Tent Width (ft)", 1, 20, 4)
        sq_ft = length * width
        
        system_type = st.selectbox("Medium", ["Soil", "Coco Coir", "DWC/Hydro", "Aeroponics"])
        
    with col2:
        st.subheader("2. Lighting")
        true_watts = st.number_input("True Draw Watts (Wall)", 50, 2000, 600)
        light_type = st.selectbox("Light Tech", ["High-End LED (Bar)", "Budget LED (Quantum)", "HPS/CMH", "Blurple/CFL"])
        co2_supplement = st.checkbox("CO2 Supplementation (>1200ppm)")
        
    with col3:
        st.subheader("3. Biology")
        plant_count = st.number_input("Plant Count", 1, 50, 4)
        pot_size = st.number_input("Pot Size (Gallons)", 0.5, 30.0, 5.0)
        strain_type = st.selectbox("Genetics", ["Photoperiod Feminized", "Autoflower", "Regular/Bagseed"])
        training = st.multiselect("Training Methods", ["Topping", "LST", "Scrog (Net)", "Mainlining"])

    # --- THE LOGIC ENGINE ---
    # 1. Light Efficiency Coefficient
    if light_type == "High-End LED (Bar)": light_eff = 1.0
    elif light_type == "Budget LED (Quantum)": light_eff = 0.85
    elif light_type == "HPS/CMH": light_eff = 0.70
    else: light_eff = 0.50

    # 2. Medium Efficiency
    if system_type == "Aeroponics": med_eff = 1.25
    elif system_type == "DWC/Hydro": med_eff = 1.20
    elif system_type == "Coco Coir": med_eff = 1.10
    else: med_eff = 1.0 # Soil base
    
    # 3. Training Multiplier
    train_mult = 1.0 + (len(training) * 0.08) # 8% boost per training method
    if "Scrog (Net)" in training: train_mult += 0.05 # Bonus for Scrog
    
    # --- LIMITING FACTOR CALCULATIONS ---
    
    # LIMIT A: LIGHT LIMIT (Photosynthetic Ceiling)
    # CO2 releases the light ceiling. Without CO2, plants can only process so much light.
    co2_mult = 1.25 if co2_supplement else 1.0
    limit_light_g = (true_watts * GRAMS_PER_WATT_LED * light_eff * co2_mult)
    
    # LIMIT B: SPACE LIMIT (Canopy Saturation)
    # You cannot physically fit infinite buds in a 4x4.
    limit_space_g = sq_ft * MAX_G_PER_SQFT
    
    # LIMIT C: ROOT/PLANT LIMIT (Biological Capacity)
    # A single plant in a 1gal pot has a max biological output regardless of light/space.
    # Auto has lower ceiling per plant than Photo.
    plant_ceiling = 400 if strain_type == "Autoflower" else 800 
    
    # Hydro roots are more efficient per gallon
    root_eff = 1.5 if system_type in ["DWC/Hydro", "Aeroponics"] else 1.0
    
    # Calculate max yield based on pot size and plant count
    # Formula: diminishing returns on pot size.
    # Base 30g + (Gallons * 35g) * RootEff
    per_plant_max = (30 + (pot_size * 35 * root_eff)) 
    if per_plant_max > plant_ceiling: per_plant_max = plant_ceiling
    
    limit_root_g = per_plant_max * plant_count

    # --- FINAL CALCULATION ---
    # The yield is determined by the LOWEST of the three limits (Liebig's Law)
    bottleneck = min(limit_light_g, limit_space_g, limit_root_g)
    
    # Apply Grower Skill and Training modifiers to the bottleneck
    predicted_yield_g = bottleneck * grower_skill * train_mult * med_eff
    
    # Hard cap logic (cannot exceed theoretical max of the light source significantly)
    max_physics = true_watts * 3.0
    if predicted_yield_g > max_physics: predicted_yield_g = max_physics

    # --- DISPLAY RESULTS ---
    st.divider()
    
    # Metric Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Predicted Dry Weight", f"{predicted_yield_g:.0f} g", f"{(predicted_yield_g/28.35):.1f} oz")
    m2.metric("Efficiency (GPW)", f"{(predicted_yield_g/true_watts):.2f} g/w")
    m3.metric("Canopy Density", f"{(predicted_yield_g/sq_ft):.1f} g/sqft")
    m4.metric("Market Value (@ $150/oz)", f"{currency_symbol}{((predicted_yield_g/28.35)*150):.0f}")

    # Bottleneck Analysis
    st.markdown("### 🔍 Bottleneck Analysis")
    st.caption("Your yield is limited by the lowest bar below. Increase that factor to improve yield.")
    
    chart_data = pd.DataFrame({
        "Factor": ["Light Limit", "Space Limit", "Root/Plant Limit"],
        "Max Grams": [limit_light_g, limit_space_g, limit_root_g]
    })
    st.bar_chart(chart_data, x="Factor", y="Max Grams", color="#10b981")
    
    if bottleneck == limit_light_g:
        st.warning("⚠️ **Limiting Factor: LIGHT.** You have enough space and plants, but not enough wattage.")
    elif bottleneck == limit_space_g:
        st.warning("⚠️ **Limiting Factor: SPACE.** Your tent is too small for this much equipment/plants.")
    elif bottleneck == limit_root_g:
        st.warning("⚠️ **Limiting Factor: ROOTS.** Add more plants or bigger pots to utilize your light/space.")

# ==========================================
# TAB 2: PRECISION ENERGY
# ==========================================
with tab_power:
    st.header("Electricity Cost Calculator")
    
    st.write("Defining Cycle Duration:")
    c1, c2, c3 = st.columns(3)
    days_veg = c1.number_input("Days in Veg (18/6)", value=35)
    days_flower = c2.number_input("Days in Flower (12/12)", value=63)
    days_dry = c3.number_input("Days Drying/Curing (24/7 env)", value=14)
    
    st.subheader("Equipment Loadout")
    
    # Helper function for adding devices
    def add_device(name, watts, duty_veg, duty_flower, duty_dry):
        return {"name": name, "watts": watts, "veg_duty": duty_veg, "flower_duty": duty_flower, "dry_duty": duty_dry}

    # Default list
    default_devices = [
        add_device("Main Grow Light", true_watts, 1.0, 1.0, 0.0), # Light off during dry
        add_device("Inline Fan (Exhaust)", 60, 0.5, 1.0, 0.5),
        add_device("Clip Fans", 30, 1.0, 1.0, 1.0),
        add_device("Dehumidifier", 400, 0.1, 0.4, 0.3), # Runs more in flower
        add_device("AC Unit", 800, 0.0, 0.0, 0.0),
        add_device("Humidifier", 50, 0.5, 0.1, 0.0),
        add_device("Heater", 1000, 0.0, 0.0, 0.0)
    ]
    
    # Data Editor for fine-tuning
    df_devices = pd.DataFrame(default_devices)
    st.caption("Edit Watts and Duty Cycles (0.5 = 50% uptime). Set Duty to 0 if you don't use it.")
    edited_df = st.data_editor(df_devices, num_rows="dynamic")
    
    if st.button("Calculate Energy Bill"):
        total_kwh = 0
        phase_costs = {"Veg": 0, "Flower": 0, "Dry": 0}
        
        # Calculate per device
        for index, row in edited_df.iterrows():
            w = row['watts']
            
            # Veg Calculation (18 hours on * duty cycle) for light, else 24h * duty
            # Actually, duty cycle applies to the "Active Time". 
            # For lights: Veg is 18h. Duty 1.0 = 18h.
            # For fans: Veg is 24h. Duty 1.0 = 24h.
            
            # Simplified Logic:
            # Light is special case.
            if "Light" in row['name']:
                kwh_veg = (w * 18 * row['veg_duty'] * days_veg) / 1000
                kwh_flow = (w * 12 * row['flower_duty'] * days_flower) / 1000
                kwh_dry = 0 # Lights off
            else:
                kwh_veg = (w * 24 * row['veg_duty'] * days_veg) / 1000
                kwh_flow = (w * 24 * row['flower_duty'] * days_flower) / 1000
                kwh_dry = (w * 24 * row['dry_duty'] * days_dry) / 1000
            
            total_kwh += (kwh_veg + kwh_flow + kwh_dry)
            phase_costs["Veg"] += kwh_veg * kwh_cost
            phase_costs["Flower"] += kwh_flow * kwh_cost
            phase_costs["Dry"] += kwh_dry * kwh_cost
            
        total_cost = total_kwh * kwh_cost
        
        c_tot, c_g = st.columns(2)
        c_tot.metric("Total Cycle Cost", f"{currency_symbol}{total_cost:.2f}")
        
        # Pull yield from tab 1
        cost_per_gram = total_cost / predicted_yield_g if predicted_yield_g > 0 else 0
        c_g.metric("Electricity Cost per Gram", f"{currency_symbol}{cost_per_gram:.2f}")
        
        st.bar_chart(phase_costs)

# ==========================================
# TAB 3: HASH & ROSIN
# ==========================================
with tab_extract:
    st.header("Solventless Extraction")
    
    st.info("Input your harvest weight to see returns.")
    
    input_type = st.radio("Input Material", ["Dry Cured Flower", "Fresh Frozen (WPFF)"])
    
    col_in, col_calc = st.columns(2)
    
    with col_in:
        input_amount_oz = st.number_input("Input Weight (oz)", value=float(predicted_yield_g/28.35))
        input_g = input_amount_oz * 28.35
        
    with col_calc:
        if input_type == "Dry Cured Flower":
            st.subheader("Flower Rosin")
            return_rate = st.slider("Press Return %", 10, 30, 20)
            rosin_g = input_g * (return_rate / 100)
            st.metric("Expected Rosin", f"{rosin_g:.1f} g", f"Return: {return_rate}%")
            
        else:
            st.subheader("Live Rosin (Ice Water -> Press)")
            st.caption("WPFF contains water weight (approx 75-80%). Yields look lower vs wet weight.")
            
            wash_yield = st.slider("Wash Yield (to Bubble Hash)", 1.0, 8.0, 4.0, help="3-5% is average for whole plant")
            press_yield = st.slider("Press Yield (Hash to Rosin)", 40, 90, 75)
            
            hash_g = input_g * (wash_yield / 100)
            rosin_g = hash_g * (press_yield / 100)
            
            m1, m2 = st.columns(2)
            m1.metric("Bubble Hash", f"{hash_g:.1f} g")
            m2.metric("Live Rosin", f"{rosin_g:.1f} g")

# ==========================================
# TAB 4: REVERSE ENGINEER
# ==========================================
with tab_reverse:
    st.header("Setup Recommender")
    st.write("Tell me what you want, I'll tell you what you need.")
    
    target_unit = st.radio("Target Unit", ["Ounces", "Pounds", "Kilograms"])
    target_val = st.number_input(f"Desired Yield ({target_unit})", value=1.0)
    
    # Convert to grams
    if target_unit == "Ounces": target_g = target_val * 28.35
    elif target_unit == "Pounds": target_g = target_val * 453.59
    else: target_g = target_val * 1000
    
    st.divider()
    
    # Logic Reversal
    # Assume average efficiency (1.5 GPW) and average density (40g/sqft)
    req_watts = target_g / 1.5
    req_sqft = target_g / 40.0
    
    col_rec1, col_rec2 = st.columns(2)
    
    with col_rec1:
        st.subheader("Hardware Required")
        st.metric("Minimum Light", f"{req_watts:.0f} Watts")
        st.metric("Minimum Space", f"{req_sqft:.1f} Sq. Ft.")
        
    with col_rec2:
        st.subheader("Configuration Suggestions")
        
        # Tent Logic
        if req_sqft < 5: 
            tent_rec = "2x2.5 or 2x4 Tent"
            light_rec = "200W-300W LED"
        elif req_sqft < 10: 
            tent_rec = "3x3 or 2x4 Tent"
            light_rec = "300W-480W LED"
        elif req_sqft < 17: 
            tent_rec = "4x4 Tent"
            light_rec = "600W-720W Bar LED"
        elif req_sqft < 26: 
            tent_rec = "5x5 Tent"
            light_rec = "800W-1000W Bar LED + CO2"
        else: 
            tent_rec = "Multiple Tents or Dedicated Room"
            light_rec = "Multi-light Setup"
            
        st.success(f"⛺ **Tent:** {tent_rec}")
        st.warning(f"💡 **Light:** {light_rec}")
        
        est_pots = math.ceil(target_g / 112) # ~4oz per plant avg assumption for counting
        st.info(f"🌱 **Plant Count:** {est_pots} plants in 5gal pots (Estimated)")