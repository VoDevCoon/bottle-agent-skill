import streamlit as st
import requests
from PIL import Image
import io
import zipfile

# --- CONFIGURATION ---
API_URL = "https://zxqyxpg2tv.ap-southeast-2.awsapprunner.com"

st.set_page_config(page_title="High-Res Image Factory", layout="wide")

st.title("High-Res (1200px) WebP Processor")
st.markdown("Upload images to convert them into **1200x1200px WebP** files with transparent backgrounds.")

# File Uploader
uploaded_files = st.file_uploader(
    "Drag & Drop your photos here", 
    type=['png', 'jpg', 'jpeg', 'webp'], 
    accept_multiple_files=True
)

if uploaded_files:
    if "zip_buffer" not in st.session_state:
        st.session_state.zip_buffer = None

    if st.button(f"Start Processing ({len(uploaded_files)} Images)"):
        
        # In-memory ZIP
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            st.write("---")
            st.subheader("Results Preview")
            cols = st.columns(4) 
            
            for i, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {i+1}/{len(uploaded_files)}: {uploaded_file.name}...")
                
                uploaded_file.seek(0)
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                try:
                    response = requests.post(f"{API_URL}/process-bottle/", files=files)
                    
                    if response.status_code == 200:
                        image_data = response.content
                        processed_image = Image.open(io.BytesIO(image_data))
                        
                        # CHANGE EXTENSION TO .webp
                        base_name = uploaded_file.name.rsplit('.', 1)[0]
                        new_filename = f"{base_name}.webp"
                        
                        # Add to ZIP
                        zip_file.writestr(new_filename, image_data)
                        
                        with cols[i % 4]:
                            st.image(processed_image, caption=f"✅ {new_filename}", use_container_width=True)
                    else:
                        st.error(f"Failed: {uploaded_file.name}")
                        
                except Exception as e:
                    st.error(f"Error on {uploaded_file.name}: {e}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.success("🎉 Done! Ready to download.")
        st.session_state.zip_buffer = zip_buffer.getvalue()

    if st.session_state.zip_buffer:
        st.download_button(
            label="⬇️ Download All (ZIP)",
            data=st.session_state.zip_buffer,
            file_name="processed_bottles_webp.zip",
            mime="application/zip",
            type="primary"
        )