import io
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import Response
from rembg import remove
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

app = FastAPI(title="Wine Bottle Processor API")

def process_image(input_bytes: bytes) -> bytes:
    # --- Configuration ---
    TARGET_WIDTH = 555
    TARGET_HEIGHT = 555
    SHADOW_OPACITY = 0.85    # 85% - Darker and more visible
    SHADOW_BLUR_RADIUS = 15  # Soft edges
    SHARPEN_FACTOR = 1.5     # Crisp details
    
    # 1. AI Background Removal
    subject_bytes = remove(input_bytes)
    subject_img = Image.open(io.BytesIO(subject_bytes)).convert("RGBA")
    
    # 2. Trim Empty Space
    bbox = subject_img.getbbox()
    if bbox:
        subject_img = subject_img.crop(bbox)
        
    # 3. Smart Resize
    # Padding: 40px top/sides, 100px bottom (extra room for shadow)
    max_w = TARGET_WIDTH - 80
    max_h = TARGET_HEIGHT - 120 
    
    # Calculate resize ratio
    width_ratio = max_w / subject_img.width
    height_ratio = max_h / subject_img.height
    scale_factor = min(width_ratio, height_ratio)
    
    new_w = int(subject_img.width * scale_factor)
    new_h = int(subject_img.height * scale_factor)
    
    # High-quality resize
    subject_img = subject_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # 4. Sharpening
    enhancer = ImageEnhance.Sharpness(subject_img)
    subject_img = enhancer.enhance(SHARPEN_FACTOR)
    
    # 5. Create Final Canvas
    final_canvas = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    
    # 6. Create the "Floor" Shadow
    # FIX: Shadow is now WIDER than the bottle (1.2x) so it peaks out
    shadow_w = int(new_w * 1.2) 
    shadow_h = int(new_w * 0.25) # Taller oval for more visibility
    
    shadow_layer = Image.new("RGBA", (TARGET_WIDTH, TARGET_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow_layer)
    
    # Center Shadow Horizontally
    shadow_x1 = (TARGET_WIDTH - shadow_w) // 2
    
    # Position Shadow Vertically
    # Place it near the bottom
    floor_y = TARGET_HEIGHT - 50 
    
    # We want the shadow oval to be centered *on* the floor line
    shadow_y1 = floor_y - (shadow_h // 2)
    shadow_x2 = shadow_x1 + shadow_w
    shadow_y2 = shadow_y1 + shadow_h
    
    # Draw Black Oval
    draw.ellipse((shadow_x1, shadow_y1, shadow_x2, shadow_y2), fill=(0, 0, 0, 255))
    
    # Blur
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR_RADIUS))
    
    # Opacity
    r, g, b, a = shadow_layer.split()
    a = a.point(lambda p: p * SHADOW_OPACITY)
    shadow_layer = Image.merge("RGBA", (r, g, b, a))
    
    # 7. Compose
    # Paste Shadow First
    final_canvas.paste(shadow_layer, (0, 0), shadow_layer)
    
    # Paste Bottle Second
    bottle_x = (TARGET_WIDTH - new_w) // 2
    # Align bottom of bottle exactly with the center of the shadow
    bottle_y = floor_y - new_h + 5  # +5 pushes bottle slightly "into" the shadow for realism
    
    final_canvas.paste(subject_img, (bottle_x, bottle_y), subject_img)

    # 8. Output
    output_buffer = io.BytesIO()
    final_canvas.save(output_buffer, format="PNG")
    return output_buffer.getvalue()

@app.post("/process-bottle/")
async def process_bottle_endpoint(file: UploadFile = File(...)):
    input_bytes = await file.read()
    output_bytes = process_image(input_bytes)
    return Response(content=output_bytes, media_type="image/png")