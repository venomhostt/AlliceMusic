import os
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760
BG_BLUR = 16
BG_BRIGHTNESS = 1  

LIME_BORDER = (158, 255, 49, 255)
RING_COLOR  = (98, 193, 169, 255)
TEXT_WHITE  = (245, 245, 245, 255)
TEXT_SOFT   = (230, 230, 230, 255)
TEXT_SHADOW = (0, 0, 0, 140)

FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH    = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB    = "ShrutixMusic/assets/temp_thumb.jpg"

def change_image_size(max_w, max_h, image):
    try:
        ratio = min(max_w / image.size[0], max_h / image.size[1])
        return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)
    except Exception as e:
        print(f"[change_image_size Error] {e}")
        return image

def wrap_two_lines(draw, text, font, max_width):
    try:
        words = text.split()
        line1, line2 = "", ""
        for w in words:
            test = (line1 + " " + w).strip()
            if draw.textlength(test, font=font) <= max_width:
                line1 = test
            else:
                break
        remaining = text[len(line1):].strip()
        if remaining:
            for w in remaining.split():
                test = (line2 + " " + w).strip()
                if draw.textlength(test, font=font) <= max_width:
                    line2 = test
                else:
                    break
        return (line1 + ("\n" + line2 if line2 else "")).strip()
    except Exception as e:
        print(f"[wrap_two_lines Error] {e}")
        return text[:50]

def fit_title_two_lines(draw, text, max_width, font_path, start_size=58, min_size=30):
    try:
        size = start_size
        while size >= min_size:
            try:
                f = ImageFont.truetype(font_path, size)
            except:
                size -= 1
                continue
            wrapped = wrap_two_lines(draw, text, f, max_width)
            lines = wrapped.split("\n")
            if len(lines) <= 2 and all(draw.textlength(l, font=f) <= max_width for l in lines):
                return f, wrapped
            size -= 1
        f = ImageFont.truetype(font_path, min_size)
        return f, wrap_two_lines(draw, text, f, max_width)
    except Exception as e:
        print(f"[fit_title_two_lines Error] {e}")
        try:
            f = ImageFont.truetype(font_path, min_size)
            return f, text[:50]
        except:
            return ImageFont.load_default(), text[:50]

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title    = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views    = result.get("viewCount", {}).get("short", "Unknown Views")
        channel  = result.get("channel", {}).get("name", "Unknown Channel")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Background
        bg = change_image_size(CANVAS_W, CANVAS_H, base_img).convert("RGBA")
        bg = bg.filter(ImageFilter.GaussianBlur(BG_BLUR))
        bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHTNESS)

        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        canvas.paste(bg, (0, 0))
        draw = ImageDraw.Draw(canvas)

        # outer lime frame
        frame_inset = 12
        draw.rectangle(
            [frame_inset//2, frame_inset//2, CANVAS_W - frame_inset//2, CANVAS_H - frame_inset//2],
            outline=LIME_BORDER, width=frame_inset
        )

        thumb_size = 470
        ring_width = 20
        circle_x = 92
        circle_y = (CANVAS_H - thumb_size) // 2

        circular_mask = Image.new("L", (thumb_size, thumb_size), 0)
        mdraw = ImageDraw.Draw(circular_mask)
        mdraw.ellipse((0, 0, thumb_size, thumb_size), fill=255)

        art = base_img.resize((thumb_size, thumb_size))
        art.putalpha(circular_mask)

        ring_size = thumb_size + ring_width * 2
        ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(ring_img)
        ring_bbox = (ring_width//2, ring_width//2, ring_size - ring_width//2, ring_size - ring_width//2)
        rdraw.ellipse(ring_bbox, outline=RING_COLOR, width=ring_width)

        canvas.paste(ring_img, (circle_x - ring_width, circle_y - ring_width), ring_img)
        canvas.paste(art, (circle_x, circle_y), art)

        try:
            tl_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
        except:
            tl_font = ImageFont.load_default()
        
        draw.text((28+1, 18+1), "AlliceMusicBot", fill=TEXT_SHADOW, font=tl_font)
        draw.text((28, 18), "AlliceMusicBot", fill=TEXT_WHITE, font=tl_font)

        info_x = circle_x + thumb_size + 60
        max_text_w = CANVAS_W - info_x - 48

        try:
            np_font = ImageFont.truetype(FONT_BOLD_PATH, 60)
        except:
            np_font = ImageFont.load_default()
        
        np_text = "NOW PLAYING"
        np_w = draw.textlength(np_text, font=np_font)
        np_x = info_x + (max_text_w - np_w) // 2 - 95
        np_y = circle_y + 30  
        draw.text((np_x+2, np_y+2), np_text, fill=TEXT_SHADOW, font=np_font)
        draw.text((np_x, np_y), np_text, fill=TEXT_WHITE, font=np_font)

        title_font, title_wrapped = fit_title_two_lines(draw, title, max_text_w, FONT_BOLD_PATH, start_size=30, min_size=30)
        title_y = np_y + 110   
        draw.multiline_text((info_x+2, title_y+2), title_wrapped, fill=TEXT_SHADOW, font=title_font, spacing=8)
        draw.multiline_text((info_x, title_y), title_wrapped, fill=TEXT_WHITE, font=title_font, spacing=8)

        try:
            meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        except:
            meta_font = ImageFont.load_default()
        
        line_gap = 46
        meta_start_y = title_y + 130  
        duration_label = duration
        if duration and ":" in duration and "Min" not in duration and "min" not in duration:
            duration_label = f"{duration} Mins"

        def draw_meta(y, text):
            draw.text((info_x+1, y+1), text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x, y), text, fill=TEXT_SOFT, font=meta_font)

        draw_meta(meta_start_y + 0 * line_gap, f"Views : {views}")
        draw_meta(meta_start_y + 1 * line_gap, f"Duration : {duration_label}")
        draw_meta(meta_start_y + 2 * line_gap, f"Channel : {channel}")

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out)

        # Clean up downloaded thumbnail
        try:
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as cleanup_error:
            print(f"[Cleanup Error] {cleanup_error}")

        return str(out)

    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback: Return the default thumbnail
        try:
            if os.path.exists(FALLBACK_THUMB):
                print(f"[Fallback] Returning default thumbnail: {FALLBACK_THUMB}")
                return FALLBACK_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {FALLBACK_THUMB}")
                return None
        except Exception as fallback_error:
            print(f"[Fallback Error] {fallback_error}")
            return None
        finally:
            # Clean up any partial downloads
            try:
                if thumb_path and os.path.exists(thumb_path):
                    os.remove(thumb_path)
            except:
                pass

    return None        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        canvas.paste(bg, (0, 0))
        draw = ImageDraw.Draw(canvas)

        draw.rectangle(
            [10, 10, CANVAS_W - 10, CANVAS_H - 10],
            outline=(0, 255, 163, 255), width=8
        )

        thumb_size = 400
        circle_x = 80
        circle_y = (CANVAS_H - thumb_size) // 2

        mask = Image.new("L", (thumb_size, thumb_size), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.ellipse((0, 0, thumb_size, thumb_size), fill=255)

        art = base_img.resize((thumb_size, thumb_size))
        art.putalpha(mask)

        ring_size = thumb_size + 30
        ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(ring_img)
        rdraw.ellipse((15, 15, ring_size - 15, ring_size - 15), outline=(0, 255, 163, 255), width=15)

        canvas.paste(ring_img, (circle_x - 15, circle_y - 15), ring_img)
        canvas.paste(art, (circle_x, circle_y), art)

        try:
            tl_font = ImageFont.truetype(FONT_PATH, 40)
        except:
            tl_font = ImageFont.load_default()
        
        draw.text((30, 30), "♫ MUSIC BOT", fill=(255, 255, 255, 255), font=tl_font)

        info_x = circle_x + thumb_size + 60
        max_text_w = CANVAS_W - info_x - 40

        try:
            np_font = ImageFont.truetype(FONT_PATH, 65)
        except:
            np_font = ImageFont.load_default()
        
        draw.text((info_x, 80), "NOW PLAYING", fill=(255, 255, 255, 255), font=np_font)

        draw.line([(info_x, 160), (info_x + max_text_w, 160)], fill=(0, 255, 163, 255), width=4)

        try:
            title_font = ImageFont.truetype(FONT_PATH, 45)
        except:
            title_font = ImageFont.load_default()
        
        words = title.split()
        line1 = ""
        line2 = ""
        
        for w in words:
            test = (line1 + " " + w).strip()
            if draw.textlength(test, font=title_font) <= max_text_w:
                line1 = test
            else:
                break
        
        remaining = title[len(line1):].strip()
        if remaining:
            for w in remaining.split():
                test = (line2 + " " + w).strip()
                if draw.textlength(test, font=title_font) <= max_text_w:
                    line2 = test
                else:
                    break
        
        title_text = (line1 + ("\n" + line2 if line2 else "")).strip()
        
        draw.multiline_text((info_x, 190), title_text, fill=(255, 255, 255, 255), font=title_font, spacing=10)

        try:
            meta_font = ImageFont.truetype(FONT_PATH, 30)
        except:
            meta_font = ImageFont.load_default()
        
        draw.text((info_x, 320), f"👁️ {views}", fill=(200, 200, 200, 255), font=meta_font)
        draw.text((info_x, 370), f"⏱️ {duration}", fill=(200, 200, 200, 255), font=meta_font)
        draw.text((info_x, 420), f"📺 {channel}", fill=(200, 200, 200, 255), font=meta_font)

        for i in range(0, CANVAS_W, 40):
            draw.line([(i, 0), (i, CANVAS_H)], fill=(255, 255, 255, 10), width=1)
        
        for i in range(0, CANVAS_H, 40):
            draw.line([(0, i), (CANVAS_W, i)], fill=(255, 255, 255, 10), width=1)

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95)

        if thumb_path and os.path.exists(thumb_path):
            os.remove(thumb_path)

        return str(out)

    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        if os.path.exists(FALLBACK_THUMB):
            return FALLBACK_THUMB
        
        return Nonewith_shadow(draw, position, text, font, main_color, shadow_color, shadow_offset=(3, 3)):
    """Draw text with shadow effect"""
    x, y = position
    sx, sy = shadow_offset
    
    for dx, dy in [(sx, sy), (sx-1, sy), (sx, sy-1), (sx+1, sy), (sx, sy+1)]:
        draw.text((x+dx, y+dy), text, font=font, fill=shadow_color)
    
    draw.text((x, y), text, font=font, fill=main_color)

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text to fit within max_width and max_lines"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if draw.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            
            if len(lines) >= max_lines:
                last_line = lines[-1]
                while draw.textlength(last_line + "...", font=font) > max_width and last_line:
                    last_line = last_line[:-1]
                lines[-1] = last_line + "..."
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def create_circular_image(image, size):
    """Create circular image with smooth edges"""
    mask = Image.new('L', (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * 2, size * 2), fill=255)
    
    mask = mask.resize((size, size), Image.LANCZOS)
    output = Image.new('RGBA', (size, size))
    output.paste(image.resize((size, size)), (0, 0), mask)
    return output

def add_pulse_ring(draw, center, size, color, width=5, segments=12):
    """Add animated-style pulse rings"""
    x, y = center
    for i in range(3):
        radius = size + (i * 20)
        alpha = 100 - (i * 30)
        segment_length = math.pi * 2 / segments
        
        for s in range(segments):
            if s % 2 == 0:
                start_angle = s * segment_length
                end_angle = start_angle + segment_length * 0.7
                
                draw.arc(
                    [x - radius, y - radius, x + radius, y + radius],
                    math.degrees(start_angle),
                    math.degrees(end_angle),
                    (*color[:3], alpha),
                    width
                )

def draw_rounded_rectangle(draw, xy, radius, **kwargs):
    """Draw rounded rectangle"""
    x1, y1, x2, y2 = xy
    fill_color = kwargs.get('fill')
    
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill_color)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill_color)
    
    for x, y in [(x1 + radius, y1 + radius), (x2 - radius, y1 + radius),
                 (x1 + radius, y2 - radius), (x2 - radius, y2 - radius)]:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill_color)

def change_image_size(max_w, max_h, image):
    """Resize image while maintaining aspect ratio"""
    try:
        ratio = min(max_w / image.size[0], max_h / image.size[1])
        return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)
    except Exception as e:
        print(f"[change_image_size Error] {e}")
        return image

def wrap_two_lines(draw, text, font, max_width):
    """Wrap text to two lines"""
    try:
        words = text.split()
        line1, line2 = "", ""
        for w in words:
            test = (line1 + " " + w).strip()
            if draw.textlength(test, font=font) <= max_width:
                line1 = test
            else:
                break
        remaining = text[len(line1):].strip()
        if remaining:
            for w in remaining.split():
                test = (line2 + " " + w).strip()
                if draw.textlength(test, font=font) <= max_width:
                    line2 = test
                else:
                    break
        return (line1 + ("\n" + line2 if line2 else "")).strip()
    except Exception as e:
        print(f"[wrap_two_lines Error] {e}")
        return text[:50]

def fit_title_two_lines(draw, text, max_width, font_path, start_size=58, min_size=30):
    """Fit title text to two lines with appropriate font size"""
    try:
        size = start_size
        while size >= min_size:
            try:
                f = ImageFont.truetype(font_path, size)
            except:
                size -= 1
                continue
            wrapped = wrap_two_lines(draw, text, f, max_width)
            lines = wrapped.split("\n")
            if len(lines) <= 2 and all(draw.textlength(l, font=f) <= max_width for l in lines):
                return f, wrapped
            size -= 1
        f = ImageFont.truetype(font_path, min_size)
        return f, wrap_two_lines(draw, text, f, max_width)
    except Exception as e:
        print(f"[fit_title_two_lines Error] {e}")
        try:
            f = ImageFont.truetype(font_path, min_size)
            return f, text[:50]
        except:
            return ImageFont.load_default(), text[:50]

async def get_thumb(videoid: str):
    """Generate attractive thumbnail for YouTube video"""
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Search for video information
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Create gradient background
        canvas = create_gradient((CANVAS_W, CANVAS_H), GRADIENT_START, GRADIENT_END)
        draw = ImageDraw.Draw(canvas)

        # Add subtle noise texture
        noise_img = create_noise_texture((CANVAS_W, CANVAS_H), intensity=15)
        canvas = Image.alpha_composite(canvas, noise_img)

        # Process and add blurred background image
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(BG_BLUR))
        bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHTNESS)
        bg.putalpha(80)
        
        # Apply gradient overlay to background
        gradient_overlay = create_gradient((CANVAS_W, CANVAS_H), (0, 0, 0, 180), (0, 0, 0, 80))
        bg = Image.alpha_composite(bg, gradient_overlay)
        
        # Composite background
        canvas = Image.alpha_composite(canvas, bg)

        # Add vibrant border
        canvas = create_vibrant_border(canvas, LIME_BORDER, border_width=8, glow=True)

        # Thumbnail setup
        thumb_size = 520
        circle_x = 120
        circle_y = (CANVAS_H - thumb_size) // 2

        # Create circular thumbnail with border
        circular_thumb = create_circular_image(base_img, thumb_size)
        
        # Add glow to thumbnail
        thumb_glow = Image.new('RGBA', (thumb_size + 40, thumb_size + 40), (0, 0, 0, 0))
        thumb_glow_draw = ImageDraw.Draw(thumb_glow)
        thumb_glow_draw.ellipse(
            [20, 20, thumb_size + 20, thumb_size + 20],
            outline=GLOW_COLOR,
            width=15
        )
        thumb_glow = thumb_glow.filter(ImageFilter.GaussianBlur(10))
        
        # Composite thumbnail with glow
        canvas.paste(thumb_glow, (circle_x - 20, circle_y - 20), thumb_glow)
        canvas.paste(circular_thumb, (circle_x, circle_y), circular_thumb)

        # Add pulse rings around thumbnail
        add_pulse_ring(draw, (circle_x + thumb_size//2, circle_y + thumb_size//2), 
                      thumb_size//2, GLOW_COLOR, width=3)

        # Modern header with logo/text
        try:
            header_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        except:
            header_font = ImageFont.load_default()
            
        logo_text = "♫ ALLICE MUSIC"
        
        # Create logo background
        logo_bg = Image.new('RGBA', (400, 60), (0, 0, 0, 0))
        logo_draw = ImageDraw.Draw(logo_bg)
        
        draw_rounded_rectangle(logo_draw, [0, 0, 400, 60], 30, fill=(0, 0, 0, 150))
        
        canvas.paste(logo_bg, (40, 40), logo_bg)
        draw_text_with_shadow(draw, (60, 52), logo_text, header_font, 
                            TEXT_NEON, TEXT_SHADOW, shadow_offset=(2, 2))

        # NOW PLAYING with modern styling
        info_x = circle_x + thumb_size + 80
        max_text_w = CANVAS_W - info_x - 60
        
        try:
            np_font = ImageFont.truetype(FONT_BOLD_PATH, 68)
        except:
            np_font = ImageFont.load_default()
            
        np_text = "NOW PLAYING"
        
        # Animated-style underline for NOW PLAYING
        underline_y = 220
        draw.line([(info_x, underline_y), (info_x + max_text_w, underline_y)], 
                 fill=TEXT_NEON, width=3)
        
        # Dotted line effect
        for i in range(0, int(max_text_w), 15):
            if i % 30 == 0:
                draw.line([(info_x + i, underline_y), (info_x + i + 8, underline_y)], 
                         fill=TEXT_NEON, width=3)
        
        draw_text_with_shadow(draw, (info_x, 140), np_text, np_font, 
                            TEXT_WHITE, TEXT_SHADOW, shadow_offset=(3, 3))

        # Title with modern wrapping
        try:
            title_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
        except:
            title_font = ImageFont.load_default()
            
        wrapped_title = wrap_text(draw, title, title_font, max_text_w)
        
        title_y = 250
        draw.multiline_text((info_x + 2, title_y + 2), wrapped_title, 
                          fill=TEXT_SHADOW, font=title_font, spacing=8)
        draw.multiline_text((info_x, title_y), wrapped_title, 
                          fill=TEXT_WHITE, font=title_font, spacing=8)

        # Metadata with icons
        meta_start_y = title_y + 180
        
        try:
            meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 32)
            icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 36)
        except:
            meta_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()
            
        line_gap = 50
        
        # Draw metadata with icons
        metadata = [
            ("👁️", f"{views}"),
            ("⏱️", f"{duration}"),
            ("📺", f"{channel}")
        ]
        
        for i, (icon, text) in enumerate(metadata):
            y_pos = meta_start_y + (i * line_gap)
            
            # Icon
            draw.text((info_x + 2, y_pos + 2), icon, fill=TEXT_SHADOW, font=icon_font)
            draw.text((info_x, y_pos), icon, fill=TEXT_NEON, font=icon_font)
            
            # Text
            meta_text = f"  {text}"
            draw.text((info_x + 40 + 2, y_pos + 2), meta_text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x + 40, y_pos), meta_text, fill=TEXT_SOFT, font=meta_font)

        # Add decorative elements
        # Top-right corner accent
        accent_size = 200
        accent = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent)
        accent_draw.pieslice([0, 0, accent_size*2, accent_size*2], 0, 90, 
                           fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent, (CANVAS_W - accent_size, 0), accent)

        # Bottom-left corner accent
        accent2 = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent2_draw = ImageDraw.Draw(accent2)
        accent2_draw.pieslice([-accent_size, -accent_size, accent_size, accent_size], 
                            180, 270, fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent2, (0, CANVAS_H - accent_size), accent2)

        # Add subtle grid lines
        grid_alpha = 20
        for i in range(0, CANVAS_W, 50):
            draw.line([(i, 0), (i, CANVAS_H)], fill=(255, 255, 255, grid_alpha), width=1)
        for i in range(0, CANVAS_H, 50):
            draw.line([(0, i), (CANVAS_W, i)], fill=(255, 255, 255, grid_alpha), width=1)

        # Add final glow effect to entire image
        canvas = add_glow_effect(canvas, (0, 0, 0, 30), radius=2)

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95)

        # Clean up downloaded thumbnail
        try:
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as cleanup_error:
            print(f"[Cleanup Error] {cleanup_error}")

        return str(out)

    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback: Return the default thumbnail
        try:
            if os.path.exists(FALLBACK_THUMB):
                print(f"[Fallback] Returning default thumbnail: {FALLBACK_THUMB}")
                return FALLBACK_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {FALLBACK_THUMB}")
                return None
        except Exception as fallback_error:
            print(f"[Fallback Error] {fallback_error}")
            return None
        finally:
            # Clean up any partial downloads
            try:
                if thumb_path and os.path.exists(thumb_path):
                    os.remove(thumb_path)
            except:
                pass

    return None    
    mask = Image.new('L', size)
    mask_data = []
    
    if direction == 'diagonal':
        for y in range(size[1]):
            for x in range(size[0]):
                value = int(255 * (x + y) / (size[0] + size[1]))
                mask_data.append(value)
    else:
        for y in range(size[1]):
            value = int(255 * y / size[1])
            for x in range(size[0]):
                mask_data.append(value)
    
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def create_noise_texture(size, intensity=10):
    """Create noise texture"""
    noise_img = Image.new('RGBA', size, (0, 0, 0, 0))
    noise_draw = ImageDraw.Draw(noise_img)
    
    for y in range(0, size[1], 2):
        for x in range(0, size[0], 2):
            if random.random() > 0.7:
                gray = random.randint(0, intensity)
                noise_draw.point((x, y), (gray, gray, gray, 5))
    
    return noise_img

def add_glow_effect(image, glow_color, radius=20):
    """Add glow effect to image"""
    glow = image.filter(ImageFilter.GaussianBlur(radius))
    glow = ImageChops.multiply(glow, Image.new('RGBA', glow.size, glow_color))
    return Image.alpha_composite(glow, image)

def create_vibrant_border(image, border_color, border_width=10, glow=True):
    """Create a vibrant border with optional glow"""
    border_img = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    
    for i in range(border_width):
        alpha = 255 - (i * 255 // border_width)
        color = (*border_color[:3], alpha)
        draw.rectangle(
            [i, i, image.size[0]-i, image.size[1]-i],
            outline=color,
            width=1
        )
    
    if glow:
        border_img = border_img.filter(ImageFilter.GaussianBlur(3))
    
    return Image.alpha_composite(image, border_img)

def draw_text_with_shadow(draw, position, text, font, main_color, shadow_color, shadow_offset=(3, 3)):
    """Draw text with shadow effect"""
    x, y = position
    sx, sy = shadow_offset
    
    for dx, dy in [(sx, sy), (sx-1, sy), (sx, sy-1), (sx+1, sy), (sx, sy+1)]:
        draw.text((x+dx, y+dy), text, font=font, fill=shadow_color)
    
    draw.text((x, y), text, font=font, fill=main_color)

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text to fit within max_width and max_lines"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if draw.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            
            if len(lines) >= max_lines:
                last_line = lines[-1]
                while draw.textlength(last_line + "...", font=font) > max_width and last_line:
                    last_line = last_line[:-1]
                lines[-1] = last_line + "..."
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def create_circular_image(image, size):
    """Create circular image with smooth edges"""
    mask = Image.new('L', (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * 2, size * 2), fill=255)
    
    mask = mask.resize((size, size), Image.LANCZOS)
    output = Image.new('RGBA', (size, size))
    output.paste(image.resize((size, size)), (0, 0), mask)
    return output

def add_pulse_ring(draw, center, size, color, width=5, segments=12):
    """Add animated-style pulse rings"""
    x, y = center
    for i in range(3):
        radius = size + (i * 20)
        alpha = 100 - (i * 30)
        segment_length = math.pi * 2 / segments
        
        for s in range(segments):
            if s % 2 == 0:
                start_angle = s * segment_length
                end_angle = start_angle + segment_length * 0.7
                
                draw.arc(
                    [x - radius, y - radius, x + radius, y + radius],
                    math.degrees(start_angle),
                    math.degrees(end_angle),
                    (*color[:3], alpha),
                    width
                )

def draw_rounded_rectangle(draw, xy, radius, **kwargs):
    """Draw rounded rectangle"""
    x1, y1, x2, y2 = xy
    fill_color = kwargs.get('fill')
    
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill_color)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill_color)
    
    for x, y in [(x1 + radius, y1 + radius), (x2 - radius, y1 + radius),
                 (x1 + radius, y2 - radius), (x2 - radius, y2 - radius)]:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill_color)

def change_image_size(max_w, max_h, image):
    """Resize image while maintaining aspect ratio"""
    try:
        ratio = min(max_w / image.size[0], max_h / image.size[1])
        return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)
    except Exception as e:
        print(f"[change_image_size Error] {e}")
        return image

def wrap_two_lines(draw, text, font, max_width):
    """Wrap text to two lines"""
    try:
        words = text.split()
        line1, line2 = "", ""
        for w in words:
            test = (line1 + " " + w).strip()
            if draw.textlength(test, font=font) <= max_width:
                line1 = test
            else:
                break
        remaining = text[len(line1):].strip()
        if remaining:
            for w in remaining.split():
                test = (line2 + " " + w).strip()
                if draw.textlength(test, font=font) <= max_width:
                    line2 = test
                else:
                    break
        return (line1 + ("\n" + line2 if line2 else "")).strip()
    except Exception as e:
        print(f"[wrap_two_lines Error] {e}")
        return text[:50]

def fit_title_two_lines(draw, text, max_width, font_path, start_size=58, min_size=30):
    """Fit title text to two lines with appropriate font size"""
    try:
        size = start_size
        while size >= min_size:
            try:
                f = ImageFont.truetype(font_path, size)
            except:
                size -= 1
                continue
            wrapped = wrap_two_lines(draw, text, f, max_width)
            lines = wrapped.split("\n")
            if len(lines) <= 2 and all(draw.textlength(l, font=f) <= max_width for l in lines):
                return f, wrapped
            size -= 1
        f = ImageFont.truetype(font_path, min_size)
        return f, wrap_two_lines(draw, text, f, max_width)
    except Exception as e:
        print(f"[fit_title_two_lines Error] {e}")
        try:
            f = ImageFont.truetype(font_path, min_size)
            return f, text[:50]
        except:
            return ImageFont.load_default(), text[:50]

async def get_thumb(videoid: str):
    """Generate attractive thumbnail for YouTube video"""
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Create gradient background
        canvas = create_gradient((CANVAS_W, CANVAS_H), GRADIENT_START, GRADIENT_END)
        draw = ImageDraw.Draw(canvas)

        # Add subtle noise texture
        noise_img = create_noise_texture((CANVAS_W, CANVAS_H), intensity=15)
        canvas = Image.alpha_composite(canvas, noise_img)

        # Process and add blurred background image
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(BG_BLUR))
        bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHTNESS)
        bg.putalpha(80)
        
        # Apply gradient overlay to background
        gradient_overlay = create_gradient((CANVAS_W, CANVAS_H), (0, 0, 0, 180), (0, 0, 0, 80))
        bg = Image.alpha_composite(bg, gradient_overlay)
        
        # Composite background
        canvas = Image.alpha_composite(canvas, bg)

        # Add vibrant border
        canvas = create_vibrant_border(canvas, LIME_BORDER, border_width=8, glow=True)

        # Thumbnail setup
        thumb_size = 520
        circle_x = 120
        circle_y = (CANVAS_H - thumb_size) // 2

        # Create circular thumbnail with border
        circular_thumb = create_circular_image(base_img, thumb_size)
        
        # Add glow to thumbnail
        thumb_glow = Image.new('RGBA', (thumb_size + 40, thumb_size + 40), (0, 0, 0, 0))
        thumb_glow_draw = ImageDraw.Draw(thumb_glow)
        thumb_glow_draw.ellipse(
            [20, 20, thumb_size + 20, thumb_size + 20],
            outline=GLOW_COLOR,
            width=15
        )
        thumb_glow = thumb_glow.filter(ImageFilter.GaussianBlur(10))
        
        # Composite thumbnail with glow
        canvas.paste(thumb_glow, (circle_x - 20, circle_y - 20), thumb_glow)
        canvas.paste(circular_thumb, (circle_x, circle_y), circular_thumb)

        # Add pulse rings around thumbnail
        add_pulse_ring(draw, (circle_x + thumb_size//2, circle_y + thumb_size//2), 
                      thumb_size//2, GLOW_COLOR, width=3)

        # Modern header with logo/text
        try:
            header_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        except:
            header_font = ImageFont.load_default()
            
        logo_text = "♫ ALLICE MUSIC"
        
        # Create logo background
        logo_bg = Image.new('RGBA', (400, 60), (0, 0, 0, 0))
        logo_draw = ImageDraw.Draw(logo_bg)
        
        draw_rounded_rectangle(logo_draw, [0, 0, 400, 60], 30, fill=(0, 0, 0, 150))
        
        canvas.paste(logo_bg, (40, 40), logo_bg)
        draw_text_with_shadow(draw, (60, 52), logo_text, header_font, 
                            TEXT_NEON, TEXT_SHADOW, shadow_offset=(2, 2))

        # NOW PLAYING with modern styling
        info_x = circle_x + thumb_size + 80
        max_text_w = CANVAS_W - info_x - 60
        
        try:
            np_font = ImageFont.truetype(FONT_BOLD_PATH, 68)
        except:
            np_font = ImageFont.load_default()
            
        np_text = "NOW PLAYING"
        
        # Animated-style underline for NOW PLAYING
        underline_y = 220
        draw.line([(info_x, underline_y), (info_x + max_text_w, underline_y)], 
                 fill=TEXT_NEON, width=3)
        
        # Dotted line effect
        for i in range(0, int(max_text_w), 15):
            if i % 30 == 0:
                draw.line([(info_x + i, underline_y), (info_x + i + 8, underline_y)], 
                         fill=TEXT_NEON, width=3)
        
        draw_text_with_shadow(draw, (info_x, 140), np_text, np_font, 
                            TEXT_WHITE, TEXT_SHADOW, shadow_offset=(3, 3))

        # Title with modern wrapping
        try:
            title_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
        except:
            title_font = ImageFont.load_default()
            
        wrapped_title = wrap_text(draw, title, title_font, max_text_w)
        
        title_y = 250
        draw.multiline_text((info_x + 2, title_y + 2), wrapped_title, 
                          fill=TEXT_SHADOW, font=title_font, spacing=8)
        draw.multiline_text((info_x, title_y), wrapped_title, 
                          fill=TEXT_WHITE, font=title_font, spacing=8)

        # Metadata with icons
        meta_start_y = title_y + 180
        
        try:
            meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 32)
            icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 36)
        except:
            meta_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()
            
        line_gap = 50
        
        # Draw metadata with icons
        metadata = [
            ("👁️", f"{views}"),
            ("⏱️", f"{duration}"),
            ("📺", f"{channel}")
        ]
        
        for i, (icon, text) in enumerate(metadata):
            y_pos = meta_start_y + (i * line_gap)
            
            # Icon
            draw.text((info_x + 2, y_pos + 2), icon, fill=TEXT_SHADOW, font=icon_font)
            draw.text((info_x, y_pos), icon, fill=TEXT_NEON, font=icon_font)
            
            # Text
            meta_text = f"  {text}"
            draw.text((info_x + 40 + 2, y_pos + 2), meta_text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x + 40, y_pos), meta_text, fill=TEXT_SOFT, font=meta_font)

        # Add decorative elements
        # Top-right corner accent
        accent_size = 200
        accent = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent)
        accent_draw.pieslice([0, 0, accent_size*2, accent_size*2], 0, 90, 
                           fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent, (CANVAS_W - accent_size, 0), accent)

        # Bottom-left corner accent
        accent2 = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent2_draw = ImageDraw.Draw(accent2)
        accent2_draw.pieslice([-accent_size, -accent_size, accent_size, accent_size], 
                            180, 270, fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent2, (0, CANVAS_H - accent_size), accent2)

        # Add subtle grid lines
        grid_alpha = 20
        for i in range(0, CANVAS_W, 50):
            draw.line([(i, 0), (i, CANVAS_H)], fill=(255, 255, 255, grid_alpha), width=1)
        for i in range(0, CANVAS_H, 50):
            draw.line([(0, i), (CANVAS_W, i)], fill=(255, 255, 255, grid_alpha), width=1)

        # Add final glow effect to entire image
        canvas = add_glow_effect(canvas, (0, 0, 0, 30), radius=2)

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95)

        # Clean up downloaded thumbnail
        try:
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as cleanup_error:
            print(f"[Cleanup Error] {cleanup_error}")

        return str(out)

    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback: Return the default thumbnail
        try:
            if os.path.exists(FALLBACK_THUMB):
                print(f"[Fallback] Returning default thumbnail: {FALLBACK_THUMB}")
                return FALLBACK_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {FALLBACK_THUMB}")
                return None
        except Exception as fallback_error:
            print(f"[Fallback Error] {fallback_error}")
            return None
        finally:
            # Clean up any partial downloads
            try:
                if thumb_path and os.path.exists(thumb_path):
                    os.remove(thumb_path)
            except:
                pass    top = Image.new('RGBA', size, end_color)
    
    mask = Image.new('L', size)
    mask_data = []
    
    if direction == 'diagonal':
        for y in range(size[1]):
            for x in range(size[0]):
                # Calculate diagonal gradient value
                value = int(255 * (x + y) / (size[0] + size[1]))
                mask_data.append(value)
    else:  # vertical
        for y in range(size[1]):
            value = int(255 * y / size[1])
            for x in range(size[0]):
                mask_data.append(value)
    
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def create_noise_texture(size, intensity=10):
    """Create noise texture without numpy"""
    noise_img = Image.new('RGBA', size, (0, 0, 0, 0))
    noise_draw = ImageDraw.Draw(noise_img)
    
    # Create random noise pixels
    for y in range(0, size[1], 2):
        for x in range(0, size[0], 2):
            if random.random() > 0.7:  # 30% chance of noise pixel
                gray = random.randint(0, intensity)
                noise_draw.point((x, y), (gray, gray, gray, 5))
    
    return noise_img

def add_glow_effect(image, glow_color, radius=20):
    """Add glow effect to image"""
    glow = image.filter(ImageFilter.GaussianBlur(radius))
    glow = ImageChops.multiply(glow, Image.new('RGBA', glow.size, glow_color))
    return Image.alpha_composite(glow, image)

def create_vibrant_border(image, border_color, border_width=10, glow=True):
    """Create a vibrant border with optional glow"""
    border_img = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    
    # Draw border rectangles
    for i in range(border_width):
        alpha = 255 - (i * 255 // border_width)
        color = (*border_color[:3], alpha)
        draw.rectangle(
            [i, i, image.size[0]-i, image.size[1]-i],
            outline=color,
            width=1
        )
    
    if glow:
        border_img = border_img.filter(ImageFilter.GaussianBlur(3))
    
    return Image.alpha_composite(image, border_img)

def draw_text_with_shadow(draw, position, text, font, main_color, shadow_color, shadow_offset=(3, 3)):
    """Draw text with shadow effect"""
    x, y = position
    sx, sy = shadow_offset
    
    # Draw multiple shadows for depth
    for dx, dy in [(sx, sy), (sx-1, sy), (sx, sy-1), (sx+1, sy), (sx, sy+1)]:
        draw.text((x+dx, y+dy), text, font=font, fill=shadow_color)
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=main_color)

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text to fit within max_width and max_lines"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if draw.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            
            if len(lines) >= max_lines:
                # Add ellipsis to last line if truncated
                last_line = lines[-1]
                while draw.textlength(last_line + "...", font=font) > max_width and last_line:
                    last_line = last_line[:-1]
                lines[-1] = last_line + "..."
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def create_circular_image(image, size):
    """Create circular image with smooth edges"""
    mask = Image.new('L', (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * 2, size * 2), fill=255)
    
    mask = mask.resize((size, size), Image.LANCZOS)
    output = Image.new('RGBA', (size, size))
    output.paste(image.resize((size, size)), (0, 0), mask)
    return output

def add_pulse_ring(draw, center, size, color, width=5, segments=12):
    """Add animated-style pulse rings"""
    x, y = center
    for i in range(3):
        radius = size + (i * 20)
        alpha = 100 - (i * 30)
        segment_length = math.pi * 2 / segments
        
        for s in range(segments):
            if s % 2 == 0:  # Create dashed effect
                start_angle = s * segment_length
                end_angle = start_angle + segment_length * 0.7
                
                draw.arc(
                    [x - radius, y - radius, x + radius, y + radius],
                    math.degrees(start_angle),
                    math.degrees(end_angle),
                    (*color[:3], alpha),
                    width
                )

def draw_rounded_rectangle(draw, xy, radius, **kwargs):
    """Draw rounded rectangle without relying on PIL's rounded_rectangle if not available"""
    x1, y1, x2, y2 = xy
    fill_color = kwargs.get('fill')
    
    # Draw main rectangle
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill_color)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill_color)
    
    # Draw four corners
    for x, y in [(x1 + radius, y1 + radius), (x2 - radius, y1 + radius),
                 (x1 + radius, y2 - radius), (x2 - radius, y2 - radius)]:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill_color)

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Create gradient background
        canvas = create_gradient((CANVAS_W, CANVAS_H), GRADIENT_START, GRADIENT_END)
        draw = ImageDraw.Draw(canvas)

        # Add subtle noise texture without numpy
        noise_img = create_noise_texture((CANVAS_W, CANVAS_H), intensity=15)
        canvas = Image.alpha_composite(canvas, noise_img)

        # Process and add blurred background image
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(BG_BLUR))
        bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHTNESS)
        bg.putalpha(80)
        
        # Apply gradient overlay to background
        gradient_overlay = create_gradient((CANVAS_W, CANVAS_H), (0, 0, 0, 180), (0, 0, 0, 80))
        bg = Image.alpha_composite(bg, gradient_overlay)
        
        # Composite background
        canvas = Image.alpha_composite(canvas, bg)

        # Add vibrant border
        canvas = create_vibrant_border(canvas, LIME_BORDER, border_width=8, glow=True)

        # Thumbnail setup
        thumb_size = 520
        circle_x = 120
        circle_y = (CANVAS_H - thumb_size) // 2

        # Create circular thumbnail with border
        circular_thumb = create_circular_image(base_img, thumb_size)
        
        # Add glow to thumbnail
        thumb_glow = Image.new('RGBA', (thumb_size + 40, thumb_size + 40), (0, 0, 0, 0))
        thumb_glow_draw = ImageDraw.Draw(thumb_glow)
        thumb_glow_draw.ellipse(
            [20, 20, thumb_size + 20, thumb_size + 20],
            outline=GLOW_COLOR,
            width=15
        )
        thumb_glow = thumb_glow.filter(ImageFilter.GaussianBlur(10))
        
        # Composite thumbnail with glow
        canvas.paste(thumb_glow, (circle_x - 20, circle_y - 20), thumb_glow)
        canvas.paste(circular_thumb, (circle_x, circle_y), circular_thumb)

        # Add pulse rings around thumbnail
        add_pulse_ring(draw, (circle_x + thumb_size//2, circle_y + thumb_size//2), 
                      thumb_size//2, GLOW_COLOR, width=3)

        # Modern header with logo/text
        try:
            header_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        except:
            header_font = ImageFont.load_default()
            
        logo_text = "♫ ALLICE MUSIC"
        
        # Create logo background
        logo_bg = Image.new('RGBA', (400, 60), (0, 0, 0, 0))
        logo_draw = ImageDraw.Draw(logo_bg)
        
        # Use custom rounded rectangle function
        draw_rounded_rectangle(logo_draw, [0, 0, 400, 60], 30, fill=(0, 0, 0, 150))
        
        canvas.paste(logo_bg, (40, 40), logo_bg)
        draw_text_with_shadow(draw, (60, 52), logo_text, header_font, 
                            TEXT_NEON, TEXT_SHADOW, shadow_offset=(2, 2))

        # NOW PLAYING with modern styling
        info_x = circle_x + thumb_size + 80
        max_text_w = CANVAS_W - info_x - 60
        
        try:
            np_font = ImageFont.truetype(FONT_BOLD_PATH, 68)
        except:
            np_font = ImageFont.load_default()
            
        np_text = "NOW PLAYING"
        
        # Animated-style underline for NOW PLAYING
        underline_y = 220
        draw.line([(info_x, underline_y), (info_x + max_text_w, underline_y)], 
                 fill=TEXT_NEON, width=3)
        
        # Dotted line effect
        for i in range(0, int(max_text_w), 15):
            if i % 30 == 0:
                draw.line([(info_x + i, underline_y), (info_x + i + 8, underline_y)], 
                         fill=TEXT_NEON, width=3)
        
        draw_text_with_shadow(draw, (info_x, 140), np_text, np_font, 
                            TEXT_WHITE, TEXT_SHADOW, shadow_offset=(3, 3))

        # Title with modern wrapping
        try:
            title_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
        except:
            title_font = ImageFont.load_default()
            
        wrapped_title = wrap_text(draw, title, title_font, max_text_w)
        
        title_y = 250
        draw.multiline_text((info_x + 2, title_y + 2), wrapped_title, 
                          fill=TEXT_SHADOW, font=title_font, spacing=8)
        draw.multiline_text((info_x, title_y), wrapped_title, 
                          fill=TEXT_WHITE, font=title_font, spacing=8)

        # Metadata with icons
        meta_start_y = title_y + 180
        
        try:
            meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 32)
            icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 36)
        except:
            meta_font = ImageFont.load_default()
            icon_font = ImageFont.load_default()
            
        line_gap = 50
        
        # Draw metadata with icons
        metadata = [
            ("👁️", f"{views}"),
            ("⏱️", f"{duration}"),
            ("📺", f"{channel}")
        ]
        
        for i, (icon, text) in enumerate(metadata):
            y_pos = meta_start_y + (i * line_gap)
            
            # Icon
            draw.text((info_x + 2, y_pos + 2), icon, fill=TEXT_SHADOW, font=icon_font)
            draw.text((info_x, y_pos), icon, fill=TEXT_NEON, font=icon_font)
            
            # Text
            meta_text = f"  {text}"
            draw.text((info_x + 40 + 2, y_pos + 2), meta_text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x + 40, y_pos), meta_text, fill=TEXT_SOFT, font=meta_font)

        # Add decorative elements
        # Top-right corner accent
        accent_size = 200
        accent = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent)
        accent_draw.pieslice([0, 0, accent_size*2, accent_size*2], 0, 90, 
                           fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent, (CANVAS_W - accent_size, 0), accent)

        # Bottom-left corner accent
        accent2 = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent2_draw = ImageDraw.Draw(accent2)
        accent2_draw.pieslice([-accent_size, -accent_size, accent_size, accent_size], 
                            180, 270, fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent2, (0, CANVAS_H - accent_size), accent2)

        # Add subtle grid lines
        grid_alpha = 20
        for i in range(0, CANVAS_W, 50):
            draw.line([(i, 0), (i, CANVAS_H)], fill=(255, 255, 255, grid_alpha), width=1)
        for i in range(0, CANVAS_H, 50):
            draw.line([(0, i), (CANVAS_W, i)], fill=(255, 255, 255, grid_alpha), width=1)

        # Add final glow effect to entire image
        canvas = add_glow_effect(canvas, (0, 0, 0, 30), radius=2)

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95)

        # Clean up downloaded thumbnail
        try:
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as cleanup_error:
            print(f"[Cleanup Error] {cleanup_error}")

        return str(out)

    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback: Return the default thumbnail
        try:
            if os.path.exists(FALLBACK_THUMB):
                print(f"[Fallback] Returning default thumbnail: {FALLBACK_THUMB}")
                return FALLBACK_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {FALLBACK_THUMB}")
                return None
        except Exception as fallback_error:
            print(f"[Fallback Error] {fallback_error}")
            return None
        finally:
            # Clean up any partial downloads
            try:
                if thumb_path and os.path.exists(thumb_path):
                    os.remove(thumb_path)
            except:
                pass    """Create a gradient background"""
    base = Image.new('RGBA', size, start_color)
    top = Image.new('RGBA', size, end_color)
    
    if direction == 'diagonal':
        mask = Image.new('L', size)
        mask_data = []
        for y in range(size[1]):
            for x in range(size[0]):
                mask_data.append(int(255 * (x + y) / (size[0] + size[1])))
        mask.putdata(mask_data)
    else:  # vertical
        mask = Image.new('L', size)
        mask_data = []
        for y in range(size[1]):
            for x in range(size[0]):
                mask_data.append(int(255 * y / size[1]))
        mask.putdata(mask_data)
    
    base.paste(top, (0, 0), mask)
    return base

def add_glow_effect(image, glow_color, radius=20):
    """Add glow effect to image"""
    glow = image.filter(ImageFilter.GaussianBlur(radius))
    glow = ImageChops.multiply(glow, Image.new('RGBA', glow.size, glow_color))
    return Image.alpha_composite(glow, image)

def create_vibrant_border(image, border_color, border_width=10, glow=True):
    """Create a vibrant border with optional glow"""
    border_img = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(border_img)
    
    # Draw border rectangles
    for i in range(border_width):
        alpha = 255 - (i * 255 // border_width)
        color = (*border_color[:3], alpha)
        draw.rectangle(
            [i, i, image.size[0]-i, image.size[1]-i],
            outline=color,
            width=1
        )
    
    if glow:
        border_img = border_img.filter(ImageFilter.GaussianBlur(3))
    
    return Image.alpha_composite(image, border_img)

def draw_text_with_shadow(draw, position, text, font, main_color, shadow_color, shadow_offset=(3, 3)):
    """Draw text with shadow effect"""
    x, y = position
    sx, sy = shadow_offset
    
    # Draw multiple shadows for depth
    for dx, dy in [(sx, sy), (sx-1, sy), (sx, sy-1), (sx+1, sy), (sx, sy+1)]:
        draw.text((x+dx, y+dy), text, font=font, fill=shadow_color)
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=main_color)

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text to fit within max_width and max_lines"""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if draw.textlength(test_line, font=font) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            
            if len(lines) >= max_lines:
                # Add ellipsis to last line if truncated
                last_line = lines[-1]
                while draw.textlength(last_line + "...", font=font) > max_width and last_line:
                    last_line = last_line[:-1]
                lines[-1] = last_line + "..."
                break
    
    if current_line and len(lines) < max_lines:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines)

def create_circular_image(image, size):
    """Create circular image with smooth edges"""
    mask = Image.new('L', (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size * 2, size * 2), fill=255)
    
    mask = mask.resize((size, size), Image.LANCZOS)
    output = Image.new('RGBA', (size, size))
    output.paste(image.resize((size, size)), (0, 0), mask)
    return output

def add_pulse_ring(draw, center, size, color, width=5, segments=12):
    """Add animated-style pulse rings"""
    x, y = center
    for i in range(3):
        radius = size + (i * 20)
        alpha = 100 - (i * 30)
        segment_length = math.pi * 2 / segments
        
        for s in range(segments):
            if s % 2 == 0:  # Create dashed effect
                start_angle = s * segment_length
                end_angle = start_angle + segment_length * 0.7
                
                draw.arc(
                    [x - radius, y - radius, x + radius, y + radius],
                    math.degrees(start_angle),
                    math.degrees(end_angle),
                    (*color[:3], alpha),
                    width
                )

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title    = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views    = result.get("viewCount", {}).get("short", "Unknown Views")
        channel  = result.get("channel", {}).get("name", "Unknown Channel")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Create gradient background
        canvas = create_gradient((CANVAS_W, CANVAS_H), GRADIENT_START, GRADIENT_END)
        draw = ImageDraw.Draw(canvas)

        # Add subtle noise texture
        noise = np.random.randint(0, 20, (CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
        noise_img = Image.fromarray(noise, 'RGB').convert('RGBA')
        noise_img.putalpha(10)  # Very subtle
        canvas = Image.alpha_composite(canvas, noise_img)

        # Process and add blurred background image
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(BG_BLUR))
        bg = ImageEnhance.Brightness(bg).enhance(BG_BRIGHTNESS)
        bg.putalpha(80)  # Semi-transparent
        
        # Apply gradient overlay to background
        gradient_overlay = create_gradient((CANVAS_W, CANVAS_H), (0, 0, 0, 180), (0, 0, 0, 80))
        bg = Image.alpha_composite(bg, gradient_overlay)
        
        # Composite background
        canvas = Image.alpha_composite(canvas, bg)

        # Add vibrant border
        canvas = create_vibrant_border(canvas, LIME_BORDER, border_width=8, glow=True)

        # Thumbnail setup
        thumb_size = 520
        circle_x = 120
        circle_y = (CANVAS_H - thumb_size) // 2

        # Create circular thumbnail with border
        circular_thumb = create_circular_image(base_img, thumb_size)
        
        # Add glow to thumbnail
        thumb_glow = Image.new('RGBA', (thumb_size + 40, thumb_size + 40), (0, 0, 0, 0))
        thumb_glow_draw = ImageDraw.Draw(thumb_glow)
        thumb_glow_draw.ellipse(
            [20, 20, thumb_size + 20, thumb_size + 20],
            outline=GLOW_COLOR,
            width=15
        )
        thumb_glow = thumb_glow.filter(ImageFilter.GaussianBlur(10))
        
        # Composite thumbnail with glow
        canvas.paste(thumb_glow, (circle_x - 20, circle_y - 20), thumb_glow)
        canvas.paste(circular_thumb, (circle_x, circle_y), circular_thumb)

        # Add pulse rings around thumbnail
        add_pulse_ring(draw, (circle_x + thumb_size//2, circle_y + thumb_size//2), 
                      thumb_size//2, GLOW_COLOR, width=3)

        # Modern header with logo/text
        header_font = ImageFont.truetype(FONT_BOLD_PATH, 42)
        logo_text = "♫ ALLICE MUSIC"
        
        # Create logo background
        logo_bg = Image.new('RGBA', (400, 60), (0, 0, 0, 0))
        logo_draw = ImageDraw.Draw(logo_bg)
        logo_draw.rounded_rectangle([0, 0, 400, 60], radius=30, 
                                   fill=(0, 0, 0, 150))
        
        canvas.paste(logo_bg, (40, 40), logo_bg)
        draw_text_with_shadow(draw, (60, 52), logo_text, header_font, 
                            TEXT_NEON, TEXT_SHADOW, shadow_offset=(2, 2))

        # NOW PLAYING with modern styling
        info_x = circle_x + thumb_size + 80
        max_text_w = CANVAS_W - info_x - 60
        
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 68)
        np_text = "NOW PLAYING"
        
        # Animated-style underline for NOW PLAYING
        underline_y = 220
        draw.line([(info_x, underline_y), (info_x + max_text_w, underline_y)], 
                 fill=TEXT_NEON, width=3)
        
        # Dotted line effect
        for i in range(0, int(max_text_w), 15):
            if i % 30 == 0:
                draw.line([(info_x + i, underline_y), (info_x + i + 8, underline_y)], 
                         fill=TEXT_NEON, width=3)
        
        draw_text_with_shadow(draw, (info_x, 140), np_text, np_font, 
                            TEXT_WHITE, TEXT_SHADOW, shadow_offset=(3, 3))

        # Title with modern wrapping
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
        wrapped_title = wrap_text(draw, title, title_font, max_text_w)
        
        title_y = 250
        draw.multiline_text((info_x + 2, title_y + 2), wrapped_title, 
                          fill=TEXT_SHADOW, font=title_font, spacing=8)
        draw.multiline_text((info_x, title_y), wrapped_title, 
                          fill=TEXT_WHITE, font=title_font, spacing=8)

        # Metadata with icons
        meta_start_y = title_y + 180
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 32)
        line_gap = 50
        
        # Draw metadata with icons
        metadata = [
            ("👁️", f"{views}"),
            ("⏱️", f"{duration}"),
            ("📺", f"{channel}")
        ]
        
        for i, (icon, text) in enumerate(metadata):
            y_pos = meta_start_y + (i * line_gap)
            
            # Icon
            icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 36)
            draw.text((info_x + 2, y_pos + 2), icon, fill=TEXT_SHADOW, font=icon_font)
            draw.text((info_x, y_pos), icon, fill=TEXT_NEON, font=icon_font)
            
            # Text
            meta_text = f"  {text}"
            draw.text((info_x + 40 + 2, y_pos + 2), meta_text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x + 40, y_pos), meta_text, fill=TEXT_SOFT, font=meta_font)

        # Add decorative elements
        # Top-right corner accent
        accent_size = 200
        accent = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent)
        accent_draw.pieslice([0, 0, accent_size*2, accent_size*2], 0, 90, 
                           fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent, (CANVAS_W - accent_size, 0), accent)

        # Bottom-left corner accent
        accent2 = Image.new('RGBA', (accent_size, accent_size), (0, 0, 0, 0))
        accent2_draw = ImageDraw.Draw(accent2)
        accent2_draw.pieslice([-accent_size, -accent_size, accent_size, accent_size], 
                            180, 270, fill=(*GLOW_COLOR[:3], 30), width=0)
        canvas.paste(accent2, (0, CANVAS_H - accent_size), accent2)

        # Add subtle grid lines
        grid_alpha = 20
        for i in range(0, CANVAS_W, 50):
            draw.line([(i, 0), (i, CANVAS_H)], fill=(255, 255, 255, grid_alpha), width=1)
        for i in range(0, CANVAS_H, 50):
            draw.line([(0, i), (CANVAS_W, i)], fill=(255, 255, 255, grid_alpha), width=1)

        # Add final glow effect to entire image
        canvas = add_glow_effect(canvas, (0, 0, 0, 30), radius=2)

        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95)

        # Clean up downloaded thumbnail
        try:
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as cleanup_error:
            print(f"[Cleanup Error] {cleanup_error}")

        return str(out)

    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback: Return the default thumbnail
        try:
            if os.path.exists(FALLBACK_THUMB):
                print(f"[Fallback] Returning default thumbnail: {FALLBACK_THUMB}")
                return FALLBACK_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {FALLBACK_THUMB}")
                return None
        except Exception as fallback_error:
            print(f"[Fallback Error] {fallback_error}")
            return None
        finally:
            # Clean up any partial downloads
            try:
                if thumb_path and os.path.exists(thumb_path):
                    os.remove(thumb_path)
            except:
                pass

# Optional: Add animation effect function for future use
def create_animated_thumbnail(base_image, output_path):
    """Create a simple animated thumbnail (requires additional libraries)"""
    # This would use PIL's save with append for GIF or other methods
    # Currently placeholder for future enhancement
    pass
