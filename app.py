"""
BidSync AI - Fire Protection Blueprint Analyzer
Clean, modern interface with multi-page PDF support
"""

import streamlit as st
import anthropic
import base64
import json
from PIL import Image
import io
import pandas as pd
from pdf2image import convert_from_bytes
import time

# Page config - dark theme
st.set_page_config(
    page_title="BidSync AI - Blueprint Analyzer",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark, sexy design
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default hamburger menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 900px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Logo/Brand header */
    .brand-header {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    
    .brand-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00d4ff, #7b2cbf, #ff6b6b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .brand-subtitle {
        color: #a0a0a0;
        font-size: 1.1rem;
        font-weight: 300;
    }
    
    /* Cards */
    .card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(10px);
    }
    
    .card-title {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Results table */
    .results-table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .results-table th {
        background: rgba(0, 212, 255, 0.2);
        color: #00d4ff;
        padding: 12px 16px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid rgba(0, 212, 255, 0.3);
    }
    
    .results-table td {
        padding: 12px 16px;
        color: #ffffff;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .results-table tr:hover {
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* Total row */
    .total-row {
        background: rgba(0, 212, 255, 0.1) !important;
        font-weight: 600;
    }
    
    .total-row td {
        color: #00d4ff !important;
        font-size: 1.1rem;
    }
    
    /* Bid total */
    .bid-total {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(123, 44, 191, 0.2));
        border-radius: 16px;
        margin-top: 1.5rem;
    }
    
    .bid-label {
        color: #a0a0a0;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 0.5rem;
    }
    
    .bid-amount {
        color: #00d4ff;
        font-size: 3rem;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00d4ff, #7b2cbf) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        width: 100% !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 40px rgba(0, 212, 255, 0.3) !important;
    }
    
    /* File uploader */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.05);
        border: 2px dashed rgba(0, 212, 255, 0.3);
        border-radius: 16px;
        padding: 1rem;
    }
    
    .stFileUploader:hover {
        border-color: rgba(0, 212, 255, 0.6);
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #00d4ff, #7b2cbf) !important;
    }
    
    /* Input fields */
    .stNumberInput input, .stTextInput input {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* Success/Info messages */
    .stSuccess, .stInfo {
        background: rgba(0, 212, 255, 0.1) !important;
        color: #00d4ff !important;
        border: 1px solid rgba(0, 212, 255, 0.3) !important;
        border-radius: 12px !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        color: white !important;
    }
    
    /* Password input */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Page analysis cards */
    .page-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .page-number {
        color: #00d4ff;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        margin: 2rem 0;
    }
    
    /* Data editor styling */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
    }
    
    /* Labels */
    .stNumberInput label, .stTextInput label {
        color: #a0a0a0 !important;
    }
</style>
""", unsafe_allow_html=True)


def check_password():
    """Simple password protection"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.markdown("""
        <div class="brand-header">
            <div class="brand-title">⚡ BidSync AI</div>
            <div class="brand-subtitle">Fire Protection Blueprint Analyzer</div>
        </div>
        """, unsafe_allow_html=True)
        
        password = st.text_input("Enter password to continue", type="password")
        if password == "FireProtect2025!":
            st.session_state.authenticated = True
            st.rerun()
        elif password:
            st.error("Incorrect password")
        return False
    return True


def analyze_page(image_data: bytes, api_key: str, page_num: int) -> dict:
    """Analyze a single blueprint page"""
    
    client = anthropic.Anthropic(api_key=api_key)
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    prompt = """Analyze this fire protection/electrical blueprint page and count ALL devices you can see.

Count these device types:
1. Smoke Detectors (any type - addressable, photoelectric, ionization)
2. Heat Detectors
3. Duct Detectors  
4. Pull Stations / Manual Stations
5. Horn/Strobes (notification appliances)
6. Strobes only
7. Horns/Speakers only
8. Sprinkler Heads
9. Fire Alarm Control Panel (FACP)
10. Annunciator panels
11. Door Holders (magnetic)
12. Monitor Modules
13. Relay Modules
14. CO Detectors
15. Duct Smoke Detectors

BE THOROUGH - count every single device symbol you can identify on this page.
If you see a symbol repeated multiple times, count each instance.

Look for common blueprint symbols:
- Circles with "S" or "SD" = Smoke Detector
- Circles with "H" or "HD" = Heat Detector
- Squares with horn symbol = Horn/Strobe
- Small circles in grid patterns = Sprinkler Heads
- Diamond shapes = Pull Stations

Return ONLY valid JSON in this exact format (no other text):
{
    "page_type": "floor plan" or "legend" or "cover" or "details" or "schedule",
    "devices": {
        "smoke_detectors": 0,
        "heat_detectors": 0,
        "duct_detectors": 0,
        "pull_stations": 0,
        "horn_strobes": 0,
        "strobes": 0,
        "horns_speakers": 0,
        "sprinkler_heads": 0,
        "facp": 0,
        "annunciators": 0,
        "door_holders": 0,
        "monitor_modules": 0,
        "relay_modules": 0,
        "co_detectors": 0,
        "duct_smoke_detectors": 0
    },
    "notes": "any relevant observations about this page"
}"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }]
        )
        
        response_text = response.content[0].text
        
        # Extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            result = json.loads(response_text[json_start:json_end])
            result['page_num'] = page_num
            return result
        else:
            return {"error": "No JSON found", "page_num": page_num}
            
    except Exception as e:
        return {"error": str(e), "page_num": page_num}


def process_pdf(pdf_bytes: bytes, max_pages: int = None) -> list:
    """Convert PDF to list of images"""
    try:
        images = convert_from_bytes(pdf_bytes, dpi=120)
        if max_pages:
            images = images[:max_pages]
        return images
    except Exception as e:
        st.error(f"PDF conversion failed: {e}")
        return []


def compress_image(img) -> bytes:
    """Compress image for API"""
    # Resize if needed
    max_dim = 2000
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = tuple(int(dim * ratio) for dim in img.size)
        img = img.resize(new_size, Image.LANCZOS)
    
    # Convert to RGB
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Compress to JPEG
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=75, optimize=True)
    return buffer.getvalue()


def main():
    # Brand header
    st.markdown("""
    <div class="brand-header">
        <div class="brand-title">⚡ BidSync AI</div>
        <div class="brand-subtitle">Fire Protection Blueprint Analyzer</div>
    </div>
    """, unsafe_allow_html=True)
    
    # API Key (hidden in expander)
    with st.expander("⚙️ Settings", expanded=False):
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=st.session_state.get('api_key', ''),
            help="Your Claude API key"
        )
        if api_key:
            st.session_state['api_key'] = api_key
    
    # Check for API key
    if not st.session_state.get('api_key'):
        st.info("👆 Enter your API key in Settings to get started")
        return
    
    # Upload section
    st.markdown("### 📄 Upload Blueprint")
    
    uploaded_file = st.file_uploader(
        "Drop your PDF or image here",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        label_visibility="collapsed"
    )
    
    if uploaded_file:
        st.success(f"✓ {uploaded_file.name} ({uploaded_file.size / 1_000_000:.1f} MB)")
        
        # Page selection for PDFs
        if uploaded_file.type == "application/pdf":
            pdf_bytes = uploaded_file.read()
            uploaded_file.seek(0)  # Reset for later
            
            # Get page count
            try:
                all_images = convert_from_bytes(pdf_bytes, dpi=50)  # Low DPI just for counting
                total_pages = len(all_images)
                st.info(f"📑 {total_pages} pages detected")
                
                # Page range selection
                col1, col2 = st.columns(2)
                with col1:
                    start_page = st.number_input("Start page", min_value=1, max_value=total_pages, value=1)
                with col2:
                    end_page = st.number_input("End page", min_value=1, max_value=total_pages, value=min(total_pages, 10))
                
                if end_page < start_page:
                    end_page = start_page
                    
            except Exception as e:
                st.error(f"Could not read PDF: {e}")
                return
        
        # Analyze button
        if st.button("🔍 Analyze Blueprint", use_container_width=True):
            
            results = []
            all_devices = {
                "smoke_detectors": 0,
                "heat_detectors": 0,
                "duct_detectors": 0,
                "pull_stations": 0,
                "horn_strobes": 0,
                "strobes": 0,
                "horns_speakers": 0,
                "sprinkler_heads": 0,
                "facp": 0,
                "annunciators": 0,
                "door_holders": 0,
                "monitor_modules": 0,
                "relay_modules": 0,
                "co_detectors": 0,
                "duct_smoke_detectors": 0
            }
            
            if uploaded_file.type == "application/pdf":
                # Multi-page PDF analysis
                pdf_bytes = uploaded_file.read()
                
                with st.spinner("Converting PDF..."):
                    images = convert_from_bytes(pdf_bytes, dpi=120)
                    selected_images = images[start_page-1:end_page]
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, img in enumerate(selected_images):
                    page_num = start_page + i
                    status_text.text(f"Analyzing page {page_num} of {end_page}...")
                    progress_bar.progress((i + 1) / len(selected_images))
                    
                    # Compress and analyze
                    img_data = compress_image(img)
                    result = analyze_page(img_data, st.session_state['api_key'], page_num)
                    results.append(result)
                    
                    # Aggregate counts
                    if "devices" in result:
                        for device, count in result["devices"].items():
                            if device in all_devices:
                                all_devices[device] += count
                    
                    time.sleep(0.5)  # Rate limiting
                
                progress_bar.empty()
                status_text.empty()
                
            else:
                # Single image
                with st.spinner("Analyzing..."):
                    img = Image.open(uploaded_file)
                    img_data = compress_image(img)
                    result = analyze_page(img_data, st.session_state['api_key'], 1)
                    results.append(result)
                    
                    if "devices" in result:
                        all_devices = result["devices"]
            
            # Store results in session
            st.session_state['results'] = all_devices
            st.session_state['page_results'] = results
    
    # Display results if available
    if 'results' in st.session_state:
        st.markdown("---")
        
        devices = st.session_state['results']
        
        # Default pricing
        default_prices = {
            "smoke_detectors": 250,
            "heat_detectors": 200,
            "duct_detectors": 350,
            "pull_stations": 150,
            "horn_strobes": 175,
            "strobes": 125,
            "horns_speakers": 150,
            "sprinkler_heads": 85,
            "facp": 3500,
            "annunciators": 1200,
            "door_holders": 175,
            "monitor_modules": 125,
            "relay_modules": 125,
            "co_detectors": 175,
            "duct_smoke_detectors": 400
        }
        
        # Nice device names
        device_names = {
            "smoke_detectors": "Smoke Detectors",
            "heat_detectors": "Heat Detectors",
            "duct_detectors": "Duct Detectors",
            "pull_stations": "Pull Stations",
            "horn_strobes": "Horn/Strobes",
            "strobes": "Strobes Only",
            "horns_speakers": "Horns/Speakers",
            "sprinkler_heads": "Sprinkler Heads",
            "facp": "Fire Alarm Control Panel",
            "annunciators": "Annunciator Panels",
            "door_holders": "Door Holders",
            "monitor_modules": "Monitor Modules",
            "relay_modules": "Relay Modules",
            "co_detectors": "CO Detectors",
            "duct_smoke_detectors": "Duct Smoke Detectors"
        }
        
        st.markdown("### 📊 Device Count")
        
        # Build results table
        table_data = []
        for device_key, count in devices.items():
            if count > 0:  # Only show devices with counts
                table_data.append({
                    "Device": device_names.get(device_key, device_key),
                    "Count": count,
                    "Unit Price": default_prices.get(device_key, 100),
                    "key": device_key
                })
        
        if table_data:
            # Create editable dataframe
            df = pd.DataFrame(table_data)
            
            # Editable table
            edited_df = st.data_editor(
                df[["Device", "Count", "Unit Price"]],
                column_config={
                    "Device": st.column_config.TextColumn("Device", disabled=True),
                    "Count": st.column_config.NumberColumn("Count", min_value=0),
                    "Unit Price": st.column_config.NumberColumn("Unit $", min_value=0, format="$%d")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Calculate totals
            edited_df["Total"] = edited_df["Count"] * edited_df["Unit Price"]
            subtotal = edited_df["Total"].sum()
            
            st.markdown("---")
            
            # Pricing adjustments
            st.markdown("### 💰 Bid Calculation")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                overhead_pct = st.number_input("Overhead %", value=10, min_value=0, max_value=50)
            with col2:
                profit_pct = st.number_input("Profit %", value=15, min_value=0, max_value=50)
            with col3:
                misc_cost = st.number_input("Misc $", value=0, min_value=0)
            
            overhead = subtotal * (overhead_pct / 100)
            profit = (subtotal + overhead) * (profit_pct / 100)
            total_bid = subtotal + overhead + profit + misc_cost
            
            # Summary table
            st.markdown(f"""
| Description | Amount |
|:---|---:|
| **Material Cost** | ${subtotal:,.2f} |
| Overhead ({overhead_pct}%) | ${overhead:,.2f} |
| Profit ({profit_pct}%) | ${profit:,.2f} |
| Miscellaneous | ${misc_cost:,.2f} |
            """)
            
            # Big total
            st.markdown(f"""
            <div class="bid-total">
                <div class="bid-label">Total Bid</div>
                <div class="bid-amount">${total_bid:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Export section
            st.markdown("---")
            st.markdown("### 📥 Export")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # CSV Export
                export_df = edited_df.copy()
                export_df["Total"] = export_df["Count"] * export_df["Unit Price"]
                
                # Add summary rows
                summary_data = [
                    {"Device": "", "Count": "", "Unit Price": "", "Total": ""},
                    {"Device": "SUBTOTAL", "Count": "", "Unit Price": "", "Total": subtotal},
                    {"Device": f"Overhead ({overhead_pct}%)", "Count": "", "Unit Price": "", "Total": overhead},
                    {"Device": f"Profit ({profit_pct}%)", "Count": "", "Unit Price": "", "Total": profit},
                    {"Device": "TOTAL BID", "Count": "", "Unit Price": "", "Total": total_bid},
                ]
                summary_df = pd.DataFrame(summary_data)
                
                final_export = pd.concat([export_df, summary_df], ignore_index=True)
                csv = final_export.to_csv(index=False)
                
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    file_name="bidsync_estimate.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Text summary
                lines = [f"- {row['Device']}: {row['Count']} @ ${row['Unit Price']} = ${row['Count'] * row['Unit Price']:,.2f}" 
                        for _, row in edited_df.iterrows()]
                
                summary_text = f"""BidSync AI Estimate
========================

DEVICES:
{chr(10).join(lines)}

TOTALS:
- Material Subtotal: ${subtotal:,.2f}
- Overhead ({overhead_pct}%): ${overhead:,.2f}
- Profit ({profit_pct}%): ${profit:,.2f}
- Misc: ${misc_cost:,.2f}

========================
TOTAL BID: ${total_bid:,.2f}
========================
"""
                st.download_button(
                    "📋 Download Summary",
                    summary_text,
                    file_name="bidsync_summary.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        else:
            st.warning("No devices detected on analyzed pages. Try selecting different pages.")
        
        # Page-by-page breakdown
        if 'page_results' in st.session_state and len(st.session_state['page_results']) > 1:
            with st.expander("📑 Page-by-Page Breakdown"):
                for result in st.session_state['page_results']:
                    if "error" in result:
                        st.error(f"Page {result.get('page_num', '?')}: {result['error']}")
                    else:
                        page_num = result.get('page_num', '?')
                        page_type = result.get('page_type', 'unknown')
                        notes = result.get('notes', '')
                        
                        st.markdown(f"**Page {page_num}** _{page_type}_")
                        if notes:
                            st.caption(notes)
                        
                        # Show non-zero counts
                        if "devices" in result:
                            non_zero = {k: v for k, v in result["devices"].items() if v > 0}
                            if non_zero:
                                cols = st.columns(4)
                                for i, (k, v) in enumerate(non_zero.items()):
                                    cols[i % 4].metric(k.replace("_", " ").title(), v)
                            else:
                                st.caption("No devices on this page")
                        st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0; color: #666;">
        <small>⚡ BidSync AI v2.0 | Built for ASAP Security</small>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    if check_password():
        main()
