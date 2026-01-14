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
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps
from py_yt import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Canvas size
CANVAS_W, CANVAS_H = 1280, 720

# Color scheme from the image
BACKGROUND_COLOR = (26, 26, 26, 255)  # Dark gray background
TEXT_WHITE = (255, 255, 255, 255)
TEXT_LIGHT_GRAY = (200, 200, 200, 255)
TEXT_DARK_GRAY = (150, 150, 150, 255)
ACCENT_RED = (255, 0, 0, 255)
ACCENT_GREEN = (0, 200, 83, 255)
ACCENT_BLUE = (66, 133, 244, 255)

FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB = "ShrutixMusic/assets/temp_thumb.jpg"

def change_image_size(max_w, max_h, image):
    try:
        ratio = min(max_w / image.size[0], max_h / image.size[1])
        return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)
    except Exception as e:
        print(f"[change_image_size Error] {e}")
        return image

def wrap_text_ellipsis(draw, text, font, max_width):
    """Wrap text and add ellipsis if too long"""
    try:
        if draw.textlength(text, font=font) <= max_width:
            return text
        
        ellipsis = "..."
        ellipsis_width = draw.textlength(ellipsis, font=font)
        
        result = ""
        for char in text:
            test = result + char + ellipsis
            if draw.textlength(test, font=font) <= max_width:
                result += char
            else:
                break
        
        return result + ellipsis if result else ellipsis
    except Exception as e:
        print(f"[wrap_text_ellipsis Error] {e}")
        return text[:30]

def fit_title_font(draw, text, max_width, font_path, start_size=48, min_size=36):
    """Find optimal font size for title"""
    try:
        size = start_size
        while size >= min_size:
            try:
                font = ImageFont.truetype(font_path, size)
            except:
                size -= 2
                continue
            
            wrapped = wrap_text_ellipsis(draw, text, font, max_width)
            if draw.textlength(wrapped, font=font) <= max_width:
                return font, wrapped
            size -= 2
        
        font = ImageFont.truetype(font_path, min_size)
        return font, wrap_text_ellipsis(draw, text, font, max_width)
    except Exception as e:
        print(f"[fit_title_font Error] {e}")
        try:
            font = ImageFont.truetype(font_path, min_size)
            return font, text[:40]
        except:
            return ImageFont.load_default(), text[:40]

def create_rounded_square(size, radius, color):
    """Create a rounded square/rectangle"""
    try:
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=color)
        return image
    except Exception as e:
        print(f"[create_rounded_square Error] {e}")
        image = Image.new('RGBA', (size, size), color)
        return image

def add_curve_overlay(image, curve_height=60, color=(20, 20, 20, 200)):
    """Add curved overlay on top of image"""
    try:
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw curved shape
        width, height = image.size
        points = [
            (0, 0),
            (width, 0),
            (width, curve_height),
            (width//2 + 100, curve_height + 40),
            (width//2 - 100, curve_height + 40),
            (0, curve_height)
        ]
        
        draw.polygon(points, fill=color)
        
        # Blend with original image
        return Image.alpha_composite(image, overlay)
    except Exception as e:
        print(f"[add_curve_overlay Error] {e}")
        return image

def format_duration(duration_str):
    """Format duration string"""
    try:
        if not duration_str or duration_str == "Unknown":
            return "5:11"  # Default duration like in reference
        
        # If duration is already in MM:SS format
        if ":" in duration_str:
            # Handle cases like "5:11" or "1:23:45"
            parts = duration_str.split(":")
            if len(parts) == 2:
                # MM:SS format
                minutes = parts[0]
                seconds = parts[1]
                return f"{minutes}:{seconds}"
            elif len(parts) == 3:
                # HH:MM:SS format, convert to minutes
                hours = int(parts[0])
                minutes = int(parts[1]) + (hours * 60)
                seconds = parts[2]
                return f"{minutes}:{seconds}"
        
        # If duration is just a number (seconds)
        try:
            total_seconds = int(duration_str)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}:{seconds:02d}"
        except:
            return "5:11"
    except Exception as e:
        print(f"[format_duration Error] {e}")
        return "5:11"

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video data
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title    = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views    = result.get("viewCount", {}).get("short", "Unknown Views")
        channel  = result.get("channel", {}).get("name", "Unknown Channel")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Create canvas with dark gray background
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(canvas)

        # Add subtle texture/noise
        for _ in range(1000):
            x = random.randint(0, CANVAS_W-1)
            y = random.randint(0, CANVAS_H-1)
            draw.point((x, y), fill=(30, 30, 30, 255))

        # Thumbnail container (rounded square on left side)
        thumb_container_size = 500
        thumb_container_x = 60
        thumb_container_y = (CANVAS_H - thumb_container_size) // 2
        
        # Container with shadow
        shadow_offset = 8
        shadow = create_rounded_square(thumb_container_size + shadow_offset*2, 
                                     30, (0, 0, 0, 100))
        canvas.paste(shadow, (thumb_container_x - shadow_offset, 
                            thumb_container_y - shadow_offset), shadow)
        
        # Main container
        container = create_rounded_square(thumb_container_size, 20, (40, 40, 40, 255))
        canvas.paste(container, (thumb_container_x, thumb_container_y), container)
        
        # Process and place thumbnail (smaller than container)
        thumb_size = 460
        thumb_x = thumb_container_x + (thumb_container_size - thumb_size) // 2
        thumb_y = thumb_container_y + (thumb_container_size - thumb_size) // 2
        
        # Resize thumbnail
        thumb = base_img.resize((thumb_size, thumb_size), Image.LANCZOS)
        
        # Create rounded mask for thumbnail
        thumb_mask = Image.new('L', (thumb_size, thumb_size), 0)
        thumb_mask_draw = ImageDraw.Draw(thumb_mask)
        thumb_mask_draw.rounded_rectangle([0, 0, thumb_size, thumb_size], 
                                        radius=15, fill=255)
        
        thumb.putalpha(thumb_mask)
        canvas.paste(thumb, (thumb_x, thumb_y), thumb)
        
        # Add play button overlay (red circle with triangle)
        play_button_size = 80
        play_x = thumb_x + (thumb_size - play_button_size) // 2
        play_y = thumb_y + (thumb_size - play_button_size) // 2
        
        play_circle = Image.new('RGBA', (play_button_size, play_button_size), (0, 0, 0, 0))
        play_draw = ImageDraw.Draw(play_circle)
        play_draw.ellipse([0, 0, play_button_size, play_button_size], fill=ACCENT_RED)
        
        # Play triangle
        triangle_points = [
            (play_button_size*0.4, play_button_size*0.3),
            (play_button_size*0.4, play_button_size*0.7),
            (play_button_size*0.7, play_button_size*0.5)
        ]
        play_draw.polygon(triangle_points, fill=TEXT_WHITE)
        
        canvas.paste(play_circle, (play_x, play_y), play_circle)

        # Content area (right side)
        content_x = thumb_container_x + thumb_container_size + 50
        content_width = CANVAS_W - content_x - 60
        
        # Branding/Channel name (top) - Like "Shemaroo Filmi Gaane" in reference
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
        brand_text = "@Allicemusic bot"
        brand_y = thumb_container_y + 30
        
        # Draw channel name with underline effect
        draw.text((content_x + 2, brand_y + 2), brand_text, 
                 fill=(0, 0, 0, 150), font=brand_font)
        draw.text((content_x, brand_y), brand_text, 
                 fill=ACCENT_BLUE, font=brand_font)
        
        # Underline
        brand_width = draw.textlength(brand_text, font=brand_font)
        draw.line([content_x, brand_y + 45, content_x + brand_width, brand_y + 45], 
                 fill=ACCENT_BLUE, width=2)

        # Title
        title_y = brand_y + 80
        title_font, title_wrapped = fit_title_font(
            draw, title, content_width, FONT_BOLD_PATH, 
            start_size=42, min_size=36
        )
        
        # Title with subtle shadow
        draw.text((content_x + 3, title_y + 3), title_wrapped, 
                 fill=(0, 0, 0, 100), font=title_font)
        draw.text((content_x, title_y), title_wrapped, 
                 fill=TEXT_WHITE, font=title_font)

        # Video info section
        info_y = title_y + 70
        
        # Channel name with icon
        channel_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        channel_text = f"• {channel}"
        draw.text((content_x, info_y), channel_text, 
                 fill=TEXT_LIGHT_GRAY, font=channel_font)

        # Views count
        views_y = info_y + 45
        views_text = f"{views}"
        draw.text((content_x, views_y), views_text, 
                 fill=TEXT_DARK_GRAY, font=channel_font)

        # Duration bar (like in reference image)
        duration_bar_y = views_y + 70
        duration_bar_width = content_width
        duration_bar_height = 6
        
        # Background bar
        draw.rounded_rectangle(
            [content_x, duration_bar_y, 
             content_x + duration_bar_width, duration_bar_y + duration_bar_height],
            radius=duration_bar_height//2, fill=(60, 60, 60, 255)
        )
        
        # Progress bar (green) - show some progress like in reference
        progress_width = int(duration_bar_width * 0.3)  # 30% progress
        draw.rounded_rectangle(
            [content_x, duration_bar_y, 
             content_x + progress_width, duration_bar_y + duration_bar_height],
            radius=duration_bar_height//2, fill=ACCENT_GREEN
        )
        
        # Time stamps
        time_font = ImageFont.truetype(FONT_REGULAR_PATH, 24)
        draw.text((content_x, duration_bar_y + 15), "00:00", 
                 fill=TEXT_LIGHT_GRAY, font=time_font)
        
        # Format duration properly
        formatted_duration = format_duration(duration)
        duration_width = draw.textlength(formatted_duration, font=time_font)
        draw.text((content_x + duration_bar_width - duration_width, duration_bar_y + 15), 
                 formatted_duration, fill=TEXT_LIGHT_GRAY, font=time_font)

        # Decorative elements (curves like in reference)
        # Top right curve
        curve_height = 80
        curve_overlay = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        curve_draw = ImageDraw.Draw(curve_overlay)
        
        # Draw curved shape at top right
        curve_points = [
            (CANVAS_W - 200, 0),
            (CANVAS_W, 0),
            (CANVAS_W, curve_height),
            (CANVAS_W - 150, curve_height + 30),
            (CANVAS_W - 300, curve_height)
        ]
        curve_draw.polygon(curve_points, fill=(40, 40, 40, 180))
        
        canvas = Image.alpha_composite(canvas, curve_overlay)
        
        # Bottom left decorative circle
        circle_size = 120
        circle_x = 20
        circle_y = CANVAS_H - circle_size - 20
        
        circle = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle)
        circle_draw.ellipse([0, 0, circle_size, circle_size], 
                          outline=ACCENT_RED, width=3)
        
        canvas.paste(circle, (circle_x, circle_y), circle)
        
        # YouTube-style info box
        info_box_y = duration_bar_y + 70
        info_box_height = 50
        
        # Info box background
        draw.rounded_rectangle(
            [content_x, info_box_y, 
             content_x + 300, info_box_y + info_box_height],
            radius=10, fill=(50, 50, 50, 255)
        )
        
        # Info text
        info_text = "Click to watch full video"
        info_font = ImageFont.truetype(FONT_REGULAR_PATH, 22)
        info_text_width = draw.textlength(info_text, font=info_font)
        info_text_x = content_x + (300 - info_text_width) // 2
        draw.text((info_text_x, info_box_y + 15), info_text, 
                 fill=TEXT_WHITE, font=info_font)

        # Add final curved overlay for depth
        canvas = add_curve_overlay(canvas, curve_height=40, color=(30, 30, 30, 100))

        # Save final thumbnail
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
                passCANVAS_W, CANVAS_H = 1280, 720

# Color scheme from the image
BACKGROUND_COLOR = (26, 26, 26, 255)  # Dark gray background
TEXT_WHITE = (255, 255, 255, 255)
TEXT_LIGHT_GRAY = (200, 200, 200, 255)
TEXT_DARK_GRAY = (150, 150, 150, 255)
ACCENT_RED = (255, 0, 0, 255)
ACCENT_GREEN = (0, 200, 83, 255)
ACCENT_BLUE = (66, 133, 244, 255)

FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB = "ShrutixMusic/assets/temp_thumb.jpg"

def change_image_size(max_w, max_h, image):
    try:
        ratio = min(max_w / image.size[0], max_h / image.size[1])
        return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)
    except Exception as e:
        print(f"[change_image_size Error] {e}")
        return image

def wrap_text_ellipsis(draw, text, font, max_width):
    """Wrap text and add ellipsis if too long"""
    try:
        if draw.textlength(text, font=font) <= max_width:
            return text
        
        ellipsis = "..."
        ellipsis_width = draw.textlength(ellipsis, font=font)
        
        result = ""
        for char in text:
            test = result + char + ellipsis
            if draw.textlength(test, font=font) <= max_width:
                result += char
            else:
                break
        
        return result + ellipsis if result else ellipsis
    except Exception as e:
        print(f"[wrap_text_ellipsis Error] {e}")
        return text[:30]

def fit_title_font(draw, text, max_width, font_path, start_size=48, min_size=36):
    """Find optimal font size for title"""
    try:
        size = start_size
        while size >= min_size:
            try:
                font = ImageFont.truetype(font_path, size)
            except:
                size -= 2
                continue
            
            wrapped = wrap_text_ellipsis(draw, text, font, max_width)
            if draw.textlength(wrapped, font=font) <= max_width:
                return font, wrapped
            size -= 2
        
        font = ImageFont.truetype(font_path, min_size)
        return font, wrap_text_ellipsis(draw, text, font, max_width)
    except Exception as e:
        print(f"[fit_title_font Error] {e}")
        try:
            font = ImageFont.truetype(font_path, min_size)
            return font, text[:40]
        except:
            return ImageFont.load_default(), text[:40]

def create_rounded_square(size, radius, color):
    """Create a rounded square/rectangle"""
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=color)
    return image

def add_curve_overlay(image, curve_height=60, color=(20, 20, 20, 200)):
    """Add curved overlay on top of image"""
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Draw curved shape
    width, height = image.size
    points = [
        (0, 0),
        (width, 0),
        (width, curve_height),
        (width//2 + 100, curve_height + 40),
        (width//2 - 100, curve_height + 40),
        (0, curve_height)
    ]
    
    draw.polygon(points, fill=color)
    
    # Blend with original image
    return Image.alpha_composite(image, overlay)

def format_duration(duration_str):
    """Format duration string"""
    if not duration_str or duration_str == "Unknown":
        return "0:00"
    
    # Remove any non-numeric characters except colon
    if ":" in duration_str:
        return duration_str
    elif duration_str.isdigit():
        minutes = int(duration_str) // 60
        seconds = int(duration_str) % 60
        return f"{minutes}:{seconds:02d}"
    else:
        return duration_str

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video data
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title    = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views    = result.get("viewCount", {}).get("short", "Unknown Views")
        channel  = result.get("channel", {}).get("name", "Unknown Channel")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Create canvas with dark gray background
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(canvas)

        # Add subtle texture/noise
        for i in range(1000):
            x = random.randint(0, CANVAS_W-1)
            y = random.randint(0, CANVAS_H-1)
            draw.point((x, y), fill=(30, 30, 30, 255))

        # Thumbnail container (rounded square on left side)
        thumb_container_size = 500
        thumb_container_x = 60
        thumb_container_y = (CANVAS_H - thumb_container_size) // 2
        
        # Container with shadow
        shadow_offset = 8
        shadow = create_rounded_square(thumb_container_size + shadow_offset*2, 
                                     30, (0, 0, 0, 100))
        canvas.paste(shadow, (thumb_container_x - shadow_offset, 
                            thumb_container_y - shadow_offset), shadow)
        
        # Main container
        container = create_rounded_square(thumb_container_size, 20, (40, 40, 40, 255))
        canvas.paste(container, (thumb_container_x, thumb_container_y), container)
        
        # Process and place thumbnail (smaller than container)
        thumb_size = 460
        thumb_x = thumb_container_x + (thumb_container_size - thumb_size) // 2
        thumb_y = thumb_container_y + (thumb_container_size - thumb_size) // 2
        
        # Resize thumbnail
        thumb = base_img.resize((thumb_size, thumb_size), Image.LANCZOS)
        
        # Create rounded mask for thumbnail
        thumb_mask = Image.new('L', (thumb_size, thumb_size), 0)
        thumb_mask_draw = ImageDraw.Draw(thumb_mask)
        thumb_mask_draw.rounded_rectangle([0, 0, thumb_size, thumb_size], 
                                        radius=15, fill=255)
        
        thumb.putalpha(thumb_mask)
        canvas.paste(thumb, (thumb_x, thumb_y), thumb)
        
        # Add play button overlay (red circle with triangle)
        play_button_size = 80
        play_x = thumb_x + (thumb_size - play_button_size) // 2
        play_y = thumb_y + (thumb_size - play_button_size) // 2
        
        play_circle = Image.new('RGBA', (play_button_size, play_button_size), (0, 0, 0, 0))
        play_draw = ImageDraw.Draw(play_circle)
        play_draw.ellipse([0, 0, play_button_size, play_button_size], fill=ACCENT_RED)
        
        # Play triangle
        triangle_size = 30
        triangle_points = [
            (play_button_size*0.4, play_button_size*0.3),
            (play_button_size*0.4, play_button_size*0.7),
            (play_button_size*0.7, play_button_size*0.5)
        ]
        play_draw.polygon(triangle_points, fill=TEXT_WHITE)
        
        canvas.paste(play_circle, (play_x, play_y), play_circle)

        # Content area (right side)
        content_x = thumb_container_x + thumb_container_size + 50
        content_width = CANVAS_W - content_x - 60
        
        # Branding/Channel name (top)
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
        brand_text = "@Allicemusic bot"
        brand_y = thumb_container_y + 30
        
        # Draw channel name with underline effect
        draw.text((content_x + 2, brand_y + 2), brand_text, 
                 fill=(0, 0, 0, 150), font=brand_font)
        draw.text((content_x, brand_y), brand_text, 
                 fill=ACCENT_BLUE, font=brand_font)
        
        # Underline
        brand_width = draw.textlength(brand_text, font=brand_font)
        draw.line([content_x, brand_y + 45, content_x + brand_width, brand_y + 45], 
                 fill=ACCENT_BLUE, width=2)

        # Title
        title_y = brand_y + 80
        title_font, title_wrapped = fit_title_font(
            draw, title, content_width, FONT_BOLD_PATH, 
            start_size=42, min_size=36
        )
        
        # Title with subtle shadow
        draw.text((content_x + 3, title_y + 3), title_wrapped, 
                 fill=(0, 0, 0, 100), font=title_font)
        draw.text((content_x, title_y), title_wrapped, 
                 fill=TEXT_WHITE, font=title_font)

        # Video info section
        info_y = title_y + 70
        
        # Channel name with icon
        channel_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        channel_text = f"• {channel}"
        draw.text((content_x, info_y), channel_text, 
                 fill=TEXT_LIGHT_GRAY, font=channel_font)

        # Views count
        views_y = info_y + 45
        views_text = f"{views}"
        draw.text((content_x, views_y), views_text, 
                 fill=TEXT_DARK_GRAY, font=channel_font)

        # Duration bar (like in reference image)
        duration_bar_y = views_y + 70
        duration_bar_width = content_width
        duration_bar_height = 6
        
        # Background bar
        draw.rounded_rectangle(
            [content_x, duration_bar_y, 
             content_x + duration_bar_width, duration_bar_y + duration_bar_height],
            radius=duration_bar_height//2, fill=(60, 60, 60, 255)
        )
        
        # Progress bar (green)
        progress_width = int(duration_bar_width * 0.3)  # 30% progress
        draw.rounded_rectangle(
            [content_x, duration_bar_y, 
             content_x + progress_width, duration_bar_y + duration_bar_height],
            radius=duration_bar_height//2, fill=ACCENT_GREEN
        )
        
        # Time stamps
        time_font = ImageFont.truetype(FONT_REGULAR_PATH, 24)
        draw.text((content_x, duration_bar_y + 15), "00:00", 
                 fill=TEXT_LIGHT_GRAY, font=time_font)
        
        # Format duration properly
        formatted_duration = format_duration(duration)
        duration_width = draw.textlength(formatted_duration, font=time_font)
        draw.text((content_x + duration_bar_width - duration_width, duration_bar_y + 15), 
                 formatted_duration, fill=TEXT_LIGHT_GRAY, font=time_font)

        # Decorative elements (curves like in reference)
        # Top right curve
        curve_height = 80
        curve_overlay = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        curve_draw = ImageDraw.Draw(curve_overlay)
        
        # Draw curved shape at top right
        curve_points = [
            (CANVAS_W - 200, 0),
            (CANVAS_W, 0),
            (CANVAS_W, curve_height),
            (CANVAS_W - 150, curve_height + 30),
            (CANVAS_W - 300, curve_height)
        ]
        curve_draw.polygon(curve_points, fill=(40, 40, 40, 180))
        
        canvas = Image.alpha_composite(canvas, curve_overlay)
        
        # Bottom left decorative circle
        circle_size = 120
        circle_x = 20
        circle_y = CANVAS_H - circle_size - 20
        
        circle = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle)
        circle_draw.ellipse([0, 0, circle_size, circle_size], 
                          outline=ACCENT_RED, width=3)
        
        canvas.paste(circle, (circle_x, circle_y), circle)
        
        # YouTube-style info box
        info_box_y = duration_bar_y + 70
        info_box_height = 50
        
        # Info box background
        draw.rounded_rectangle(
            [content_x, info_box_y, 
             content_x + 300, info_box_y + info_box_height],
            radius=10, fill=(50, 50, 50, 255)
        )
        
        # Info text
        info_text = "Click to watch full video"
        info_font = ImageFont.truetype(FONT_REGULAR_PATH, 22)
        info_text_width = draw.textlength(info_text, font=info_font)
        info_text_x = content_x + (300 - info_text_width) // 2
        draw.text((info_text_x, info_box_y + 15), info_text, 
                 fill=TEXT_WHITE, font=info_font)

        # Add final curved overlay for depth
        canvas = add_curve_overlay(canvas, curve_height=40, color=(30, 30, 30, 100))

        # Save final thumbnail
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

# Add random import for texture
import randomCANVAS_W, CANVAS_H = 1280, 720

# Modern color palette
PRIMARY_COLOR = (144, 238, 144, 255)  # Light green
SECONDARY_COLOR = (30, 144, 255, 255)  # Dodger blue
ACCENT_COLOR = (255, 105, 180, 255)    # Hot pink
BACKGROUND_COLOR = (20, 20, 30, 255)   # Dark blue-gray
TEXT_WHITE = (245, 245, 245, 255)
TEXT_GRAY = (200, 200, 200, 255)
GLOW_COLOR = (144, 238, 144, 100)      # Light green with transparency

FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB = "ShrutixMusic/assets/temp_thumb.jpg"

def change_image_size(max_w, max_h, image):
    try:
        ratio = min(max_w / image.size[0], max_h / image.size[1])
        return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)
    except Exception as e:
        print(f"[change_image_size Error] {e}")
        return image

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text to fit within max_width, limiting to max_lines"""
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
                    # Single word too long, truncate
                    lines.append(word[:20] + "...")
                    break
                    
                if len(lines) >= max_lines:
                    # Add ellipsis to last line if we hit max lines
                    if len(lines) == max_lines:
                        last_line = lines[-1]
                        while draw.textlength(last_line + " ...", font=font) > max_width and len(last_line) > 3:
                            last_line = last_line[:-1]
                        lines[-1] = last_line + " ..."
                    break
        
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    except Exception as e:
        print(f"[wrap_text Error] {e}")
        return text[:50]

def fit_title_text(draw, text, max_width, font_path, max_lines=2, start_size=42, min_size=28):
    """Find optimal font size for title text"""
    try:
        size = start_size
        while size >= min_size:
            try:
                font = ImageFont.truetype(font_path, size)
            except:
                size -= 2
                continue
            
            wrapped = wrap_text(draw, text, font, max_width, max_lines)
            lines = wrapped.split('\n')
            
            if len(lines) <= max_lines and all(draw.textlength(line, font=font) <= max_width for line in lines):
                return font, wrapped
            size -= 2
        
        # Fallback to minimum size
        font = ImageFont.truetype(font_path, min_size)
        return font, wrap_text(draw, text, font, max_width, max_lines)
    except Exception as e:
        print(f"[fit_title_text Error] {e}")
        try:
            font = ImageFont.truetype(font_path, min_size)
            return font, text[:40]
        except:
            return ImageFont.load_default(), text[:40]

def add_corners(image, radius):
    """Add rounded corners to image"""
    try:
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        
        # Draw rounded rectangle mask
        draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
        
        # Apply mask
        result = image.copy()
        result.putalpha(mask)
        return result
    except Exception as e:
        print(f"[add_corners Error] {e}")
        return image

def create_gradient(width, height, color1, color2, horizontal=True):
    """Create a gradient background"""
    try:
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        
        mask = Image.new('L', (width, height))
        mask_data = []
        
        for y in range(height):
            if horizontal:
                alpha = int(255 * y / height)
            else:
                alpha = int(255 * y / height)
            mask_data.extend([alpha] * width)
        
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base.convert('RGBA')
    except Exception as e:
        print(f"[create_gradient Error] {e}")
        return Image.new('RGBA', (width, height), color1)

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video data
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title    = result.get("title", "Unknown Title")
        duration = result.get("duration", "Unknown")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views    = result.get("viewCount", {}).get("short", "Unknown Views")
        channel  = result.get("channel", {}).get("name", "Unknown Channel")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

        # Create modern background with gradient
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(canvas)
        
        # Add subtle gradient overlay
        gradient = create_gradient(CANVAS_W, CANVAS_H, (30, 30, 45), (20, 20, 30))
        canvas.paste(gradient, (0, 0), gradient)

        # Add decorative elements
        # Top decorative bar
        draw.rectangle([0, 0, CANVAS_W, 8], fill=PRIMARY_COLOR)
        
        # Bottom decorative bar
        draw.rectangle([0, CANVAS_H-8, CANVAS_W, CANVAS_H], fill=SECONDARY_COLOR)
        
        # Left decorative accent
        draw.rectangle([0, 0, 12, CANVAS_H], fill=ACCENT_COLOR)

        # Process and place thumbnail image (left side)
        thumb_size = 380
        padding = 40
        
        # Resize and round corners for thumbnail
        thumb = base_img.resize((thumb_size, thumb_size), Image.LANCZOS)
        thumb = add_corners(thumb, 25)
        
        # Add border to thumbnail
        bordered_thumb = Image.new('RGBA', (thumb_size + 10, thumb_size + 10), PRIMARY_COLOR)
        bordered_thumb.paste(thumb, (5, 5), thumb)
        bordered_thumb = add_corners(bordered_thumb, 30)
        
        # Add shadow effect
        shadow_offset = 8
        shadow_layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(
            [padding + shadow_offset, padding + shadow_offset + 40,
             padding + thumb_size + 10 + shadow_offset, padding + thumb_size + 10 + shadow_offset + 40],
            radius=30, fill=(0, 0, 0, 100)
        )
        canvas = Image.alpha_composite(canvas, shadow_layer)
        
        # Place thumbnail on canvas
        canvas.paste(bordered_thumb, (padding, padding + 40), bordered_thumb)

        # Add play button overlay on thumbnail
        play_size = 80
        play_x = padding + (thumb_size - play_size) // 2
        play_y = padding + 40 + (thumb_size - play_size) // 2
        
        play_circle = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 150))
        play_draw = ImageDraw.Draw(play_circle)
        play_draw.ellipse([0, 0, play_size, play_size], fill=(255, 255, 255, 180))
        
        # Draw play triangle
        triangle_points = [
            (play_size*0.35, play_size*0.25),
            (play_size*0.35, play_size*0.75),
            (play_size*0.75, play_size*0.5)
        ]
        play_draw.polygon(triangle_points, fill=PRIMARY_COLOR)
        
        play_circle = play_circle.filter(ImageFilter.GaussianBlur(2))
        canvas.paste(play_circle, (play_x, play_y), play_circle)

        # Branding text (top right)
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 36)
        brand_text = "@Allicemusic bot"
        brand_width = draw.textlength(brand_text, font=brand_font)
        brand_x = CANVAS_W - brand_width - 40
        brand_y = 30
        
        # Branding with glow effect
        for offset in range(3, 0, -1):
            draw.text((brand_x+offset, brand_y+offset), brand_text, 
                     fill=(255, 255, 255, 30), font=brand_font)
        draw.text((brand_x, brand_y), brand_text, fill=PRIMARY_COLOR, font=brand_font)

        # Content area (right side)
        content_x = padding + thumb_size + padding + 40
        content_width = CANVAS_W - content_x - padding
        
        # Now Playing badge
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 28)
        np_text = "NOW PLAYING"
        np_width = draw.textlength(np_text, font=np_font)
        np_x = content_x
        np_y = padding + 40
        
        # Badge background
        badge_height = 45
        draw.rounded_rectangle(
            [np_x, np_y, np_x + np_width + 40, np_y + badge_height],
            radius=badge_height//2, fill=PRIMARY_COLOR
        )
        
        # Badge text
        draw.text((np_x + 20, np_y + badge_height//2 - 10), 
                 np_text, fill=(20, 20, 30), font=np_font)

        # Title
        title_y = np_y + badge_height + 30
        title_font, title_wrapped = fit_title_text(
            draw, title, content_width - 20, FONT_BOLD_PATH, 
            max_lines=2, start_size=36, min_size=28
        )
        
        # Title with shadow
        draw.multiline_text((content_x + 2, title_y + 2), 
                           title_wrapped, fill=(0, 0, 0, 100), 
                           font=title_font, spacing=8)
        draw.multiline_text((content_x, title_y), 
                           title_wrapped, fill=TEXT_WHITE, 
                           font=title_font, spacing=8)

        # Metadata section
        meta_y = title_y + 100
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 26)
        icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        
        # Channel info
        channel_icon = "📺"
        draw.text((content_x, meta_y), channel_icon, fill=ACCENT_COLOR, font=icon_font)
        draw.text((content_x + 40, meta_y), f"Channel: {channel}", 
                 fill=TEXT_GRAY, font=meta_font)
        
        # Views info
        views_icon = "👁️"
        draw.text((content_x, meta_y + 50), views_icon, fill=SECONDARY_COLOR, font=icon_font)
        draw.text((content_x + 40, meta_y + 50), f"Views: {views}", 
                 fill=TEXT_GRAY, font=meta_font)
        
        # Duration info
        duration_icon = "⏱️"
        draw.text((content_x, meta_y + 100), duration_icon, fill=PRIMARY_COLOR, font=icon_font)
        draw.text((content_x + 40, meta_y + 100), f"Duration: {duration}", 
                 fill=TEXT_GRAY, font=meta_font)

        # Add decorative elements
        # Right side decorative line
        draw.line([CANVAS_W - 12, 0, CANVAS_W - 12, CANVAS_H], 
                 fill=PRIMARY_COLOR, width=3)
        
        # Bottom left decorative circle
        circle_radius = 60
        circle_x = 30
        circle_y = CANVAS_H - 30 - circle_radius
        draw.ellipse([circle_x, circle_y, 
                     circle_x + circle_radius*2, circle_y + circle_radius*2],
                    outline=SECONDARY_COLOR, width=3)

        # Save final thumbnail
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
                passBG_BLUR = 16
BG_BRIGHTNESS = 1  

LIME_BORDER = (158, 255, 49, 255)
RING_COLOR  = (98, 193, 169, 255)
TEXT_WHITE  = (245, 245, 245, 255)
TEXT_SOFT   = (230, 230, 230, 255)
TEXT_SHADOW = (0, 0, 0, 140)

FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH    = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB    = "ShrutixMusic/assets/temp_thumb.jpg"

FONT_REGULAR = ImageFont.truetype(FONT_REGULAR_PATH, 30)
FONT_BOLD    = ImageFont.truetype(FONT_BOLD_PATH, 30)


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
        return text[:50]  # Return truncated text as fallback


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

        tl_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
        draw.text((28+1, 18+1), "ShrutixMusic", fill=TEXT_SHADOW, font=tl_font)
        draw.text((28, 18), "ShrutixMusic", fill=TEXT_WHITE, font=tl_font)

        info_x = circle_x + thumb_size + 60
        max_text_w = CANVAS_W - info_x - 48

        np_font = ImageFont.truetype(FONT_BOLD_PATH, 60)
        np_text = "NOW PLAYING"
        np_w = draw.textlength(np_text, font=np_font)
        np_x = info_x + (max_text_w - np_w) // 2 - 95
        np_y = circle_y + 30  
        draw.text((np_x+2, np_y+2), np_text, fill=TEXT_SHADOW, font=np_font)
        draw.text((np_x, np_y), np_text, fill=TEXT_WHITE, font=np_font)

        title_font, title_wrapped = fit_title_two_lines(draw, title, max_text_w, FONT_BOLD_PATH, start_size=30, min_size=30)
        title_y = np_y + 110   
        draw.multiline_text((info_x+2, title_y+2), title_wrapped, fill=TEXT_SHADOW, font=title_font, spacing=8)
        draw.multiline_text((info_x, title_y),     title_wrapped, fill=TEXT_WHITE,  font=title_font, spacing=8)

        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        line_gap = 46
        meta_start_y = title_y + 130  
        duration_label = duration
        if duration and ":" in duration and "Min" not in duration and "min" not in duration:
            duration_label = f"{duration} Mins"

        def draw_meta(y, text):
            draw.text((info_x+1, y+1), text, fill=TEXT_SHADOW, font=meta_font)
            draw.text((info_x,   y),   text, fill=TEXT_SOFT,  font=meta_font)

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


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi
# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutixMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================
