import streamlit as st
import requests
from PIL import Image
import io

# --- CONFIGURATION ---
# PASTE YOUR RENDER URL HERE (No trailing slash, no /docs)
API_URL = "https://bottle-processor.onrender.com" 

st.set_page_config(page_title="Wine Bottle Studio", page_icon="🍷")

# --- UI HEADER ---
st.title("🍷 Wine Bottle Studio")
st.markdown("""
Upload a raw photo of a wine bottle. 
This tool will **remove the background**, **fix the lighting**, 
and add a **perfect ground shadow**.
""")

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Choose a bottle photo...", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file is not None:
    # 1. Show the original image
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original")
        st.image(uploaded_file, use_container_width=True)

    # 2. Process Button
    with col2:
        st.subheader("Professional Result")
        process_btn = st.button("✨ Process Bottle", type="primary")

        if process_btn:
            with st.spinner("Processing... (This might take 30s if the server is waking up)"):
                try:
                    # Prepare the file for the API
                    files = {"file": uploaded_file.getvalue()}
                    
                    # Call your Render API
                    response = requests.post(f"{API_URL}/process-bottle/", files=files)
                    
                    if response.status_code == 200:
                        # Success!
                        result_image = Image.open(io.BytesIO(response.content))
                        st.image(result_image, use_container_width=True)
                        
                        # Download Button
                        st.download_button(
                            label="📥 Download Transparent PNG",
                            data=response.content,
                            file_name="processed_bottle.png",
                            mime="image/png"
                        )
                    else:
                        st.error(f"Error {response.status_code}: Something went wrong.")
                        st.write(response.text)
                        
                except Exception as e:
                    st.error(f"Connection Failed: {e}")
                    st.info("Tip: Make sure your Render API is running and the URL is correct.")

# --- SIDEBAR INSTRUCTIONS ---
with st.sidebar:
    st.header("Instructions")
    st.write("1. Take a photo of your bottle.")
    st.write("2. Upload it here.")
    st.write("3. Wait for the magic.")
    st.divider()
    st.caption("Powered by AI & Python")