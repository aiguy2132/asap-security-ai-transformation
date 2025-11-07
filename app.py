import streamlit as st
import anthropic
import base64
from PIL import Image
import io
import json
import csv
from io import StringIO

import hmac

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], "FireProtect2025!"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "🔒 Enter Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# Set up the page
st.set_page_config(page_title="Fire Protection Blueprint Analyzer", layout="wide")

# Initialize session state for analysis results
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'pricing_data' not in st.session_state:
    st.session_state.pricing_data = {
        'sprinkler_heads': 45.0,
        'smoke_detectors': 85.0,
        'heat_detectors': 75.0,
        'pull_stations': 120.0,
        'horn_strobes': 95.0,
        'control_panel': 2500.0,
        'wire_per_foot': 0.85,
        'conduit_per_foot': 1.25,
        'labor_rate': 75.0,
        'overhead_percent': 15.0,
        'profit_percent': 20.0
    }
if 'last_estimate' not in st.session_state:
    st.session_state.last_estimate = None

# Title
st.title("🔥 Fire Protection Blueprint Analyzer")
st.markdown("### AI-Powered Material Takeoff & Estimation System")

# Sidebar for API key and pricing
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Enter your Anthropic API Key:", type="password")
    
    st.markdown("---")
    st.markdown("### 💰 Pricing Calculator")
    
    with st.expander("Unit Costs", expanded=False):
        st.session_state.pricing_data['sprinkler_heads'] = st.number_input(
            "Sprinkler Head ($)", 
            value=st.session_state.pricing_data['sprinkler_heads'], 
            min_value=0.0, 
            step=5.0
        )
        st.session_state.pricing_data['smoke_detectors'] = st.number_input(
            "Smoke Detector ($)", 
            value=st.session_state.pricing_data['smoke_detectors'], 
            min_value=0.0, 
            step=5.0
        )
        st.session_state.pricing_data['heat_detectors'] = st.number_input(
            "Heat Detector ($)", 
            value=st.session_state.pricing_data['heat_detectors'], 
            min_value=0.0, 
            step=5.0
        )
        st.session_state.pricing_data['pull_stations'] = st.number_input(
            "Pull Station ($)", 
            value=st.session_state.pricing_data['pull_stations'], 
            min_value=0.0, 
            step=5.0
        )
        st.session_state.pricing_data['horn_strobes'] = st.number_input(
            "Horn/Strobe ($)", 
            value=st.session_state.pricing_data['horn_strobes'], 
            min_value=0.0, 
            step=5.0
        )
        st.session_state.pricing_data['control_panel'] = st.number_input(
            "Control Panel ($)", 
            value=st.session_state.pricing_data['control_panel'], 
            min_value=0.0, 
            step=100.0
        )
        st.session_state.pricing_data['wire_per_foot'] = st.number_input(
            "Wire ($/ft)", 
            value=st.session_state.pricing_data['wire_per_foot'], 
            min_value=0.0, 
            step=0.10
        )
        st.session_state.pricing_data['conduit_per_foot'] = st.number_input(
            "Conduit ($/ft)", 
            value=st.session_state.pricing_data['conduit_per_foot'], 
            min_value=0.0, 
            step=0.10
        )
    
    with st.expander("Labor & Markup", expanded=False):
        st.session_state.pricing_data['labor_rate'] = st.number_input(
            "Labor Rate ($/hr)", 
            value=st.session_state.pricing_data['labor_rate'], 
            min_value=0.0, 
            step=5.0
        )
        st.session_state.pricing_data['overhead_percent'] = st.number_input(
            "Overhead (%)", 
            value=st.session_state.pricing_data['overhead_percent'], 
            min_value=0.0, 
            max_value=100.0, 
            step=1.0
        )
        st.session_state.pricing_data['profit_percent'] = st.number_input(
            "Profit Margin (%)", 
            value=st.session_state.pricing_data['profit_percent'], 
            min_value=0.0, 
            max_value=100.0, 
            step=1.0
        )
    
    st.markdown("---")
    st.markdown("**Upload a blueprint PDF or image to analyze:**")
    st.markdown("- Fire alarm systems")
    st.markdown("- Sprinkler systems")
    st.markdown("- Security cameras")
    st.markdown("- Access control")

# Main content area
if api_key:
    # File uploader
    uploaded_file = st.file_uploader("Upload Blueprint (PDF or Image)", type=['pdf', 'png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        # Display the uploaded file
        st.subheader("Uploaded Blueprint")
        
        # Convert file to image for display
        if uploaded_file.type == "application/pdf":
            st.info("PDF uploaded. Click 'Analyze Blueprint' to process.")
        else:
            image = Image.open(uploaded_file)
            st.image(image, use_column_width=True)
        
        # Analyze button
        if st.button("🔍 Analyze Blueprint", type="primary"):
            with st.spinner("Analyzing blueprint with AI... This may take 30-60 seconds..."):
                try:
                    # Read the file
                    file_bytes = uploaded_file.getvalue()
                    
                    # Convert to base64
                    base64_image = base64.b64encode(file_bytes).decode('utf-8')
                    
                    # Determine media type
                    if uploaded_file.type == "application/pdf":
                        media_type = "application/pdf"
                        source_type = "document"
                    elif uploaded_file.type == "image/png":
                        media_type = "image/png"
                        source_type = "image"
                    elif uploaded_file.type in ["image/jpeg", "image/jpg"]:
                        media_type = "image/jpeg"
                        source_type = "image"
                    else:
                        st.error("Unsupported file type")
                        st.stop()
                    
                    # Create Anthropic client
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    # Create the analysis prompt
                    prompt = """Analyze this fire protection/security blueprint and extract the following information in a structured format.

IMPORTANT: Provide ONLY numerical counts for devices. Be specific and accurate.

1. PROJECT DETAILS:
   - Project name
   - Location
   - Building type
   - Total square footage
   - Number of floors

2. FIRE ALARM SYSTEM (provide exact counts):
   - Smoke detectors: [number only]
   - Heat detectors: [number only]
   - Pull stations: [number only]
   - Strobes: [number only]
   - Horn/strobes: [number only]
   - Fire alarm control panel: [yes/no and model if visible]

3. SPRINKLER SYSTEM (provide exact counts):
   - Total sprinkler heads: [number only]
   - Sprinkler zones: [number]
   - Riser locations: [describe]
   - Coverage area: [square footage if visible]

4. SECURITY SYSTEMS (provide exact counts):
   - Cameras/CCTV: [number only]
   - Motion sensors: [number only]
   - Access control points: [number only]
   - Door contacts: [number only]

5. ESTIMATED MEASUREMENTS:
   - Estimated wire length needed (in feet): [number]
   - Estimated conduit length (in feet): [number]
   - Estimated labor hours: [number]

6. CIRCUIT CALCULATIONS:
   - Estimate NAC (Notification Appliance Circuit) requirements
   - Estimate SLC/IDC (Signaling Line Circuit) requirements
   - Power requirements

Please provide a detailed, organized analysis. If certain information is not visible in the blueprint, note that it's "Not visible in drawing" rather than guessing. 

For device counts, if you can see devices clearly, provide the actual count. If you cannot determine exact counts, note "Cannot determine from drawing"."""

                    # Make API call to Claude
                    if source_type == "document":
                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=4000,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "document",
                                            "source": {
                                                "type": "base64",
                                                "media_type": media_type,
                                                "data": base64_image
                                            }
                                        },
                                        {
                                            "type": "text",
                                            "text": prompt
                                        }
                                    ]
                                }
                            ]
                        )
                    else:  # image
                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=4000,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": media_type,
                                                "data": base64_image
                                            }
                                        },
                                        {
                                            "type": "text",
                                            "text": prompt
                                        }
                                    ]
                                }
                            ]
                        )
                    
                    # Extract the response
                    analysis = message.content[0].text
                    st.session_state.analysis_results = analysis
                    
                    st.success("Analysis Complete!")
                    
                except Exception as e:
                    st.error(f"Error analyzing blueprint: {str(e)}")
                    st.info("Make sure your API key is correct and you have sufficient credits.")
        
        # Display results if they exist
        if st.session_state.analysis_results:
            st.subheader("📊 Blueprint Analysis Results")
            st.markdown(st.session_state.analysis_results)
            
            # Download button for analysis
            st.download_button(
                label="📥 Download Analysis as Text",
                data=st.session_state.analysis_results,
                file_name="blueprint_analysis.txt",
                mime="text/plain"
            )
            
            st.markdown("---")
            
            # PRICING ESTIMATE SECTION
            st.subheader("💰 Cost Estimate")
            
            st.info("📝 Adjust device counts below based on the analysis, then click 'Calculate Estimate'")
            
            # Create input fields for quantities
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Fire Alarm Devices**")
                qty_smoke = st.number_input("Smoke Detectors (qty)", min_value=0, value=0, step=1, key="qty_smoke")
                qty_heat = st.number_input("Heat Detectors (qty)", min_value=0, value=0, step=1, key="qty_heat")
                qty_pull = st.number_input("Pull Stations (qty)", min_value=0, value=0, step=1, key="qty_pull")
                qty_horn = st.number_input("Horn/Strobes (qty)", min_value=0, value=0, step=1, key="qty_horn")
                qty_panel = st.number_input("Control Panels (qty)", min_value=0, value=0, step=1, key="qty_panel")
            
            with col2:
                st.markdown("**Sprinkler & Other**")
                qty_sprinklers = st.number_input("Sprinkler Heads (qty)", min_value=0, value=0, step=1, key="qty_sprinklers")
                qty_wire = st.number_input("Wire Length (feet)", min_value=0, value=0, step=100, key="qty_wire")
                qty_conduit = st.number_input("Conduit Length (feet)", min_value=0, value=0, step=100, key="qty_conduit")
                labor_hours = st.number_input("Estimated Labor (hours)", min_value=0.0, value=0.0, step=1.0, key="labor_hours")
            
            if st.button("💵 Calculate Estimate", type="primary"):
                # Calculate material costs
                material_cost = (
                    (qty_smoke * st.session_state.pricing_data['smoke_detectors']) +
                    (qty_heat * st.session_state.pricing_data['heat_detectors']) +
                    (qty_pull * st.session_state.pricing_data['pull_stations']) +
                    (qty_horn * st.session_state.pricing_data['horn_strobes']) +
                    (qty_panel * st.session_state.pricing_data['control_panel']) +
                    (qty_sprinklers * st.session_state.pricing_data['sprinkler_heads']) +
                    (qty_wire * st.session_state.pricing_data['wire_per_foot']) +
                    (qty_conduit * st.session_state.pricing_data['conduit_per_foot'])
                )
                
                # Calculate labor cost
                labor_cost = labor_hours * st.session_state.pricing_data['labor_rate']
                
                # Calculate subtotal
                subtotal = material_cost + labor_cost
                
                # Calculate overhead
                overhead = subtotal * (st.session_state.pricing_data['overhead_percent'] / 100)
                
                # Calculate total with overhead
                total_with_overhead = subtotal + overhead
                
                # Calculate profit
                profit = total_with_overhead * (st.session_state.pricing_data['profit_percent'] / 100)
                
                # Calculate final total
                final_total = total_with_overhead + profit
                
                # Store estimate data for export
                st.session_state.last_estimate = {
                    'quantities': {
                        'smoke_detectors': qty_smoke,
                        'heat_detectors': qty_heat,
                        'pull_stations': qty_pull,
                        'horn_strobes': qty_horn,
                        'control_panels': qty_panel,
                        'sprinkler_heads': qty_sprinklers,
                        'wire_feet': qty_wire,
                        'conduit_feet': qty_conduit,
                        'labor_hours': labor_hours
                    },
                    'costs': {
                        'material_cost': material_cost,
                        'labor_cost': labor_cost,
                        'subtotal': subtotal,
                        'overhead': overhead,
                        'total_with_overhead': total_with_overhead,
                        'profit': profit,
                        'final_total': final_total
                    },
                    'unit_prices': st.session_state.pricing_data.copy()
                }
                
                # Display results
                st.markdown("---")
                st.subheader("📈 Cost Breakdown")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Material Cost", f"${material_cost:,.2f}")
                    st.metric("Labor Cost", f"${labor_cost:,.2f}")
                
                with col2:
                    st.metric("Subtotal", f"${subtotal:,.2f}")
                    st.metric("Overhead ({:.0f}%)".format(st.session_state.pricing_data['overhead_percent']), f"${overhead:,.2f}")
                
                with col3:
                    st.metric("Total + Overhead", f"${total_with_overhead:,.2f}")
                    st.metric("Profit ({:.0f}%)".format(st.session_state.pricing_data['profit_percent']), f"${profit:,.2f}")
                
                st.markdown("---")
                st.markdown("### 🎯 **FINAL ESTIMATE**")
                st.markdown(f"# ${final_total:,.2f}")
                
                # Detailed breakdown
                with st.expander("View Detailed Breakdown"):
                    breakdown_text = f"""
# DETAILED COST ESTIMATE

## MATERIALS
- Smoke Detectors: {qty_smoke} × ${st.session_state.pricing_data['smoke_detectors']:.2f} = ${qty_smoke * st.session_state.pricing_data['smoke_detectors']:,.2f}
- Heat Detectors: {qty_heat} × ${st.session_state.pricing_data['heat_detectors']:.2f} = ${qty_heat * st.session_state.pricing_data['heat_detectors']:,.2f}
- Pull Stations: {qty_pull} × ${st.session_state.pricing_data['pull_stations']:.2f} = ${qty_pull * st.session_state.pricing_data['pull_stations']:,.2f}
- Horn/Strobes: {qty_horn} × ${st.session_state.pricing_data['horn_strobes']:.2f} = ${qty_horn * st.session_state.pricing_data['horn_strobes']:,.2f}
- Control Panels: {qty_panel} × ${st.session_state.pricing_data['control_panel']:.2f} = ${qty_panel * st.session_state.pricing_data['control_panel']:,.2f}
- Sprinkler Heads: {qty_sprinklers} × ${st.session_state.pricing_data['sprinkler_heads']:.2f} = ${qty_sprinklers * st.session_state.pricing_data['sprinkler_heads']:,.2f}
- Wire: {qty_wire} ft × ${st.session_state.pricing_data['wire_per_foot']:.2f}/ft = ${qty_wire * st.session_state.pricing_data['wire_per_foot']:,.2f}
- Conduit: {qty_conduit} ft × ${st.session_state.pricing_data['conduit_per_foot']:.2f}/ft = ${qty_conduit * st.session_state.pricing_data['conduit_per_foot']:,.2f}

**Material Subtotal: ${material_cost:,.2f}**

## LABOR
- Labor Hours: {labor_hours} hrs × ${st.session_state.pricing_data['labor_rate']:.2f}/hr = ${labor_cost:,.2f}

**Labor Subtotal: ${labor_cost:,.2f}**

## SUMMARY
- Materials: ${material_cost:,.2f}
- Labor: ${labor_cost:,.2f}
- **Subtotal: ${subtotal:,.2f}**

- Overhead ({st.session_state.pricing_data['overhead_percent']:.0f}%): ${overhead:,.2f}
- **Total with Overhead: ${total_with_overhead:,.2f}**

- Profit Margin ({st.session_state.pricing_data['profit_percent']:.0f}%): ${profit:,.2f}

## FINAL TOTAL: ${final_total:,.2f}
"""
                    st.text(breakdown_text)
                    
                    # Download button for estimate
                    st.download_button(
                        label="📥 Download Detailed Estimate",
                        data=breakdown_text,
                        file_name="cost_estimate.txt",
                        mime="text/plain",
                        key="download_text_estimate"
                    )
            
            # Google Sheets Export Section
            if st.session_state.last_estimate:
                st.markdown("---")
                st.subheader("📤 Export to Google Sheets")
                
                st.info("💡 Click below to download a CSV file that you can import into Google Sheets")
                
                # Create CSV data
                csv_data = []
                
                # Header
                csv_data.append(["FIRE PROTECTION PROJECT ESTIMATE"])
                csv_data.append([])
                
                # Project Info Section
                csv_data.append(["PROJECT INFORMATION"])
                csv_data.append(["Date", ""])  # Client can fill in
                csv_data.append(["Project Name", ""])
                csv_data.append(["Location", ""])
                csv_data.append(["Prepared By", ""])
                csv_data.append([])
                
                # Material Takeoff Section
                csv_data.append(["MATERIAL TAKEOFF"])
                csv_data.append(["Item", "Quantity", "Unit Price", "Total"])
                
                est = st.session_state.last_estimate
                
                # Fire Alarm Devices
                csv_data.append(["Smoke Detectors", est['quantities']['smoke_detectors'], 
                               f"${est['unit_prices']['smoke_detectors']:.2f}", 
                               f"${est['quantities']['smoke_detectors'] * est['unit_prices']['smoke_detectors']:.2f}"])
                csv_data.append(["Heat Detectors", est['quantities']['heat_detectors'], 
                               f"${est['unit_prices']['heat_detectors']:.2f}", 
                               f"${est['quantities']['heat_detectors'] * est['unit_prices']['heat_detectors']:.2f}"])
                csv_data.append(["Pull Stations", est['quantities']['pull_stations'], 
                               f"${est['unit_prices']['pull_stations']:.2f}", 
                               f"${est['quantities']['pull_stations'] * est['unit_prices']['pull_stations']:.2f}"])
                csv_data.append(["Horn/Strobes", est['quantities']['horn_strobes'], 
                               f"${est['unit_prices']['horn_strobes']:.2f}", 
                               f"${est['quantities']['horn_strobes'] * est['unit_prices']['horn_strobes']:.2f}"])
                csv_data.append(["Control Panels", est['quantities']['control_panels'], 
                               f"${est['unit_prices']['control_panel']:.2f}", 
                               f"${est['quantities']['control_panels'] * est['unit_prices']['control_panel']:.2f}"])
                csv_data.append(["Sprinkler Heads", est['quantities']['sprinkler_heads'], 
                               f"${est['unit_prices']['sprinkler_heads']:.2f}", 
                               f"${est['quantities']['sprinkler_heads'] * est['unit_prices']['sprinkler_heads']:.2f}"])
                csv_data.append(["Wire (feet)", est['quantities']['wire_feet'], 
                               f"${est['unit_prices']['wire_per_foot']:.2f}", 
                               f"${est['quantities']['wire_feet'] * est['unit_prices']['wire_per_foot']:.2f}"])
                csv_data.append(["Conduit (feet)", est['quantities']['conduit_feet'], 
                               f"${est['unit_prices']['conduit_per_foot']:.2f}", 
                               f"${est['quantities']['conduit_feet'] * est['unit_prices']['conduit_per_foot']:.2f}"])
                
                csv_data.append([])
                csv_data.append(["MATERIAL SUBTOTAL", "", "", f"${est['costs']['material_cost']:.2f}"])
                csv_data.append([])
                
                # Labor Section
                csv_data.append(["LABOR"])
                csv_data.append(["Description", "Hours", "Rate", "Total"])
                csv_data.append(["Installation Labor", est['quantities']['labor_hours'], 
                               f"${est['unit_prices']['labor_rate']:.2f}/hr", 
                               f"${est['costs']['labor_cost']:.2f}"])
                csv_data.append([])
                csv_data.append(["LABOR SUBTOTAL", "", "", f"${est['costs']['labor_cost']:.2f}"])
                csv_data.append([])
                
                # Cost Summary
                csv_data.append(["COST SUMMARY"])
                csv_data.append(["Materials", "", "", f"${est['costs']['material_cost']:.2f}"])
                csv_data.append(["Labor", "", "", f"${est['costs']['labor_cost']:.2f}"])
                csv_data.append(["Subtotal", "", "", f"${est['costs']['subtotal']:.2f}"])
                csv_data.append([])
                csv_data.append([f"Overhead ({est['unit_prices']['overhead_percent']:.0f}%)", "", "", f"${est['costs']['overhead']:.2f}"])
                csv_data.append(["Total with Overhead", "", "", f"${est['costs']['total_with_overhead']:.2f}"])
                csv_data.append([])
                csv_data.append([f"Profit Margin ({est['unit_prices']['profit_percent']:.0f}%)", "", "", f"${est['costs']['profit']:.2f}"])
                csv_data.append([])
                csv_data.append(["FINAL ESTIMATE", "", "", f"${est['costs']['final_total']:.2f}"])
                
                # Convert to CSV string
                output = StringIO()
                writer = csv.writer(output)
                writer.writerows(csv_data)
                csv_string = output.getvalue()
                
                # Download button
                st.download_button(
                    label="📊 Download as CSV for Google Sheets",
                    data=csv_string,
                    file_name="fire_protection_estimate.csv",
                    mime="text/csv",
                    type="primary",
                    help="Download this CSV and import it into Google Sheets"
                )
                
                with st.expander("📖 How to Import into Google Sheets"):
                    st.markdown("""
**Step-by-step instructions:**

1. Click the button above to download the CSV file
2. Go to [Google Sheets](https://sheets.google.com)
3. Click **File** → **Import**
4. Click **Upload** tab
5. Drag the downloaded CSV file or click **Browse**
6. Choose **"Replace spreadsheet"** or **"Insert new sheet"**
7. Click **Import data**
8. Your estimate will appear in Google Sheets!
9. You can now edit, format, and share it

**Tips:**
- All cells are editable - adjust quantities and prices as needed
- Add your company logo and branding
- Share with your team or clients
- Export as PDF for final proposals
""")

else:
    st.warning("⚠️ Please enter your Anthropic API key in the sidebar to begin.")
    st.info("Don't have an API key? Get one at: https://console.anthropic.com/")

# Footer
st.markdown("---")
st.markdown("*Powered by Claude AI | Fire Protection Blueprint Analysis System*")