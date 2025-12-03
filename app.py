"""
BidSync AI v2.1 - Fire Protection Blueprint Analyzer
Built for ASAP Security
v8 - Trade-based UX: Select your trade, see only what matters
"""

import streamlit as st
import anthropic
import base64
import json
from PIL import Image
import io
import pandas as pd
from typing import Dict, List
import re
from pdf2image import convert_from_bytes
import PyPDF2

# Page config
st.set_page_config(
    page_title="BidSync AI - Blueprint Analyzer",
    page_icon="⚡",
    layout="wide"
)

# ============================================
# TRADE CONFIGURATIONS
# ============================================
TRADE_CONFIG = {
    "fire_alarm": {
        "name": "Fire Alarm",
        "icon": "🚨",
        "description": "Smoke detectors, pull stations, horn/strobes, panels",
        "devices": {
            "smoke_detectors": ("Smoke Detectors", 250),
            "heat_detectors": ("Heat Detectors", 200),
            "pull_stations": ("Pull Stations", 150),
            "horn_strobes": ("Horn/Strobes", 175),
            "strobes_only": ("Strobes Only", 125),
            "horns_speakers": ("Horns/Speakers", 150),
            "duct_detectors": ("Duct Detectors", 350),
            "beam_detectors": ("Beam Detectors", 800),
            "facp": ("Fire Alarm Control Panel", 3500),
            "annunciator": ("Annunciator Panel", 1200),
            "monitor_modules": ("Monitor Modules", 125),
            "relay_modules": ("Relay Modules", 125),
            "door_holders": ("Magnetic Door Holders", 85),
        },
        "prompt_focus": """Focus ONLY on FIRE ALARM devices:
- Smoke detectors (addressable, photoelectric, ionization)
- Heat detectors (fixed temp, rate-of-rise)
- Manual pull stations
- Horn/strobes, strobes, horns/speakers (notification devices)
- Duct detectors
- Beam detectors
- Fire Alarm Control Panel (FACP)
- Annunciator panels
- Monitor modules, relay modules
- Magnetic door holders

IGNORE: Sprinkler heads, electrical panels, security devices, 120VAC smoke detectors"""
    },
    
    "sprinkler": {
        "name": "Sprinkler",
        "icon": "💧",
        "description": "Sprinkler heads, risers, valves, FDC",
        "devices": {
            "sprinkler_heads": ("Sprinkler Heads", 85),
            "risers": ("Risers", 1500),
            "piv": ("PIV (Post Indicator Valve)", 2500),
            "osny": ("OS&Y Valve", 800),
            "fdc": ("Fire Dept Connection", 650),
            "flow_switch": ("Flow Switch", 275),
            "tamper_switch": ("Tamper Switch", 150),
            "inspectors_test": ("Inspector's Test", 125),
            "fire_pump": ("Fire Pump", 15000),
        },
        "prompt_focus": """Focus ONLY on SPRINKLER/SUPPRESSION devices:
- Sprinkler heads (pendant, upright, sidewall, concealed) - count ALL circles on sprinkler piping
- Risers
- PIV (Post Indicator Valve)
- OS&Y valves
- FDC (Fire Department Connection)
- Flow switches
- Tamper switches
- Inspector's test connections
- Fire pumps

IGNORE: Fire alarm devices, electrical, security"""
    },
    
    "electrical": {
        "name": "Electrical",
        "icon": "⚡",
        "description": "120VAC devices, panels, receptacles, lighting",
        "devices": {
            "smoke_detectors_120v": ("Smoke Detectors (120VAC)", 45),
            "co_detectors_120v": ("CO Detectors (120VAC)", 55),
            "combo_smoke_co": ("Combo Smoke/CO (120VAC)", 65),
            "receptacles": ("Receptacles", 25),
            "switches": ("Switches", 20),
            "junction_boxes": ("Junction Boxes", 15),
            "panels": ("Electrical Panels", 1500),
            "disconnects": ("Disconnects", 350),
            "lighting_fixtures": ("Lighting Fixtures", 150),
            "emergency_lights": ("Emergency Lights", 200),
            "exit_signs": ("Exit Signs", 125),
        },
        "prompt_focus": """Focus ONLY on ELECTRICAL devices:
- 120VAC smoke detectors (residential/line voltage type)
- 120VAC CO detectors
- Combo smoke/CO detectors
- Receptacles
- Switches
- Junction boxes
- Electrical panels
- Disconnects
- Lighting fixtures
- Emergency lights
- Exit signs

IGNORE: Low voltage fire alarm (24VDC), sprinkler, security"""
    },
    
    "security": {
        "name": "Security/Access",
        "icon": "🔐",
        "description": "Cameras, card readers, door contacts, access control",
        "devices": {
            "cameras": ("Security Cameras", 450),
            "card_readers": ("Card Readers", 350),
            "door_contacts": ("Door Contacts", 45),
            "motion_sensors": ("Motion Sensors", 125),
            "glass_break": ("Glass Break Sensors", 85),
            "access_panel": ("Access Control Panel", 2500),
            "electric_strike": ("Electric Strikes", 275),
            "mag_locks": ("Magnetic Locks", 325),
            "rex": ("REX (Request to Exit)", 150),
            "keypad": ("Keypads", 225),
            "intercom": ("Intercom Stations", 400),
        },
        "prompt_focus": """Focus ONLY on SECURITY/ACCESS CONTROL devices:
- Security cameras (IP, analog, PTZ)
- Card readers
- Door contacts
- Motion sensors
- Glass break sensors
- Access control panels
- Electric strikes
- Magnetic locks (mag locks)
- REX (Request to Exit) sensors
- Keypads
- Intercom stations

IGNORE: Fire alarm, sprinkler, general electrical"""
    },
    
    "low_voltage": {
        "name": "Low Voltage",
        "icon": "🔌",
        "description": "All low voltage: fire alarm + security combined",
        "devices": {
            # Fire alarm
            "smoke_detectors": ("Smoke Detectors", 250),
            "heat_detectors": ("Heat Detectors", 200),
            "pull_stations": ("Pull Stations", 150),
            "horn_strobes": ("Horn/Strobes", 175),
            "strobes_only": ("Strobes Only", 125),
            "facp": ("Fire Alarm Control Panel", 3500),
            "annunciator": ("Annunciator Panel", 1200),
            "monitor_modules": ("Monitor Modules", 125),
            "relay_modules": ("Relay Modules", 125),
            # Security
            "cameras": ("Security Cameras", 450),
            "card_readers": ("Card Readers", 350),
            "door_contacts": ("Door Contacts", 45),
            "motion_sensors": ("Motion Sensors", 125),
            "access_panel": ("Access Control Panel", 2500),
        },
        "prompt_focus": """Focus on ALL LOW VOLTAGE devices (both fire alarm and security):

FIRE ALARM:
- Smoke detectors, heat detectors
- Pull stations
- Horn/strobes, notification devices
- FACP, annunciator panels
- Modules (monitor, relay)

SECURITY:
- Cameras
- Card readers, door contacts
- Motion sensors
- Access control panels

IGNORE: Sprinkler heads, 120VAC electrical, lighting"""
    }
}

# ============================================
# CUSTOM CSS - Dark theme
# ============================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #1a2744 50%, #0d1f3c 100%);
    }
    
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #e0e0e0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Trade selector cards */
    .trade-card {
        background: rgba(22, 33, 62, 0.8);
        border: 2px solid rgba(0, 212, 255, 0.3);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        margin: 0.5rem;
    }
    
    .trade-card:hover {
        border-color: #00d4ff;
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
    }
    
    .trade-card.selected {
        border-color: #00d4ff;
        background: rgba(0, 212, 255, 0.15);
    }
    
    .trade-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .trade-name {
        font-size: 1.3rem;
        font-weight: 600;
        color: #00d4ff !important;
        margin-bottom: 0.3rem;
    }
    
    .trade-desc {
        font-size: 0.85rem;
        color: #888 !important;
    }
    
    /* Input fields */
    .stTextInput input,
    input[type="text"],
    input[type="password"] {
        background: rgba(15, 52, 96, 0.95) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
        border-radius: 8px !important;
    }
    
    .stNumberInput input {
        background: rgba(15, 52, 96, 0.95) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
    }
    
    /* Expander */
    [data-testid="stExpander"] {
        background: rgba(22, 33, 62, 0.95) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
    }
    
    [data-testid="stExpander"] summary,
    .streamlit-expanderHeader {
        background: rgba(22, 33, 62, 0.95) !important;
        color: #00d4ff !important;
    }
    
    [data-testid="stExpander"] input {
        background: rgba(15, 52, 96, 0.95) !important;
        color: #00d4ff !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(15, 52, 96, 0.6) !important;
        border: 2px dashed rgba(0, 212, 255, 0.4) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    
    [data-testid="stFileUploader"] * {
        color: #00d4ff !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 2rem !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4) !important;
    }
    
    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(15, 52, 96, 0.95) !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
    }
    
    /* Total bid box */
    .total-bid-box {
        background: linear-gradient(135deg, rgba(22, 33, 62, 0.9) 0%, rgba(44, 62, 114, 0.9) 100%) !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        text-align: center !important;
        margin: 1rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2) !important;
    }
    
    .total-bid-box h2 {
        color: #00d4ff !important;
        font-size: 3rem !important;
        margin: 0 !important;
        text-shadow: 0 0 20px rgba(0, 212, 255, 0.5) !important;
    }
    
    /* Markdown tables */
    .stMarkdown table {
        background: rgba(15, 52, 96, 0.6) !important;
        border-radius: 8px !important;
    }
    
    .stMarkdown th {
        background: rgba(10, 35, 70, 0.95) !important;
        color: #00d4ff !important;
        padding: 12px !important;
    }
    
    .stMarkdown td {
        background: rgba(15, 52, 96, 0.8) !important;
        color: #00d4ff !important;
        padding: 10px 12px !important;
    }
    
    /* Radio buttons for trade selection */
    .stRadio > div {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 1rem !important;
    }
    
    .stRadio label {
        background: rgba(22, 33, 62, 0.8) !important;
        border: 2px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 1rem 1.5rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }
    
    .stRadio label:hover {
        border-color: #00d4ff !important;
    }
    
    .stRadio label[data-checked="true"] {
        border-color: #00d4ff !important;
        background: rgba(0, 212, 255, 0.15) !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #0a1628 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# PASSWORD PROTECTION
# ============================================
def check_password():
    """Returns True if user has correct password."""
    def password_entered():
        if st.session_state["password"] == "FireProtect2025!":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

# ============================================
# ANALYSIS FUNCTION
# ============================================
def analyze_blueprint_page(client, image_data: bytes, trade_config: dict, page_num: int = 1) -> Dict:
    """Analyze a blueprint page for specific trade."""
    
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    # Build device list for JSON response
    device_keys = list(trade_config["devices"].keys())
    device_json = {key: 0 for key in device_keys}
    
    prompt = f"""Analyze this construction blueprint and count devices.

{trade_config["prompt_focus"]}

Return JSON format:
{{
    "page_type": "floor plan/riser/schedule/detail/legend/other",
    "description": "Brief description of what this page shows",
    "devices": {json.dumps(device_json, indent=2)},
    "notes": "Any relevant notes"
}}

Be thorough - count EVERY device symbol you can identify. Check legends and schedules for quantities."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        
        response_text = response.content[0].text
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        else:
            return {"error": "Could not parse response", "raw": response_text}
            
    except Exception as e:
        return {"error": str(e)}

def convert_pdf_page_to_image(pdf_bytes: bytes, page_num: int) -> bytes:
    """Convert a specific PDF page to image."""
    try:
        images = convert_from_bytes(
            pdf_bytes,
            first_page=page_num,
            last_page=page_num,
            dpi=150
        )
        
        if images:
            img = images[0]
            max_dim = 2000
            if max(img.size) > max_dim:
                ratio = max_dim / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)
            
            img_byte_arr = io.BytesIO()
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            img.save(img_byte_arr, format='JPEG', quality=75, optimize=True)
            return img_byte_arr.getvalue()
    except Exception as e:
        st.error(f"Error converting page {page_num}: {str(e)}")
    return None

def get_pdf_page_count(pdf_bytes: bytes) -> int:
    """Get total number of pages in PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        return len(pdf_reader.pages)
    except:
        return 0

# ============================================
# MAIN APPLICATION
# ============================================
def main():
    # Header
    st.markdown("""
    <h1 style='text-align: center; background: linear-gradient(135deg, #00d4ff 0%, #a855f7 100%); 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3rem;'>
    ⚡ BidSync AI</h1>
    """, unsafe_allow_html=True)
    
    # ========================================
    # STEP 1: TRADE SELECTION
    # ========================================
    if 'selected_trade' not in st.session_state:
        st.session_state['selected_trade'] = None
    
    if st.session_state['selected_trade'] is None:
        st.markdown("""
        <p style='text-align: center; color: #888; font-size: 1.2rem; margin-bottom: 2rem;'>
        What do you install?
        </p>
        """, unsafe_allow_html=True)
        
        # Trade selection cards
        cols = st.columns(5)
        
        for idx, (trade_key, trade_info) in enumerate(TRADE_CONFIG.items()):
            with cols[idx]:
                if st.button(
                    f"{trade_info['icon']}\n\n**{trade_info['name']}**",
                    key=f"trade_{trade_key}",
                    use_container_width=True,
                    help=trade_info['description']
                ):
                    st.session_state['selected_trade'] = trade_key
                    st.rerun()
                
                st.caption(trade_info['description'])
        
        # Settings at bottom
        st.markdown("---")
        with st.expander("⚙️ Settings"):
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                value=st.session_state.get('api_key', ''),
                help="Enter your Anthropic API key"
            )
            if api_key:
                st.session_state['api_key'] = api_key
    
    else:
        # ========================================
        # STEP 2: ANALYSIS (Trade Selected)
        # ========================================
        trade_key = st.session_state['selected_trade']
        trade_config = TRADE_CONFIG[trade_key]
        
        # Show selected trade with change option
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
            <p style='color: #888; margin: 0;'>Analyzing for:</p>
            <h3 style='margin: 0;'>{trade_config['icon']} {trade_config['name']}</h3>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("Change", use_container_width=True):
                st.session_state['selected_trade'] = None
                st.session_state.pop('analysis_results', None)
                st.session_state.pop('editable_counts', None)
                st.session_state.pop('editable_prices', None)
                st.rerun()
        
        # Settings
        with st.expander("⚙️ Settings"):
            api_key = st.text_input(
                "Anthropic API Key",
                type="password",
                value=st.session_state.get('api_key', ''),
            )
            if api_key:
                st.session_state['api_key'] = api_key
        
        st.markdown("---")
        
        # File upload
        st.markdown("### 📁 Upload Blueprint")
        uploaded_file = st.file_uploader(
            "Drag and drop file here",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="PDF, PNG, JPG, JPEG"
        )
        
        if uploaded_file and st.session_state.get('api_key'):
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            
            # Handle PDF
            if uploaded_file.type == "application/pdf":
                total_pages = get_pdf_page_count(file_bytes)
                st.success(f"✓ {uploaded_file.name} ({len(file_bytes)/1_000_000:.1f} MB)")
                st.info(f"📄 {total_pages} pages detected")
                
                col1, col2 = st.columns(2)
                with col1:
                    start_page = st.number_input("Start page", min_value=1, max_value=total_pages, value=1)
                with col2:
                    end_page = st.number_input("End page", min_value=1, max_value=total_pages, value=total_pages)
                
                if st.button(f"🔍 Analyze {trade_config['name']} Devices", type="primary", use_container_width=True):
                    if start_page > end_page:
                        st.error("Start page must be ≤ end page")
                        return
                    
                    client = anthropic.Anthropic(api_key=st.session_state['api_key'])
                    
                    # Initialize totals for this trade's devices
                    total_devices = {key: 0 for key in trade_config["devices"].keys()}
                    page_results = []
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    pages_to_analyze = list(range(start_page, end_page + 1))
                    
                    for idx, page_num in enumerate(pages_to_analyze):
                        status_text.text(f"Analyzing page {page_num}...")
                        progress_bar.progress((idx + 1) / len(pages_to_analyze))
                        
                        image_data = convert_pdf_page_to_image(file_bytes, page_num)
                        
                        if image_data:
                            result = analyze_blueprint_page(client, image_data, trade_config, page_num)
                            
                            if "error" not in result:
                                page_results.append({
                                    "page": page_num,
                                    "type": result.get("page_type", "unknown"),
                                    "description": result.get("description", ""),
                                    "devices": result.get("devices", {}),
                                    "notes": result.get("notes", "")
                                })
                                
                                for device_type, count in result.get("devices", {}).items():
                                    if device_type in total_devices:
                                        total_devices[device_type] += count
                    
                    status_text.text("✅ Analysis complete!")
                    progress_bar.progress(1.0)
                    
                    st.session_state['analysis_results'] = {
                        "total_devices": total_devices,
                        "page_results": page_results,
                        "filename": uploaded_file.name,
                        "trade": trade_key
                    }
                    # Clear previous edits
                    st.session_state.pop('editable_counts', None)
                    st.session_state.pop('editable_prices', None)
            
            else:
                # Single image
                st.image(file_bytes, caption="Blueprint Preview", use_column_width=True)
                
                if st.button(f"🔍 Analyze {trade_config['name']} Devices", type="primary", use_container_width=True):
                    client = anthropic.Anthropic(api_key=st.session_state['api_key'])
                    
                    with st.spinner("Analyzing..."):
                        result = analyze_blueprint_page(client, file_bytes, trade_config)
                        
                        if "error" not in result:
                            st.session_state['analysis_results'] = {
                                "total_devices": result.get("devices", {}),
                                "page_results": [{"page": 1, **result}],
                                "filename": uploaded_file.name,
                                "trade": trade_key
                            }
                            st.session_state.pop('editable_counts', None)
                            st.session_state.pop('editable_prices', None)
                        else:
                            st.error(f"Error: {result['error']}")
        
        elif uploaded_file and not st.session_state.get('api_key'):
            st.warning("⚠️ Enter your API key in Settings above")
        
        # ========================================
        # RESULTS DISPLAY
        # ========================================
        if 'analysis_results' in st.session_state:
            results = st.session_state['analysis_results']
            
            # Make sure we're showing results for current trade
            if results.get('trade') == trade_key:
                total_devices = results['total_devices']
                page_results = results['page_results']
                
                st.markdown("---")
                
                # Device Count - Editable
                st.markdown(f"### {trade_config['icon']} Device Count")
                st.caption("✏️ Edit counts and prices as needed")
                
                # Initialize editable values
                if 'editable_counts' not in st.session_state:
                    st.session_state['editable_counts'] = {}
                if 'editable_prices' not in st.session_state:
                    st.session_state['editable_prices'] = {}
                
                edited_counts = {}
                edited_prices = {}
                
                # Header
                col_d, col_c, col_p, col_t = st.columns([3, 1.5, 1.5, 1.5])
                with col_d:
                    st.markdown("**Device**")
                with col_c:
                    st.markdown("**Count**")
                with col_p:
                    st.markdown("**Unit $**")
                with col_t:
                    st.markdown("**Total**")
                
                st.markdown("---")
                
                # Device rows
                for key, (display_name, default_price) in trade_config["devices"].items():
                    ai_count = total_devices.get(key, 0)
                    current_count = st.session_state['editable_counts'].get(key, ai_count)
                    current_price = st.session_state['editable_prices'].get(key, default_price)
                    
                    col_d, col_c, col_p, col_t = st.columns([3, 1.5, 1.5, 1.5])
                    
                    with col_d:
                        st.markdown(display_name)
                    
                    with col_c:
                        edited_counts[key] = st.number_input(
                            f"c_{key}", min_value=0, value=current_count,
                            key=f"c_{key}", label_visibility="collapsed"
                        )
                    
                    with col_p:
                        edited_prices[key] = st.number_input(
                            f"p_{key}", min_value=0, value=current_price,
                            key=f"p_{key}", label_visibility="collapsed"
                        )
                    
                    with col_t:
                        line_total = edited_counts[key] * edited_prices[key]
                        st.markdown(f"**${line_total:,.2f}**")
                
                st.session_state['editable_counts'] = edited_counts
                st.session_state['editable_prices'] = edited_prices
                
                # Bid Calculation
                st.markdown("---")
                st.markdown("### 💰 Bid Calculation")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    overhead_pct = st.number_input("Overhead %", min_value=0, max_value=50, value=10)
                with col2:
                    profit_pct = st.number_input("Profit %", min_value=0, max_value=50, value=15)
                with col3:
                    misc_cost = st.number_input("Misc $", min_value=0, value=0)
                
                # Calculate
                material_cost = sum(
                    edited_counts.get(key, 0) * edited_prices.get(key, dp)
                    for key, (_, dp) in trade_config["devices"].items()
                )
                
                overhead_amount = material_cost * (overhead_pct / 100)
                profit_amount = (material_cost + overhead_amount) * (profit_pct / 100)
                total_bid = material_cost + overhead_amount + profit_amount + misc_cost
                
                # Summary table
                st.markdown(f"""
| **Description** | **Amount** |
|-----------------|------------|
| Material Cost | ${material_cost:,.2f} |
| Overhead ({overhead_pct}%) | ${overhead_amount:,.2f} |
| Profit ({profit_pct}%) | ${profit_amount:,.2f} |
| Miscellaneous | ${misc_cost:,.2f} |
""")
                
                st.markdown(f"""
                <div class="total-bid-box">
                    <p style="color: #888; margin-bottom: 0.5rem; font-size: 0.9rem;">TOTAL BID</p>
                    <h2>${total_bid:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Export
                st.markdown("### 📤 Export")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    export_data = []
                    for key, (display_name, default_price) in trade_config["devices"].items():
                        count = edited_counts.get(key, 0)
                        price = edited_prices.get(key, default_price)
                        if count > 0:
                            export_data.append({
                                "Device": display_name,
                                "Count": count,
                                "Unit Price": price,
                                "Total": count * price
                            })
                    export_df = pd.DataFrame(export_data)
                    csv = export_df.to_csv(index=False)
                    st.download_button("📊 Download CSV", csv,
                        f"bidsync_{trade_config['name'].lower()}_{results['filename'].split('.')[0]}.csv",
                        "text/csv", use_container_width=True)
                
                with col2:
                    summary = f"""BidSync AI - {trade_config['name']} Analysis
File: {results['filename']}
Pages: {len(page_results)}

DEVICES:
"""
                    for key, (display_name, dp) in trade_config["devices"].items():
                        count = edited_counts.get(key, 0)
                        price = edited_prices.get(key, dp)
                        if count > 0:
                            summary += f"- {display_name}: {count} @ ${price} = ${count * price:,.2f}\n"
                    
                    summary += f"""
BID:
- Material: ${material_cost:,.2f}
- Overhead ({overhead_pct}%): ${overhead_amount:,.2f}
- Profit ({profit_pct}%): ${profit_amount:,.2f}
- Misc: ${misc_cost:,.2f}
- TOTAL: ${total_bid:,.2f}
"""
                    st.download_button("📝 Download Summary", summary,
                        f"bidsync_{trade_config['name'].lower()}_{results['filename'].split('.')[0]}.txt",
                        "text/plain", use_container_width=True)
                
                # Page breakdown
                with st.expander("📄 Page-by-Page Breakdown"):
                    for pr in page_results:
                        st.markdown(f"**Page {pr['page']}** *{pr.get('type', '')}*")
                        st.write(pr.get('description', ''))
                        
                        devices_found = {k: v for k, v in pr.get('devices', {}).items() if v > 0}
                        if devices_found:
                            for dk, dv in devices_found.items():
                                display = trade_config["devices"].get(dk, (dk.replace('_', ' ').title(), 0))[0]
                                st.markdown(f"- {display}: **{dv}**")
                        else:
                            st.caption("No devices on this page")
                        st.markdown("---")
    
    # Footer
    st.markdown("---")
    st.caption("⚡ BidSync AI v2.1 | Built for ASAP Security")

# ============================================
# RUN
# ============================================
if __name__ == "__main__":
    if check_password():
        main()
