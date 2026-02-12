import io
import gc
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
from rembg import remove, new_session
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# 1. Pre-load the "Lite" Model
model_session = new_session("u2netp")

app = FastAPI(title="Wine Bottle Processor API")

@app.get("/")
def home():
    return {"status": "healthy", "message": "Wine Bottle AI is running!"}

def aggressive_crop(pil_img, threshold=20):
    """
    Crops the image based on visible pixels only.
    """
    try:
        img_np = np.array(pil_img)
        alpha = img_np[:, :, 3]
        rows = np.any(alpha > threshold, axis=1)
        cols = np.any(alpha > threshold, axis=0)
        
        if not np.any(rows) or not np.any(cols):
            return pil_img
            
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        
        return pil_img.crop((xmin, ymin, xmax + 1, ymax + 1))
        
    except Exception as e:
        print(f"Aggressive crop failed: {e}")
        return pil_img

def straighten_bottle(pil_img):
    """
    Detects tilt and rotates the bottle to be vertical.
    """
    try:
        img_np = np.array(pil_img)
        alpha = img_np[:, :, 3]
        contours, _ = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return pil_img 
            
        largest_contour = max(contours, key=cv2.contourArea)
        center, (w, h), angle = cv2.minAreaRect(largest_contour)
        
        if w > h:
            angle = angle + 90
            
        if abs(angle) > 45:
            angle = 0
            
        return pil_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
        
    except Exception as e:
        print(f"Straightening failed: {e}")
        return pil_img

@app.post("/process-bottle/")
def process_bottle_endpoint(file: UploadFile = File(...)):
    
    # Read file
    input_bytes = file.file.read()
    
    # --- STEP 1: SAFETY RESIZE ---
    raw_img = Image.open(io.BytesIO(input_bytes)).convert("RGBA")
    
    # Resize heavily to prevent memory crashes
    MAX_HEIGHT = 800 
    if raw_img.height > MAX_HEIGHT:
        ratio = MAX_HEIGHT / raw_img.height
        new_w = int(raw_img.width * ratio)
        raw_img = raw_img.resize((new_w, MAX_HEIGHT), Image.Resampling.LANCZOS)
    
    # --- STEP 2: AI BACKGROUND REMOVAL ---
    subject_img = remove(raw_img, session=model_session)
    del raw_img
    gc.collect()
    
    # --- STEP 3: STRAIGHTEN & AGGRESSIVE CROP ---
    subject_img = straighten_bottle(subject_img)
    subject_img = aggressive_crop(subject_img)
    
    # --- STEP 4: COMPOSITING ---
    TARGET_WIDTH = 555
    TARGET_HEIGHT = 555
    SHADOW_OPACITY = 0.85
    SHADOW_BLUR_RADIUS = 15
    SHARPEN_FACTOR = 1.5

    # Smart Resize to Target Box
    max_w = TARGET_WIDTH - 80
    max_h = TARGET_HEIGHT - 120 
    
    width_ratio = max_w / subject_img.width
    height_ratio = max_h / subject_img.height
    scale_factor = min(width_ratio, height_ratio)
    
    new_w = int(subject_img.width * scale_factor)
    new_h = int(subject_img.height * scale_factor)
    
    subject_img = subject_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Sharpening
    enhancer = ImageEnhance.Sharpness(subject_img)
    subject_img = enhancer.enhance(SHARPEN_FACTOR)
    
    # Create Final Canvas
    final_canvas = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    
    # Create Shadow
    shadow_w = int(new_w * 1.2) 
    shadow_h = int(new_w * 0.25)
    
    shadow_layer = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow_layer)
    
    shadow_x1 = (TARGET_WIDTH - shadow_w) // 2
    floor_y = TARGET_HEIGHT - 50 
    shadow_y1 = floor_y - (shadow_h // 2)
    shadow_x2 = shadow_x1 + shadow_w
    shadow_y2 = shadow_y1 + shadow_h
    
    draw.ellipse((shadow_x1, shadow_y1, shadow_x2, shadow_y2), fill=(0, 0, 0, 255))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR_RADIUS))
    
    r, g, b, a = shadow_layer.split()
    a = a.point(lambda p: p * SHADOW_OPACITY)
    shadow_layer = Image.merge("RGBA", (r, g, b, a))
    
    # Final Paste (Centered)
    final_canvas.paste(shadow_layer, (0, 0), shadow_layer)
    bottle_x = (TARGET_WIDTH - new_w) // 2
    bottle_y = floor_y - new_h + 5
    final_canvas.paste(subject_img, (bottle_x, bottle_y), subject_img)

    # Output
    output_buffer = io.BytesIO()
    final_canvas.save(output_buffer, format="PNG")
    
    return Response(content=output_buffer.getvalue(), media_type="image/png")

# --- SELF-RUNNER BLOCK ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)