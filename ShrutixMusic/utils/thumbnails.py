# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com
#
# ATLEAST GIVE CREDITS IF YOU STEALING :
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import os
import aiohttp
import aiofiles
import traceback
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Canvas size
CANVAS_W, CANVAS_H = 1280, 720

# Color scheme
BG_COLOR = (20, 20, 30, 255)
TEXT_WHITE = (255, 255, 255, 255)
TEXT_LIGHT = (230, 230, 230, 255)
TEXT_GRAY = (180, 180, 180, 255)
ACCENT_BLUE = (30, 144, 255, 255)
ACCENT_GREEN = (57, 255, 20, 255)
ACCENT_PINK = (255, 105, 180, 255)
ACCENT_PURPLE = (138, 43, 226, 255)
SHADOW_COLOR = (0, 0, 0, 180)

# Font paths
FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB = "ShrutixMusic/assets/temp_thumb.jpg"

# Ensure fonts exist
try:
    FONT_REGULAR = ImageFont.truetype(FONT_REGULAR_PATH, 30)
    FONT_BOLD = ImageFont.truetype(FONT_BOLD_PATH, 30)
except:
    # Fallback to default font if custom fonts not found
    FONT_REGULAR = ImageFont.load_default()
    FONT_BOLD = ImageFont.load_default()

async def get_youtube_data(videoid: str):
    """Fetch YouTube video data"""
    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = await results.next()
        
        if not data or "result" not in data or len(data["result"]) == 0:
            return None
            
        result = data["result"][0]
        
        return {
            "title": result.get("title", "Unknown Song"),
            "duration": result.get("duration", "0:00"),
            "thumbnail": result.get("thumbnails", [{}])[0].get("url", ""),
            "views": result.get("viewCount", {}).get("short", "0 views"),
            "channel": result.get("channel", {}).get("name", "Unknown Channel"),
            "published": result.get("publishedTime", "Unknown")
        }
    except Exception as e:
        print(f"[get_youtube_data Error] {e}")
        return None

def add_rounded_corners(image, radius=20):
    """Add rounded corners to image"""
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius=radius, fill=255)
    
    result = image.copy()
    result.putalpha(mask)
    return result

def add_text_with_shadow(draw, text, position, font, text_color, shadow_color=SHADOW_COLOR, shadow_offset=2):
    """Draw text with shadow effect"""
    x, y = position
    # Draw shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, fill=shadow_color, font=font)
    # Draw main text
    draw.text((x, y), text, fill=text_color, font=font)

def create_simple_gradient(width, height, color1, color2):
    """Create a simple gradient background"""
    gradient = Image.new('RGB', (width, height), color1)
    draw = ImageDraw.Draw(gradient)
    
    for i in range(height):
        # Interpolate between colors
        ratio = i / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, i), (width, i)], fill=(r, g, b))
    
    return gradient.convert('RGBA')

def wrap_text_simple(draw, text, font, max_width, max_lines=2):
    """Simple text wrapping with ellipsis"""
    try:
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = draw.textlength(test_line, font=font)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Word too long, truncate
                    lines.append(word[:15] + "...")
                    break
                
                if len(lines) >= max_lines:
                    # Add ellipsis to last line
                    if len(lines) == max_lines:
                        last_line = lines[-1]
                        while draw.textlength(last_line + "...", font=font) > max_width and len(last_line) > 3:
                            last_line = last_line[:-1]
                        lines[-1] = last_line + "..."
                    break
        
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines) if lines else text[:20]
    except:
        return text[:30]

async def get_thumb(videoid: str, requested_by: str = "User"):
    """Generate thumbnail showing all YouTube details"""
    thumb_path = None
    
    try:
        print(f"[DEBUG] Fetching data for video: {videoid}")
        
        # Get YouTube data
        video_data = await get_youtube_data(videoid)
        
        if not video_data:
            print("[ERROR] Could not fetch YouTube data")
            if os.path.exists(FALLBACK_THUMB):
                return FALLBACK_THUMB
            return None
        
        title = video_data["title"]
        duration = video_data["duration"]
        thumbnail_url = video_data["thumbnail"]
        views = video_data["views"]
        channel = video_data["channel"]
        
        print(f"[DEBUG] Title: {title}")
        print(f"[DEBUG] Channel: {channel}")
        print(f"[DEBUG] Views: {views}")
        print(f"[DEBUG] Duration: {duration}")
        print(f"[DEBUG] Thumbnail URL: {thumbnail_url}")
        
        # Download thumbnail
        if thumbnail_url:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumbnail_url) as resp:
                        if resp.status == 200:
                            thumb_path = CACHE_DIR / f"thumb_{videoid}.jpg"
                            async with aiofiles.open(thumb_path, "wb") as f:
                                await f.write(await resp.read())
                            print(f"[DEBUG] Thumbnail downloaded to: {thumb_path}")
                        else:
                            print(f"[ERROR] Failed to download thumbnail: {resp.status}")
            except Exception as e:
                print(f"[ERROR] Download failed: {e}")
        
        # Create canvas
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
        draw = ImageDraw.Draw(canvas)
        
        # Create gradient background
        gradient = create_simple_gradient(
            CANVAS_W, CANVAS_H,
            (30, 30, 50),  # Dark blue
            (60, 20, 80)   # Dark purple
        )
        canvas.paste(gradient, (0, 0))
        
        # Add background pattern (subtle dots)
        for _ in range(100):
            x = random.randint(0, CANVAS_W)
            y = random.randint(0, CANVAS_H)
            size = random.randint(1, 3)
            color = (random.randint(50, 100), random.randint(50, 100), random.randint(100, 150), 50)
            draw.ellipse([x, y, x + size, y + size], fill=color)
        
        # Load and process YouTube thumbnail
        if thumb_path and os.path.exists(thumb_path):
            try:
                base_img = Image.open(thumb_path).convert("RGBA")
                
                # Create blurred background from thumbnail
                bg_blur = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
                bg_blur = bg_blur.filter(ImageFilter.GaussianBlur(25))
                
                # Darken the blurred background
                enhancer = ImageEnhance.Brightness(bg_blur)
                bg_blur = enhancer.enhance(0.4)
                
                # Apply gradient overlay
                overlay = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 150))
                bg_blur = Image.alpha_composite(bg_blur, overlay)
                
                # Paste blurred background
                canvas.paste(bg_blur, (0, 0), bg_blur)
                
            except Exception as e:
                print(f"[ERROR] Processing thumbnail: {e}")
        
        # Main content container
        container_width = CANVAS_W - 100
        container_height = CANVAS_H - 100
        container_x = 50
        container_y = 50
        
        # Draw semi-transparent container
        container_bg = Image.new('RGBA', (container_width, container_height), (255, 255, 255, 30))
        container_bg = container_bg.filter(ImageFilter.GaussianBlur(5))
        canvas.paste(container_bg, (container_x, container_y), container_bg)
        
        # Draw container border
        draw.rounded_rectangle(
            [container_x, container_y, 
             container_x + container_width, container_y + container_height],
            radius=20,
            outline=(255, 255, 255, 80),
            width=2
        )
        
        # YouTube Thumbnail Display (Left side)
        thumb_display_size = 380
        thumb_x = container_x + 40
        thumb_y = container_y + (container_height - thumb_display_size) // 2
        
        if thumb_path and os.path.exists(thumb_path):
            try:
                thumb_img = Image.open(thumb_path).convert("RGBA")
                thumb_img = thumb_img.resize((thumb_display_size, thumb_display_size), Image.LANCZOS)
                
                # Add rounded corners and border
                thumb_img = add_rounded_corners(thumb_img, 15)
                
                # Add shadow
                shadow_offset = 10
                shadow = Image.new('RGBA', 
                                 (thumb_display_size + shadow_offset*2, thumb_display_size + shadow_offset*2),
                                 (0, 0, 0, 100))
                shadow = add_rounded_corners(shadow, 20)
                shadow = shadow.filter(ImageFilter.GaussianBlur(10))
                canvas.paste(shadow, (thumb_x - shadow_offset//2, thumb_y - shadow_offset//2), shadow)
                
                # Add thumbnail border
                border_size = thumb_display_size + 8
                border = Image.new('RGBA', (border_size, border_size), ACCENT_BLUE)
                border = add_rounded_corners(border, 18)
                canvas.paste(border, (thumb_x - 4, thumb_y - 4), border)
                
                # Place thumbnail
                canvas.paste(thumb_img, (thumb_x, thumb_y), thumb_img)
                
                # Add play button overlay
                play_size = 60
                play_x = thumb_x + (thumb_display_size - play_size) // 2
                play_y = thumb_y + (thumb_display_size - play_size) // 2
                
                play_bg = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 180))
                play_draw = ImageDraw.Draw(play_bg)
                play_draw.ellipse([0, 0, play_size, play_size], fill=ACCENT_PINK)
                
                # Play triangle
                triangle_size = 30
                triangle_points = [
                    (play_size*0.3, play_size*0.2),
                    (play_size*0.3, play_size*0.8),
                    (play_size*0.7, play_size*0.5)
                ]
                play_draw.polygon(triangle_points, fill=TEXT_WHITE)
                
                canvas.paste(play_bg, (play_x, play_y), play_bg)
                
            except Exception as e:
                print(f"[ERROR] Displaying thumbnail: {e}")
                # Draw placeholder if thumbnail fails
                draw.rectangle([thumb_x, thumb_y, 
                              thumb_x + thumb_display_size, thumb_y + thumb_display_size],
                             fill=(50, 50, 70, 255))
                add_text_with_shadow(draw, "No Thumbnail", 
                                   (thumb_x + 100, thumb_y + thumb_display_size//2 - 15),
                                   FONT_BOLD, TEXT_GRAY)
        
        # Content Area (Right side)
        content_x = thumb_x + thumb_display_size + 60
        content_y = thumb_y
        content_width = container_width - (content_x - container_x) - 40
        
        # Header: Music Player Name
        header_font = ImageFont.truetype(FONT_BOLD_PATH, 42) if os.path.exists(FONT_BOLD_PATH) else ImageFont.load_default()
        header_text = "🎵 Shrutix Music"
        add_text_with_shadow(draw, header_text, (content_x, content_y), header_font, ACCENT_GREEN)
        
        # Now Playing Badge
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 28) if os.path.exists(FONT_BOLD_PATH) else ImageFont.load_default()
        np_y = content_y + 70
        
        # Draw badge background
        badge_width = 200
        badge_height = 45
        badge_bg = Image.new('RGBA', (badge_width, badge_height), ACCENT_BLUE)
        badge_bg = add_rounded_corners(badge_bg, badge_height//2)
        canvas.paste(badge_bg, (content_x, np_y), badge_bg)
        
        # Badge text
        np_text = "▶ NOW PLAYING"
        np_text_x = content_x + (badge_width - draw.textlength(np_text, font=np_font)) // 2
        draw.text((np_text_x, np_y + badge_height//2 - 12), np_text, fill=TEXT_WHITE, font=np_font)
        
        # Song Title
        title_y = np_y + badge_height + 40
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 36) if os.path.exists(FONT_BOLD_PATH) else ImageFont.load_default()
        
        # Wrap title if too long
        max_title_width = content_width - 40
        wrapped_title = wrap_text_simple(draw, title, title_font, max_title_width, max_lines=2)
        
        # Draw title
        title_lines = wrapped_title.split('\n')
        for i, line in enumerate(title_lines):
            add_text_with_shadow(draw, line, (content_x, title_y + i*45), title_font, TEXT_WHITE)
        
        # Song Details Panel
        details_y = title_y + len(title_lines)*45 + 30
        details_panel_height = 220
        details_font = ImageFont.truetype(FONT_REGULAR_PATH, 26) if os.path.exists(FONT_REGULAR_PATH) else ImageFont.load_default()
        icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 28) if os.path.exists(FONT_REGULAR_PATH) else ImageFont.load_default()
        
        # Create details panel background
        panel_bg = Image.new('RGBA', (content_width, details_panel_height), (255, 255, 255, 30))
        panel_bg = add_rounded_corners(panel_bg, 15)
        canvas.paste(panel_bg, (content_x, details_y), panel_bg)
        
        # Draw details border
        draw.rounded_rectangle(
            [content_x, details_y, 
             content_x + content_width, details_y + details_panel_height],
            radius=15,
            outline=(255, 255, 255, 60),
            width=2
        )
        
        # Channel Details
        row1_y = details_y + 30
        draw.text((content_x + 20, row1_y), "📺", fill=ACCENT_BLUE, font=icon_font)
        add_text_with_shadow(draw, f"Channel: {channel}", 
                           (content_x + 60, row1_y), details_font, TEXT_LIGHT)
        
        # Views Details
        row2_y = row1_y + 50
        draw.text((content_x + 20, row2_y), "👁️", fill=ACCENT_GREEN, font=icon_font)
        add_text_with_shadow(draw, f"Views: {views}", 
                           (content_x + 60, row2_y), details_font, TEXT_LIGHT)
        
        # Duration Details
        row3_y = row2_y + 50
        draw.text((content_x + 20, row3_y), "⏱️", fill=ACCENT_PINK, font=icon_font)
        add_text_with_shadow(draw, f"Duration: {duration}", 
                           (content_x + 60, row3_y), details_font, TEXT_LIGHT)
        
        # Requested By Details
        row4_y = row3_y + 50
        draw.text((content_x + 20, row4_y), "👤", fill=ACCENT_PURPLE, font=icon_font)
        add_text_with_shadow(draw, f"Requested by: {requested_by}", 
                           (content_x + 60, row4_y), details_font, TEXT_LIGHT)
        
        # Progress Bar (optional)
        progress_y = details_y + details_panel_height + 20
        progress_width = content_width
        progress_height = 8
        
        # Draw progress bar background
        draw.rounded_rectangle(
            [content_x, progress_y, 
             content_x + progress_width, progress_y + progress_height],
            radius=progress_height//2,
            fill=(60, 60, 60, 200)
        )
        
        # Draw progress (30% as example)
        progress_fill = int(progress_width * 0.3)
        draw.rounded_rectangle(
            [content_x, progress_y, 
             content_x + progress_fill, progress_y + progress_height],
            radius=progress_height//2,
            fill=ACCENT_GREEN
        )
        
        # Time stamps
        time_font = ImageFont.truetype(FONT_REGULAR_PATH, 22) if os.path.exists(FONT_REGULAR_PATH) else ImageFont.load_default()
        draw.text((content_x, progress_y + 15), "0:00", fill=TEXT_GRAY, font=time_font)
        draw.text((content_x + progress_width - 50, progress_y + 15), duration, fill=TEXT_GRAY, font=time_font)
        
        # Decorative Elements
        
        # Top right decorative
        circle_size = 100
        circle_x = container_x + container_width - circle_size - 20
        circle_y = container_y + 20
        draw.ellipse([circle_x, circle_y, circle_x + circle_size, circle_y + circle_size], 
                    outline=ACCENT_PINK, width=3)
        
        # Music note
        note_font = ImageFont.truetype(FONT_BOLD_PATH, 50) if os.path.exists(FONT_BOLD_PATH) else ImageFont.load_default()
        draw.text((circle_x + circle_size//2 - 15, circle_y + circle_size//2 - 25), 
                 "♪", fill=ACCENT_BLUE, font=note_font)
        
        # Bottom decorative wave
        wave_y = container_y + container_height - 50
        for i in range(0, container_width, 30):
            height = random.randint(5, 20)
            draw.rectangle([container_x + i, wave_y, 
                          container_x + i + 20, wave_y - height],
                         fill=(ACCENT_BLUE[0], ACCENT_BLUE[1], ACCENT_BLUE[2], 100))
        
        # Save final thumbnail
        out = CACHE_DIR / f"{videoid}_thumbnail.png"
        canvas.save(out, "PNG", quality=95)
        print(f"[DEBUG] Thumbnail saved to: {out}")
        
        # Clean up downloaded thumbnail
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
                print(f"[DEBUG] Cleaned up temporary thumbnail")
            except:
                pass
        
        return str(out)
        
    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback
        try:
            if os.path.exists(FALLBACK_THUMB):
                print("[Fallback] Using default thumbnail")
                return FALLBACK_THUMB
        except:
            pass
        
        return None

# Test function (you can remove this)
async def test_thumbnail():
    """Test the thumbnail generation"""
    test_video_id = "dQw4w9WgXcQ"  # Example YouTube video ID
    print("Testing thumbnail generation...")
    result = await get_thumb(test_video_id, "Test User")
    print(f"Result: {result}")

# Run test if script is executed directly
if __name__ == "__main__":
    import asyncio
    asyncio.run(test_thumbnail())
