from memory_profiler import profile
import io
import gc
import cv2
import numpy as np
from rembg import remove, new_session
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# Load model
session = new_session("u2netp")

# --- HELPER FUNCTIONS ---
def aggressive_crop(pil_img, threshold=20):
    try:
        img_np = np.array(pil_img)
        alpha = img_np[:, :, 3]
        rows = np.any(alpha > threshold, axis=1)
        cols = np.any(alpha > threshold, axis=0)
        if not np.any(rows) or not np.any(cols): return pil_img
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        return pil_img.crop((xmin, ymin, xmax + 1, ymax + 1))
    except: return pil_img

def straighten_bottle(pil_img):
    try:
        img_np = np.array(pil_img)
        alpha = img_np[:, :, 3]
        contours, _ = cv2.findContours(alpha, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours: return pil_img 
        largest_contour = max(contours, key=cv2.contourArea)
        center, (w, h), angle = cv2.minAreaRect(largest_contour)
        if w > h: angle = angle + 90
        if abs(angle) > 45: angle = 0
        return pil_img.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    except: return pil_img

# --- THE TEST FUNCTION ---
@profile
def run_benchmark():
    print("--- STARTING HIGH-RES (1200px) MEMORY TEST ---")
    
    # REPLACE THIS WITH YOUR IMAGE NAME
    filename = "test111.png" 
    
    try:
        with open(filename, "rb") as f:
            input_bytes = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Could not find '{filename}'. Please make sure an image file is in this folder.")
        return

    # 1. HIGH-RES INPUT RESIZE (1600px)
    print("1. Opening & Resizing (Target: 1600px)...")
    raw_img = Image.open(io.BytesIO(input_bytes)).convert("RGBA")
    MAX_INPUT_HEIGHT = 1600 
    if raw_img.height > MAX_INPUT_HEIGHT:
        ratio = MAX_INPUT_HEIGHT / raw_img.height
        new_w = int(raw_img.width * ratio)
        raw_img = raw_img.resize((new_w, MAX_INPUT_HEIGHT), Image.Resampling.LANCZOS)
    
    # 2. AI PROCESSING
    print("2. Running AI (Heavier now due to size)...")
    subject_img = remove(raw_img, session=session)
    del raw_img
    gc.collect() 
    
    # 3. POLISH
    print("3. Straightening & Cropping...")
    subject_img = straighten_bottle(subject_img)
    subject_img = aggressive_crop(subject_img)
    
    # 4. COMPOSITING (1200x1200px)
    print("4. Creating 1200px Canvas & Shadows...")
    TARGET_WIDTH = 1200
    TARGET_HEIGHT = 1200
    SHADOW_OPACITY = 0.85
    SHADOW_BLUR_RADIUS = 30  # Increased for Hi-Res
    SHARPEN_FACTOR = 1.3

    max_w = TARGET_WIDTH - 200
    max_h = TARGET_HEIGHT - 250 
    width_ratio = max_w / subject_img.width
    height_ratio = max_h / subject_img.height
    scale_factor = min(width_ratio, height_ratio)
    new_w = int(subject_img.width * scale_factor)
    new_h = int(subject_img.height * scale_factor)
    subject_img = subject_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Sharpness(subject_img)
    subject_img = enhancer.enhance(SHARPEN_FACTOR)
    
    final_canvas = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    shadow_w = int(new_w * 1.2) 
    shadow_h = int(new_w * 0.25)
    shadow_layer = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow_layer)
    shadow_x1 = (TARGET_WIDTH - shadow_w) // 2
    floor_y = TARGET_HEIGHT - 100 
    shadow_y1 = floor_y - (shadow_h // 2)
    shadow_x2 = shadow_x1 + shadow_w
    shadow_y2 = shadow_y1 + shadow_h
    draw.ellipse((shadow_x1, shadow_y1, shadow_x2, shadow_y2), fill=(0, 0, 0, 255))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR_RADIUS))
    r, g, b, a = shadow_layer.split()
    a = a.point(lambda p: p * SHADOW_OPACITY)
    shadow_layer = Image.merge("RGBA", (r, g, b, a))
    final_canvas.paste(shadow_layer, (0, 0), shadow_layer)
    bottle_x = (TARGET_WIDTH - new_w) // 2
    bottle_y = floor_y - new_h + 10
    final_canvas.paste(subject_img, (bottle_x, bottle_y), subject_img)

    # 5. SAVING AS WEBP
    print("5. Saving as WebP...")
    output_buffer = io.BytesIO()
    final_canvas.save(output_buffer, format="WEBP", quality=95, method=6)
    
    print(f"--- DONE! Output size: {len(output_buffer.getvalue())/1024:.1f} KB ---")

if __name__ == "__main__":
    run_benchmark()