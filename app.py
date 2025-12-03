"""
BidSync AI v2.0 - Fire Protection Blueprint Analyzer
Built for ASAP Security
Multi-page PDF support with device detection
v6 - Complete dark theme fix for Settings expander and data table
"""

import streamlit as st
import anthropic
import base64
import json
from PIL import Image
import io
import pandas as pd
from typing import Dict, List, Tuple
import re
from pdf2image import convert_from_bytes
import PyPDF2

# Page config
st.set_page_config(
    page_title="BidSync AI - Fire Protection Blueprint Analyzer",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS - Dark theme with cyan accents - v6 COMPLETE FIX
st.markdown("""
<style>
    /* ============================================
       GLOBAL DARK THEME
       ============================================ */
    .stApp {
        background: linear-gradient(135deg, #0a1628 0%, #1a2744 50%, #0d1f3c 100%);
    }
    
    /* Main text styling */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div {
        color: #e0e0e0 !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* ============================================
       INPUT FIELDS - DARK WITH CYAN TEXT
       ============================================ */
    /* All text inputs including password and API key */
    .stTextInput input,
    .stTextInput input[type="text"],
    .stTextInput input[type="password"],
    input[type="text"],
    input[type="password"] {
        background: rgba(15, 52, 96, 0.95) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
        border-radius: 8px !important;
        caret-color: #00d4ff !important;
    }
    
    /* Number inputs */
    .stNumberInput input,
    input[type="number"] {
        background: rgba(15, 52, 96, 0.95) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
        border-radius: 8px !important;
    }
    
    /* Input labels */
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label {
        color: #b0b0b0 !important;
    }
    
    /* Placeholder text */
    .stTextInput input::placeholder,
    .stNumberInput input::placeholder {
        color: rgba(0, 212, 255, 0.5) !important;
    }
    
    /* ============================================
       EXPANDER / SETTINGS - COMPLETE DARK THEME
       ============================================ */
    /* Expander container */
    [data-testid="stExpander"] {
        background: rgba(22, 33, 62, 0.95) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
    }
    
    /* Expander header bar */
    [data-testid="stExpander"] > div:first-child {
        background: rgba(22, 33, 62, 0.95) !important;
        border-radius: 12px !important;
    }
    
    /* Expander header text and icon */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] summary p,
    .streamlit-expanderHeader,
    .streamlit-expanderHeader span,
    .streamlit-expanderHeader p {
        background: rgba(22, 33, 62, 0.95) !important;
        color: #00d4ff !important;
    }
    
    /* Expander content area */
    [data-testid="stExpander"] > div:last-child,
    [data-testid="stExpander"] [data-testid="stExpanderDetails"],
    .streamlit-expanderContent {
        background: rgba(22, 33, 62, 0.95) !important;
        border: none !important;
    }
    
    /* Inputs INSIDE expanders */
    [data-testid="stExpander"] input,
    [data-testid="stExpander"] input[type="text"],
    [data-testid="stExpander"] input[type="password"],
    [data-testid="stExpander"] .stTextInput input {
        background: rgba(15, 52, 96, 0.95) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
        caret-color: #00d4ff !important;
    }
    
    /* Labels inside expanders */
    [data-testid="stExpander"] label,
    [data-testid="stExpander"] .stTextInput label {
        color: #b0b0b0 !important;
    }
    
    /* Help text inside expanders */
    [data-testid="stExpander"] .stTextInput div[data-testid="stMarkdownContainer"] p {
        color: #888888 !important;
    }
    
    /* ============================================
       DATA TABLE - COMPLETE DARK THEME
       ============================================ */
    /* Main dataframe container */
    [data-testid="stDataFrame"],
    .stDataFrame,
    [data-testid="stDataFrame"] > div,
    .stDataFrame > div {
        background: rgba(15, 52, 96, 0.6) !important;
        border-radius: 8px !important;
    }
    
    /* DataFrame iframe and content */
    [data-testid="stDataFrame"] iframe,
    .stDataFrame iframe {
        background: rgba(15, 52, 96, 0.95) !important;
    }
    
    /* Table element itself */
    [data-testid="stDataFrame"] table,
    .stDataFrame table,
    .dataframe,
    table.dataframe {
        background: rgba(15, 52, 96, 0.95) !important;
        color: #00d4ff !important;
    }
    
    /* Table headers */
    [data-testid="stDataFrame"] th,
    .stDataFrame th,
    .dataframe th,
    table th {
        background: rgba(10, 35, 70, 0.95) !important;
        color: #00d4ff !important;
        border-bottom: 2px solid rgba(0, 212, 255, 0.4) !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    /* Table cells */
    [data-testid="stDataFrame"] td,
    .stDataFrame td,
    .dataframe td,
    table td {
        background: rgba(15, 52, 96, 0.8) !important;
        color: #00d4ff !important;
        border-bottom: 1px solid rgba(0, 212, 255, 0.2) !important;
    }
    
    /* Table rows hover */
    [data-testid="stDataFrame"] tr:hover td,
    .stDataFrame tr:hover td,
    table tr:hover td {
        background: rgba(0, 212, 255, 0.15) !important;
    }
    
    /* Glide Data Grid (Streamlit's new table component) */
    [data-testid="glideDataEditor"],
    .glideDataEditor,
    [class*="glide"] {
        background: rgba(15, 52, 96, 0.95) !important;
    }
    
    /* Canvas-based table rendering */
    [data-testid="stDataFrame"] canvas {
        background: rgba(15, 52, 96, 0.95) !important;
    }
    
    /* Override any white backgrounds in data display */
    [data-testid="stDataFrame"] *,
    .stDataFrame * {
        background-color: transparent !important;
    }
    
    [data-testid="stDataFrame"] > div > div,
    .stDataFrame > div > div {
        background: rgba(15, 52, 96, 0.95) !important;
    }
    
    /* ============================================
       FILE UPLOADER - DARK THEME
       ============================================ */
    [data-testid="stFileUploader"] {
        background: rgba(15, 52, 96, 0.6) !important;
        border: 2px dashed rgba(0, 212, 255, 0.4) !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    
    [data-testid="stFileUploader"] * {
        color: #00d4ff !important;
    }
    
    [data-testid="stFileUploader"] section {
        background: transparent !important;
    }
    
    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #00d4ff 0%, #00a8cc 100%) !important;
        color: #0a1628 !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    /* ============================================
       BUTTONS
       ============================================ */
    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 20px rgba(0, 212, 255, 0.4) !important;
    }
    
    /* Download buttons */
    .stDownloadButton > button {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #0a1628 !important;
        border: none !important;
    }
    
    /* ============================================
       METRICS AND INFO BOXES
       ============================================ */
    [data-testid="stMetric"] {
        background: rgba(22, 33, 62, 0.6) !important;
        padding: 1rem !important;
        border-radius: 8px !important;
        border-left: 3px solid #00d4ff !important;
    }
    
    [data-testid="stMetric"] label {
        color: #b0b0b0 !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #00d4ff !important;
    }
    
    /* Info/Success/Warning/Error boxes */
    .stAlert, [data-testid="stAlert"] {
        background: rgba(22, 33, 62, 0.8) !important;
        border-radius: 8px !important;
    }
    
    /* ============================================
       SIDEBAR
       ============================================ */
    [data-testid="stSidebar"] {
        background: rgba(10, 22, 40, 0.95) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    
    /* ============================================
       MARKDOWN TABLES
       ============================================ */
    .stMarkdown table {
        background: rgba(15, 52, 96, 0.6) !important;
        border-collapse: collapse !important;
        width: 100% !important;
        border-radius: 8px !important;
        overflow: hidden !important;
    }
    
    .stMarkdown th {
        background: rgba(10, 35, 70, 0.95) !important;
        color: #00d4ff !important;
        padding: 12px !important;
        text-align: left !important;
        border-bottom: 2px solid rgba(0, 212, 255, 0.4) !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
    }
    
    .stMarkdown td {
        background: rgba(15, 52, 96, 0.8) !important;
        color: #00d4ff !important;
        padding: 10px 12px !important;
        border-bottom: 1px solid rgba(0, 212, 255, 0.2) !important;
    }
    
    .stMarkdown tr:hover td {
        background: rgba(0, 212, 255, 0.15) !important;
    }
    
    /* ============================================
       TOTAL BID BOX
       ============================================ */
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
    
    /* ============================================
       SELECTBOX
       ============================================ */
    .stSelectbox > div > div {
        background: rgba(15, 52, 96, 0.95) !important;
        border: 1px solid rgba(0, 212, 255, 0.4) !important;
        color: #00d4ff !important;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background: rgba(15, 52, 96, 0.95) !important;
    }
    
    .stSelectbox [data-baseweb="select"] * {
        color: #00d4ff !important;
    }
    
    /* ============================================
       DIVIDERS AND CAPTIONS
       ============================================ */
    hr {
        border-color: rgba(0, 212, 255, 0.2) !important;
    }
    
    .stCaption, caption {
        color: #888888 !important;
    }
    
    /* ============================================
       PAGE-BY-PAGE BREAKDOWN EXPANDER
       ============================================ */
    details {
        background: rgba(22, 33, 62, 0.95) !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 8px !important;
    }
    
    details summary {
        background: rgba(22, 33, 62, 0.95) !important;
        color: #00d4ff !important;
    }
    
    details[open] > summary {
        border-bottom: 1px solid rgba(0, 212, 255, 0.3) !important;
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
# DEVICE PRICING
# ============================================
DEFAULT_PRICES = {
    "smoke_detector": 250,
    "pull_station": 150,
    "horn_strobe": 175,
    "strobe_only": 125,
    "horn_speaker": 150,
    "sprinkler_head": 85,
    "facp": 3500,
    "annunciator": 1200,
    "monitor_module": 125,
    "relay_module": 125
}

# ============================================
# BLUEPRINT ANALYSIS FUNCTION
# ============================================
def analyze_blueprint_page(client, image_data: bytes, page_num: int = 1) -> Dict:
    """Analyze a single blueprint page using Claude Vision."""
    
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    prompt = """Analyze this fire protection blueprint page and identify ALL devices.

COUNT THESE FIRE ALARM DEVICES:
- Smoke Detectors (circles with "SD" or smoke symbols)
- Pull Stations (manual pull stations, usually at exits)
- Horn/Strobes (notification devices, "H/S" symbols)
- Strobes Only (visual only notification)
- Horns/Speakers (audio notification devices)
- Fire Alarm Control Panel (FACP)
- Annunciator Panels
- Monitor Modules
- Relay Modules

COUNT THESE SPRINKLER DEVICES:
- Sprinkler Heads (circles on piping, pendant/upright symbols)

ALSO NOTE:
- Page/drawing type (floor plan, riser diagram, details, schedule, etc.)
- Any device schedules or legends with quantities

Return JSON format:
{
    "page_type": "floor plan/riser/schedule/detail/legend/other",
    "description": "Brief description of what this page shows",
    "devices": {
        "smoke_detectors": 0,
        "pull_stations": 0,
        "horn_strobes": 0,
        "strobes_only": 0,
        "horns_speakers": 0,
        "sprinkler_heads": 0,
        "facp": 0,
        "annunciator": 0,
        "monitor_modules": 0,
        "relay_modules": 0
    },
    "notes": "Any relevant notes about devices or quantities found"
}

Be thorough - count EVERY device symbol visible. If you see a legend/schedule with device quantities, include those counts."""

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
        
        # Extract JSON from response
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
            
            # Resize if too large
            max_dim = 2000
            if max(img.size) > max_dim:
                ratio = max_dim / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.LANCZOS)
            
            # Convert to JPEG bytes
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
    <p style='text-align: center; color: #888; font-size: 1.1rem;'>Fire Protection Blueprint Analyzer</p>
    """, unsafe_allow_html=True)
    
    # Settings expander for API key
    with st.expander("⚙️ Settings"):
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=st.session_state.get('api_key', ''),
            help="Enter your Anthropic API key"
        )
        if api_key:
            st.session_state['api_key'] = api_key
    
    # File upload section
    st.markdown("### 📁 Upload Blueprint")
    uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Limit 200MB per file • PDF, PNG, JPG, JPEG"
    )
    
    if uploaded_file and st.session_state.get('api_key'):
        file_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        
        # Handle PDF
        if uploaded_file.type == "application/pdf":
            total_pages = get_pdf_page_count(file_bytes)
            st.success(f"✓ {uploaded_file.name} ({len(file_bytes)/1_000_000:.1f} MB)")
            st.info(f"📄 {total_pages} pages detected")
            
            # Page range selection
            col1, col2 = st.columns(2)
            with col1:
                start_page = st.number_input("Start page", min_value=1, max_value=total_pages, value=1)
            with col2:
                end_page = st.number_input("End page", min_value=1, max_value=total_pages, value=total_pages)
            
            # Analyze button
            if st.button("🔍 Analyze Blueprint", type="primary", use_container_width=True):
                if start_page > end_page:
                    st.error("Start page must be less than or equal to end page")
                    return
                
                client = anthropic.Anthropic(api_key=st.session_state['api_key'])
                
                # Initialize totals
                total_devices = {
                    "smoke_detectors": 0,
                    "pull_stations": 0,
                    "horn_strobes": 0,
                    "strobes_only": 0,
                    "horns_speakers": 0,
                    "sprinkler_heads": 0,
                    "facp": 0,
                    "annunciator": 0,
                    "monitor_modules": 0,
                    "relay_modules": 0
                }
                
                page_results = []
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                pages_to_analyze = list(range(start_page, end_page + 1))
                
                for idx, page_num in enumerate(pages_to_analyze):
                    status_text.text(f"Analyzing page {page_num} of {end_page}...")
                    progress_bar.progress((idx + 1) / len(pages_to_analyze))
                    
                    # Convert page to image
                    image_data = convert_pdf_page_to_image(file_bytes, page_num)
                    
                    if image_data:
                        result = analyze_blueprint_page(client, image_data, page_num)
                        
                        if "error" not in result:
                            page_results.append({
                                "page": page_num,
                                "type": result.get("page_type", "unknown"),
                                "description": result.get("description", ""),
                                "devices": result.get("devices", {}),
                                "notes": result.get("notes", "")
                            })
                            
                            # Add to totals
                            for device_type, count in result.get("devices", {}).items():
                                if device_type in total_devices:
                                    total_devices[device_type] += count
                
                status_text.text("✅ Analysis complete!")
                progress_bar.progress(1.0)
                
                # Store results in session state
                st.session_state['analysis_results'] = {
                    "total_devices": total_devices,
                    "page_results": page_results,
                    "filename": uploaded_file.name
                }
        
        # Display results if available
        if 'analysis_results' in st.session_state:
            results = st.session_state['analysis_results']
            total_devices = results['total_devices']
            page_results = results['page_results']
            
            st.markdown("---")
            
            # Device Count Table
            st.markdown("### 📊 Device Count")
            
            device_data = []
            prices = DEFAULT_PRICES
            
            device_mapping = {
                "smoke_detectors": ("Smoke Detectors", "smoke_detector"),
                "pull_stations": ("Pull Stations", "pull_station"),
                "horn_strobes": ("Horn/Strobes", "horn_strobe"),
                "strobes_only": ("Strobes Only", "strobe_only"),
                "horns_speakers": ("Horns/Speakers", "horn_speaker"),
                "sprinkler_heads": ("Sprinkler Heads", "sprinkler_head"),
                "facp": ("Fire Alarm Control Panel", "facp"),
                "annunciator": ("Annunciator Panels", "annunciator"),
                "monitor_modules": ("Monitor Modules", "monitor_module"),
                "relay_modules": ("Relay Modules", "relay_module")
            }
            
            for key, (display_name, price_key) in device_mapping.items():
                count = total_devices.get(key, 0)
                if count > 0 or key in ["smoke_detectors", "pull_stations", "horn_strobes", "sprinkler_heads", "facp", "annunciator", "monitor_modules", "relay_modules"]:
                    device_data.append({
                        "Device": display_name,
                        "Count": count,
                        "Unit $": f"${prices[price_key]}"
                    })
            
            df = pd.DataFrame(device_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Bid Calculation
            st.markdown("### 💰 Bid Calculation")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                overhead_pct = st.number_input("Overhead %", min_value=0, max_value=50, value=10)
            with col2:
                profit_pct = st.number_input("Profit %", min_value=0, max_value=50, value=15)
            with col3:
                misc_cost = st.number_input("Misc $", min_value=0, value=0)
            
            # Calculate totals
            material_cost = sum(
                total_devices.get(key, 0) * prices[price_key]
                for key, (_, price_key) in device_mapping.items()
            )
            
            overhead_amount = material_cost * (overhead_pct / 100)
            profit_amount = (material_cost + overhead_amount) * (profit_pct / 100)
            total_bid = material_cost + overhead_amount + profit_amount + misc_cost
            
            # Bid breakdown table
            bid_data = [
                {"Description": "Material Cost", "Amount": f"${material_cost:,.2f}"},
                {"Description": f"Overhead ({overhead_pct}%)", "Amount": f"${overhead_amount:,.2f}"},
                {"Description": f"Profit ({profit_pct}%)", "Amount": f"${profit_amount:,.2f}"},
                {"Description": "Miscellaneous", "Amount": f"${misc_cost:,.2f}"}
            ]
            
            # Display as markdown table for better styling
            st.markdown(f"""
| **Description** | **Amount** |
|-----------------|------------|
| Material Cost | ${material_cost:,.2f} |
| Overhead ({overhead_pct}%) | ${overhead_amount:,.2f} |
| Profit ({profit_pct}%) | ${profit_amount:,.2f} |
| Miscellaneous | ${misc_cost:,.2f} |
""")
            
            # Total Bid Display
            st.markdown(f"""
            <div class="total-bid-box">
                <p style="color: #888; margin-bottom: 0.5rem; font-size: 0.9rem;">TOTAL BID</p>
                <h2>${total_bid:,.2f}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Export Section
            st.markdown("### 📤 Export")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV Export
                export_df = pd.DataFrame(device_data)
                export_df['Total'] = export_df['Count'] * export_df['Unit $'].str.replace('$', '').astype(int)
                csv = export_df.to_csv(index=False)
                st.download_button(
                    "📊 Download CSV",
                    csv,
                    f"bidsync_export_{uploaded_file.name.split('.')[0]}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Summary text export
                summary = f"""BidSync AI Analysis Report
File: {uploaded_file.name}
Pages Analyzed: {len(page_results)}

DEVICE COUNTS:
"""
                for key, (display_name, _) in device_mapping.items():
                    count = total_devices.get(key, 0)
                    if count > 0:
                        summary += f"- {display_name}: {count}\n"
                
                summary += f"""
BID CALCULATION:
- Material Cost: ${material_cost:,.2f}
- Overhead ({overhead_pct}%): ${overhead_amount:,.2f}
- Profit ({profit_pct}%): ${profit_amount:,.2f}
- Miscellaneous: ${misc_cost:,.2f}
- TOTAL BID: ${total_bid:,.2f}
"""
                st.download_button(
                    "📝 Download Summary",
                    summary,
                    f"bidsync_summary_{uploaded_file.name.split('.')[0]}.txt",
                    "text/plain",
                    use_container_width=True
                )
            
            # Page-by-Page Breakdown
            with st.expander("📄 Page-by-Page Breakdown"):
                for page_result in page_results:
                    st.markdown(f"**Page {page_result['page']}** *{page_result['type']}*")
                    st.write(page_result['description'])
                    
                    # Show devices found on this page
                    devices_on_page = {k: v for k, v in page_result['devices'].items() if v > 0}
                    if devices_on_page:
                        for device, count in devices_on_page.items():
                            display_name = device.replace('_', ' ').title()
                            st.markdown(f"{display_name}")
                            st.markdown(f"**{count}**")
                    else:
                        st.write("No devices on this page")
                    
                    if page_result['notes']:
                        st.caption(page_result['notes'])
                    
                    st.markdown("---")
        
        else:
            # Single image handling
            if uploaded_file.type != "application/pdf":
                st.image(file_bytes, caption="Blueprint Preview", use_column_width=True)
                
                if st.button("🔍 Analyze Blueprint", type="primary", use_container_width=True):
                    client = anthropic.Anthropic(api_key=st.session_state['api_key'])
                    
                    with st.spinner("Analyzing blueprint..."):
                        result = analyze_blueprint_page(client, file_bytes)
                        
                        if "error" not in result:
                            st.success("Analysis complete!")
                            st.json(result)
                        else:
                            st.error(f"Error: {result['error']}")
    
    elif uploaded_file and not st.session_state.get('api_key'):
        st.warning("⚠️ Please enter your Anthropic API key in Settings above")
    
    # Footer
    st.markdown("---")
    st.caption("⚡ BidSync AI v2.0 | Built for ASAP Security")

# ============================================
# RUN APPLICATION
# ============================================
if __name__ == "__main__":
    if check_password():
        main()
# v6 dark theme
