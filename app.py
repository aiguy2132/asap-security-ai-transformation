"""
ASAP Security Fire Protection Blueprint Analyzer
Updated: November 24, 2025
Now differentiates between electrical and fire alarm devices
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
    page_title="ASAP Security - Fire Protection Blueprint Analyzer",
    page_icon="🔥",
    layout="wide"
)

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "FireProtect2025!":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct
        return True

def classify_device_type(text: str, page_context: str = "") -> str:
    """
    Classify if a device is electrical or fire alarm based on context
    
    Returns: 'electrical', 'fire_alarm', or 'both'
    """
    text = text.upper()
    page_context = page_context.upper()
    
    # Electrical indicators
    electrical_indicators = [
        '120VAC', '120V', '120 VAC', '120 V',
        '277V', '277VAC', '208V', '240V',
        'ELECTRICAL PANEL', 'PANEL SCHEDULE',
        'BRANCH CIRCUIT', 'RECEPTACLE',
        'JUNCTION BOX', 'J-BOX',
        'LINE VOLTAGE'
    ]
    
    # Fire alarm indicators  
    fire_alarm_indicators = [
        'FACP', 'FIRE ALARM CONTROL PANEL',
        'NAC', 'NOTIFICATION APPLIANCE CIRCUIT',
        'SLC', 'SIGNALING LINE CIRCUIT',
        'ADDRESSABLE', 'MODULE', 'MONITOR',
        'PULL STATION', 'MANUAL STATION',
        'HORN/STROBE', 'HORN STROBE',
        'ANNUNCIATOR', 'DUCT DETECTOR',
        'HEAT DETECTOR', 'BEAM DETECTOR',
        'FIRE ALARM', 'FA-', 'CLASS B', 'CLASS A',
        '24VDC', '24V DC', 'LOW VOLTAGE'
    ]
    
    # Check drawing title
    if 'ELECTRICAL' in page_context and 'FIRE ALARM' not in page_context:
        electrical_weight = 2
    elif 'FIRE ALARM' in page_context and 'ELECTRICAL' not in page_context:
        fire_alarm_weight = 2
    else:
        electrical_weight = 0
        fire_alarm_weight = 0
    
    # Count indicators
    for indicator in electrical_indicators:
        if indicator in text or indicator in page_context:
            electrical_weight += 1
    
    for indicator in fire_alarm_indicators:
        if indicator in text or indicator in page_context:
            fire_alarm_weight += 1
    
    # Classify based on weights
    if electrical_weight > 0 and fire_alarm_weight > 0:
        return 'both'
    elif fire_alarm_weight > electrical_weight:
        return 'fire_alarm'
    elif electrical_weight > 0:
        return 'electrical'
    else:
        # Default to fire_alarm if no clear indicators
        return 'fire_alarm'

def analyze_blueprint_with_ai(image_data: bytes, detection_mode: str) -> Dict:
    """
    Analyze blueprint using Claude Vision API with device type filtering
    
    Args:
        image_data: The blueprint image data
        detection_mode: 'all', 'fire_alarm', or 'electrical'
    """
    
    # Initialize Anthropic client
    client = anthropic.Anthropic(api_key=st.session_state.get('api_key'))
    
    # Encode image
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    # Adjust prompt based on detection mode
    mode_instruction = ""
    if detection_mode == 'fire_alarm':
        mode_instruction = """
        IMPORTANT: Only count devices that are part of the FIRE ALARM SYSTEM:
        - Connected to Fire Alarm Control Panel (FACP)
        - On NAC (Notification Appliance Circuits) or SLC (Signaling Line Circuits)
        - Low voltage (24VDC) devices
        - Has fire alarm symbols or labels
        
        DO NOT count:
        - 120VAC smoke detectors (these are electrical, not fire alarm)
        - Devices connected to electrical panels
        - Line voltage devices
        """
    elif detection_mode == 'electrical':
        mode_instruction = """
        IMPORTANT: Only count ELECTRICAL devices:
        - 120VAC smoke/CO detectors
        - Devices connected to electrical panels
        - Line voltage equipment
        
        DO NOT count:
        - Fire alarm system devices
        - Low voltage (24VDC) devices
        - Devices connected to FACP
        """
    
    prompt = f"""
    Analyze this construction blueprint and extract fire protection/electrical equipment information.
    
    {mode_instruction}
    
    Please identify and count:
    1. All smoke detectors (note if 120VAC electrical or fire alarm type)
    2. Heat detectors
    3. CO detectors (note if 120VAC electrical or fire alarm type) 
    4. Pull stations
    5. Horn/strobes
    6. Sprinkler heads
    7. Fire alarm control panels (FACP)
    8. Annunciator panels
    9. Any other fire safety devices
    
    For each device type found, provide:
    - Quantity/count
    - Type/model if visible
    - Voltage if specified (120VAC = electrical, 24VDC = fire alarm)
    - Circuit type if visible (NAC, SLC, electrical panel)
    - Location/zone if indicated
    
    Also note:
    - Drawing title and number
    - Scale if shown
    - Any relevant notes or specifications
    
    Return the information in this JSON format:
    {{
        "drawing_info": {{
            "title": "drawing title",
            "number": "drawing number",
            "type": "electrical or fire_alarm or combined",
            "scale": "scale if shown"
        }},
        "devices": [
            {{
                "device_type": "device name",
                "quantity": number,
                "system_type": "electrical or fire_alarm",
                "model": "model if shown",
                "voltage": "voltage if shown",
                "circuit": "circuit type",
                "locations": ["list of locations"]
            }}
        ],
        "notes": ["any relevant notes"],
        "total_counts": {{
            "smoke_detectors_electrical": number,
            "smoke_detectors_fire_alarm": number,
            "heat_detectors": number,
            "pull_stations": number,
            "horn_strobes": number,
            "sprinkler_heads": number
        }}
    }}
    """
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
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
        
        # Extract JSON from response
        response_text = response.content[0].text
        
        # Try to parse JSON
        try:
            # Find JSON in response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = {"error": "No JSON found in response", "raw": response_text}
        except json.JSONDecodeError:
            result = {"error": "Failed to parse JSON", "raw": response_text}
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

def main():
    st.title("🔥 ASAP Security - Fire Protection Blueprint Analyzer")
    st.markdown("**Enhanced Edition** - Now differentiates between Electrical and Fire Alarm devices")
    
    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # API Key
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=st.session_state.get('api_key', ''),
            help="Enter your Claude API key"
        )
        if api_key:
            st.session_state['api_key'] = api_key
        
        st.divider()
        
        # Detection Mode
        st.subheader("🎯 Detection Mode")
        detection_mode = st.radio(
            "Which devices to count?",
            options=[
                ('fire_alarm', '🚨 Fire Alarm Only'),
                ('electrical', '⚡ Electrical Only'),
                ('all', '📊 All Devices')
            ],
            format_func=lambda x: x[1],
            help="Fire Alarm = FACP/NAC/SLC devices\nElectrical = 120VAC devices"
        )
        
        st.info("""
        **Fire Alarm:** Low voltage devices connected to FACP
        **Electrical:** 120VAC devices on electrical circuits
        """)
        
        st.divider()
        
        # Pricing Settings
        st.subheader("💰 Unit Pricing")
        
        # Default prices with separate categories
        st.caption("Fire Alarm Devices")
        smoke_fa_price = st.number_input("Smoke Detector (Fire Alarm)", value=250, step=10)
        heat_price = st.number_input("Heat Detector", value=200, step=10)
        pull_price = st.number_input("Pull Station", value=150, step=10)
        horn_strobe_price = st.number_input("Horn/Strobe", value=175, step=10)
        
        st.caption("Electrical Devices")  
        smoke_elec_price = st.number_input("Smoke Detector (120VAC)", value=75, step=10)
        co_elec_price = st.number_input("CO Detector (120VAC)", value=80, step=10)
        
        st.caption("Other")
        sprinkler_price = st.number_input("Sprinkler Head", value=85, step=10)
        
        st.divider()
        
        # Overhead & Profit
        overhead = st.slider("Overhead %", 0, 30, 10)
        profit = st.slider("Profit %", 0, 50, 15)
    
    # Main content area
    st.header("📄 Upload Blueprint")
    
    uploaded_file = st.file_uploader(
        "Choose a blueprint file",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Upload a PDF or image file of the construction blueprint"
    )
    
    if uploaded_file is not None and api_key:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Process button
        if st.button("🔍 Analyze Blueprint", type="primary"):
            with st.spinner("🤖 AI analyzing blueprint..."):
                
                # Handle PDF vs Image
                if uploaded_file.type == "application/pdf":
                    st.warning("PDF detected - analyzing first page only. For multi-page analysis, use separate images.")
                    # Convert PDF to image
                    try:
                        pdf_bytes = uploaded_file.read()
                        # Lower DPI for smaller file size
                        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1, dpi=100)
                        
                        # Compress image to stay under 5MB limit
                        img = images[0]
                        
                        # More aggressive resize (max dimension 2000px instead of 3000)
                        max_dim = 2000
                        if max(img.size) > max_dim:
                            ratio = max_dim / max(img.size)
                            new_size = tuple(int(dim * ratio) for dim in img.size)
                            img = img.resize(new_size, Image.LANCZOS)
                        
                        # Convert to RGB if needed
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        
                        # Start with lower quality (70% instead of 85%)
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=70, optimize=True)
                        image_data = img_byte_arr.getvalue()
                        
                        # If still too large, go even lower
                        if len(image_data) > 5_000_000:  # 5MB
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='JPEG', quality=50, optimize=True)
                            image_data = img_byte_arr.getvalue()
                        
                        # Final check - if STILL too large, resize more
                        if len(image_data) > 5_000_000:
                            max_dim = 1500
                            ratio = max_dim / max(img.size)
                            new_size = tuple(int(dim * ratio) for dim in img.size)
                            img = img.resize(new_size, Image.LANCZOS)
                            img_byte_arr = io.BytesIO()
                            img.save(img_byte_arr, format='JPEG', quality=60, optimize=True)
                            image_data = img_byte_arr.getvalue()
                        
                        # Show compressed size
                        size_mb = len(image_data) / 1_000_000
                        st.info(f"✅ PDF compressed to {size_mb:.2f}MB for analysis")
                            
                    except Exception as e:
                        st.error(f"❌ PDF conversion failed: {str(e)}")
                        st.info("Please try converting your PDF to an image (PNG/JPG) first.")
                        return
                else:
                    # Process image - always convert to JPEG for API consistency
                    image_data = uploaded_file.read()
                    img = Image.open(io.BytesIO(image_data))
                    
                    # Resize if needed
                    max_dim = 3000
                    if max(img.size) > max_dim:
                        ratio = max_dim / max(img.size)
                        new_size = tuple(int(dim * ratio) for dim in img.size)
                        img = img.resize(new_size, Image.LANCZOS)
                    
                    # Convert to RGB and JPEG
                    if img.mode == 'RGBA':
                        img = img.convert('RGB')
                    
                    # Determine quality based on original size
                    quality = 70 if len(image_data) > 5_000_000 else 85
                    
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=quality, optimize=True)
                    image_data = img_byte_arr.getvalue()
                
                # Display image (works for both PDF and regular images now)
                st.subheader("📐 Blueprint Preview")
                st.image(image_data, use_column_width=True)
                
                # Analyze with AI (works for both PDF and regular images now)
                result = analyze_blueprint_with_ai(image_data, detection_mode[0])
                
                if "error" in result:
                    st.error(f"❌ Analysis failed: {result['error']}")
                    if "raw" in result:
                        with st.expander("Show raw response"):
                            st.text(result["raw"])
                else:
                    # Display results
                    col1, col2 = st.columns(2)
                        
                    with col1:
                        st.subheader("📊 Device Count")
                        
                        if "total_counts" in result:
                            counts = result["total_counts"]
                            
                            # Show counts based on mode
                            if detection_mode[0] in ['fire_alarm', 'all']:
                                st.metric("🚨 Smoke Detectors (Fire Alarm)", 
                                        counts.get("smoke_detectors_fire_alarm", 0))
                                st.metric("🌡️ Heat Detectors", counts.get("heat_detectors", 0))
                                st.metric("🔔 Pull Stations", counts.get("pull_stations", 0))
                                st.metric("📢 Horn/Strobes", counts.get("horn_strobes", 0))
                            
                            if detection_mode[0] in ['electrical', 'all']:
                                st.metric("⚡ Smoke Detectors (120VAC)", 
                                        counts.get("smoke_detectors_electrical", 0))
                            
                            if detection_mode[0] == 'all':
                                st.metric("💧 Sprinkler Heads", counts.get("sprinkler_heads", 0))
                    
                    with col2:
                        st.subheader("💵 Cost Estimate")
                        
                        # Calculate costs
                        total_cost = 0
                        
                        if "total_counts" in result:
                            counts = result["total_counts"]
                            
                            if detection_mode[0] in ['fire_alarm', 'all']:
                                total_cost += counts.get("smoke_detectors_fire_alarm", 0) * smoke_fa_price
                                total_cost += counts.get("heat_detectors", 0) * heat_price
                                total_cost += counts.get("pull_stations", 0) * pull_price
                                total_cost += counts.get("horn_strobes", 0) * horn_strobe_price
                            
                            if detection_mode[0] in ['electrical', 'all']:
                                total_cost += counts.get("smoke_detectors_electrical", 0) * smoke_elec_price
                            
                            if detection_mode[0] == 'all':
                                total_cost += counts.get("sprinkler_heads", 0) * sprinkler_price
                        
                        # Add overhead and profit
                        subtotal = total_cost
                        overhead_amount = subtotal * (overhead / 100)
                        profit_amount = (subtotal + overhead_amount) * (profit / 100)
                        final_total = subtotal + overhead_amount + profit_amount
                        
                        st.metric("📦 Material Cost", f"${subtotal:,.2f}")
                        st.metric("🏢 Overhead", f"${overhead_amount:,.2f}")
                        st.metric("💰 Profit", f"${profit_amount:,.2f}")
                        st.metric("✅ **TOTAL BID**", f"${final_total:,.2f}")
                    
                    # Detailed breakdown
                    with st.expander("📋 Detailed Device Breakdown"):
                        if "devices" in result:
                            for device in result["devices"]:
                                st.write(f"""
                                **{device.get('device_type', 'Unknown')}**
                                - Quantity: {device.get('quantity', 0)}
                                - System: {device.get('system_type', 'Unknown')}
                                - Voltage: {device.get('voltage', 'Not specified')}
                                - Circuit: {device.get('circuit', 'Not specified')}
                                """)
                    
                    # Drawing info
                    with st.expander("📐 Drawing Information"):
                        if "drawing_info" in result:
                            info = result["drawing_info"]
                            st.write(f"""
                            - **Title:** {info.get('title', 'Not found')}
                            - **Number:** {info.get('number', 'Not found')}
                            - **Type:** {info.get('type', 'Not detected')}
                            - **Scale:** {info.get('scale', 'Not shown')}
                            """)
                        
                        # Export functionality
                        st.divider()
                        st.subheader("📥 Export Results")
                        
                        # Create export data
                        export_data = {
                            "Project": uploaded_file.name,
                            "Detection Mode": detection_mode[1],
                            **{k.replace('_', ' ').title(): v for k, v in counts.items()},
                            "Material Cost": subtotal,
                            "Overhead": overhead_amount,
                            "Profit": profit_amount,
                            "Total Bid": final_total
                        }
                        
                        df = pd.DataFrame([export_data])
                        csv = df.to_csv(index=False)
                        
                        st.download_button(
                            label="📊 Download as CSV",
                            data=csv,
                            file_name=f"estimate_{uploaded_file.name.split('.')[0]}.csv",
                            mime="text/csv"
                        )
    
    elif not api_key:
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to begin")
    
    # Footer
    st.divider()
    st.caption("Built for ASAP Security | Fire Protection Blueprint Analysis System v2.0")
    st.caption("Now with Electrical vs Fire Alarm device differentiation")

if __name__ == "__main__":
    if check_password():
        main()
