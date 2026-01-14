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

# Modern colors
BG_COLOR = (15, 15, 25, 255)
TEXT_WHITE = (255, 255, 255, 255)
TEXT_GRAY = (200, 200, 200, 255)
ACCENT_BLUE = (30, 144, 255, 255)
ACCENT_PINK = (255, 105, 180, 255)
ACCENT_GREEN = (57, 255, 20, 255)
NEON_PURPLE = (147, 112, 219, 255)

# Font paths
FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB = "ShrutixMusic/assets/temp_thumb.jpg"

async def get_thumb(videoid: str):
    """Generate simple thumbnail with 4 lines of YouTube details"""
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch YouTube data
        print(f"[INFO] Fetching data for video: {videoid}")
        results = VideosSearch(url, limit=1)
        data = await results.next()
        
        if not data or "result" not in data or len(data["result"]) == 0:
            print("[ERROR] No video data found")
            return FALLBACK_THUMB if os.path.exists(FALLBACK_THUMB) else None
            
        result = data["result"][0]
        
        # Extract data with defaults
        title = result.get("title", "Unknown Song")
        duration = result.get("duration", "0:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0] if result.get("thumbnails") else ""
        views = result.get("viewCount", {}).get("short", "0 views")
        
        print(f"[INFO] Title: {title}")
        print(f"[INFO] Duration: {duration}")
        print(f"[INFO] Views: {views}")
        
        # Download thumbnail
        if thumburl:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(thumburl) as resp:
                        if resp.status == 200:
                            thumb_path = CACHE_DIR / f"thumb_{videoid}.jpg"
                            async with aiofiles.open(thumb_path, "wb") as f:
                                await f.write(await resp.read())
                            print(f"[INFO] Thumbnail downloaded successfully")
            except Exception as e:
                print(f"[WARNING] Could not download thumbnail: {e}")
        
        # Create canvas
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
        draw = ImageDraw.Draw(canvas)
        
        # Load YouTube thumbnail for background (blurred)
        if thumb_path and os.path.exists(thumb_path):
            try:
                bg_img = Image.open(thumb_path).convert("RGBA")
                # Resize for background
                bg_img = bg_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
                # Apply blur
                bg_img = bg_img.filter(ImageFilter.GaussianBlur(20))
                # Darken for readability
                enhancer = ImageEnhance.Brightness(bg_img)
                bg_img = enhancer.enhance(0.4)
                # Add dark overlay
                overlay = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 150))
                bg_img = Image.alpha_composite(bg_img, overlay)
                # Paste background
                canvas.paste(bg_img, (0, 0))
            except Exception as e:
                print(f"[WARNING] Could not process background: {e}")
        
        # Main content container (glass effect)
        container_width = 1000
        container_height = 500
        container_x = (CANVAS_W - container_width) // 2
        container_y = (CANVAS_H - container_height) // 2
        
        # Create glass effect container
        glass = Image.new('RGBA', (container_width, container_height), (255, 255, 255, 30))
        glass = glass.filter(ImageFilter.GaussianBlur(10))
        canvas.paste(glass, (container_x, container_y), glass)
        
        # Container border
        draw.rounded_rectangle(
            [container_x, container_y, 
             container_x + container_width, container_y + container_height],
            radius=25,
            outline=(255, 255, 255, 80),
            width=3
        )
        
        # YouTube thumbnail preview (left side)
        thumb_size = 350
        thumb_x = container_x + 50
        thumb_y = container_y + (container_height - thumb_size) // 2
        
        if thumb_path and os.path.exists(thumb_path):
            try:
                thumb_img = Image.open(thumb_path).convert("RGBA")
                thumb_img = thumb_img.resize((thumb_size, thumb_size), Image.LANCZOS)
                
                # Add rounded corners
                mask = Image.new('L', (thumb_size, thumb_size), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([0, 0, thumb_size, thumb_size], radius=20, fill=255)
                thumb_img.putalpha(mask)
                
                # Add border
                border_size = thumb_size + 10
                border = Image.new('RGBA', (border_size, border_size), ACCENT_BLUE)
                border_mask = Image.new('L', (border_size, border_size), 0)
                border_draw = ImageDraw.Draw(border_mask)
                border_draw.rounded_rectangle([0, 0, border_size, border_size], radius=25, fill=255)
                border.putalpha(border_mask)
                
                canvas.paste(border, (thumb_x - 5, thumb_y - 5), border)
                canvas.paste(thumb_img, (thumb_x, thumb_y), thumb_img)
                
                # Play button
                play_size = 60
                play_x = thumb_x + (thumb_size - play_size) // 2
                play_y = thumb_y + (thumb_size - play_size) // 2
                
                play_bg = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 180))
                play_draw = ImageDraw.Draw(play_bg)
                play_draw.ellipse([0, 0, play_size, play_size], fill=ACCENT_PINK)
                
                # Play triangle
                triangle_points = [
                    (play_size * 0.35, play_size * 0.25),
                    (play_size * 0.35, play_size * 0.75),
                    (play_size * 0.75, play_size * 0.5)
                ]
                play_draw.polygon(triangle_points, fill=TEXT_WHITE)
                
                canvas.paste(play_bg, (play_x, play_y), play_bg)
                
            except Exception as e:
                print(f"[WARNING] Could not display thumbnail: {e}")
                # Draw placeholder
                draw.rounded_rectangle(
                    [thumb_x, thumb_y, thumb_x + thumb_size, thumb_y + thumb_size],
                    radius=20,
                    fill=(40, 40, 60, 255)
                )
        
        # Content area (right side - 4 lines)
        content_x = thumb_x + thumb_size + 60
        content_width = container_width - (content_x - container_x) - 50
        
        # Try to load custom fonts, fallback to default
        try:
            title_font = ImageFont.truetype(FONT_BOLD_PATH, 48)
            detail_font = ImageFont.truetype(FONT_REGULAR_PATH, 36)
            bot_font = ImageFont.truetype(FONT_BOLD_PATH, 40)
        except:
            print("[WARNING] Using default fonts")
            title_font = ImageFont.load_default()
            detail_font = ImageFont.load_default()
            bot_font = ImageFont.load_default()
        
        # Line 1: YouTube Song Name (Title)
        line1_y = thumb_y + 30
        
        # Wrap title if too long
        title_text = title
        max_title_width = content_width - 20
        
        # Simple title wrapping
        if draw.textlength(title_text, font=title_font) > max_title_width:
            words = title_text.split()
            new_title = ""
            for word in words:
                test = f"{new_title} {word}".strip()
                if draw.textlength(test, font=title_font) <= max_title_width:
                    new_title = test
                else:
                    if new_title:
                        title_text = new_title + "..."
                    else:
                        title_text = title_text[:20] + "..."
                    break
        
        # Draw title with shadow
        draw.text((content_x + 3, line1_y + 3), title_text, 
                 fill=(0, 0, 0, 150), font=title_font)
        draw.text((content_x, line1_y), title_text, 
                 fill=TEXT_WHITE, font=title_font)
        
        # Line 2: Duration
        line2_y = line1_y + 80
        duration_text = f"⏱️ Duration: {duration}"
        
        draw.text((content_x + 2, line2_y + 2), duration_text, 
                 fill=(0, 0, 0, 150), font=detail_font)
        draw.text((content_x, line2_y), duration_text, 
                 fill=ACCENT_GREEN, font=detail_font)
        
        # Line 3: Views
        line3_y = line2_y + 60
        views_text = f"👁️ Views: {views}"
        
        draw.text((content_x + 2, line3_y + 2), views_text, 
                 fill=(0, 0, 0, 150), font=detail_font)
        draw.text((content_x, line3_y), views_text, 
                 fill=ACCENT_BLUE, font=detail_font)
        
        # Line 4: @Allicemusicbot
        line4_y = line3_y + 60
        bot_text = f"🎵 @Allicemusicbot"
        
        draw.text((content_x + 2, line4_y + 2), bot_text, 
                 fill=(0, 0, 0, 150), font=bot_font)
        draw.text((content_x, line4_y), bot_text, 
                 fill=ACCENT_PINK, font=bot_font)
        
        # Add decorative elements
        
        # Now Playing badge at top
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 32) if os.path.exists(FONT_BOLD_PATH) else ImageFont.load_default()
        np_text = "▶ NOW PLAYING"
        np_width = draw.textlength(np_text, font=np_font)
        np_x = container_x + (container_width - np_width) // 2
        np_y = container_y + 20
        
        # Badge background
        badge_bg = Image.new('RGBA', (int(np_width) + 40, 50), ACCENT_PINK)
        badge_mask = Image.new('L', (int(np_width) + 40, 50), 0)
        badge_draw = ImageDraw.Draw(badge_mask)
        badge_draw.rounded_rectangle([0, 0, int(np_width) + 40, 50], radius=25, fill=255)
        badge_bg.putalpha(badge_mask)
        
        canvas.paste(badge_bg, (np_x - 20, np_y - 10), badge_bg)
        draw.text((np_x, np_y), np_text, fill=TEXT_WHITE, font=np_font)
        
        # Add decorative music notes
        note_font = ImageFont.truetype(FONT_BOLD_PATH, 60) if os.path.exists(FONT_BOLD_PATH) else ImageFont.load_default()
        
        # Top left note
        draw.text((container_x + 30, container_y + 30), "♪", 
                 fill=(ACCENT_BLUE[0], ACCENT_BLUE[1], ACCENT_BLUE[2], 100), 
                 font=note_font)
        
        # Bottom right note
        draw.text((container_x + container_width - 80, container_y + container_height - 80), "♫", 
                 fill=(ACCENT_PINK[0], ACCENT_PINK[1], ACCENT_PINK[2], 100), 
                 font=note_font)
        
        # Add subtle gradient overlay at bottom
        gradient = Image.new('RGBA', (CANVAS_W, 100), (0, 0, 0, 0))
        gradient_draw = ImageDraw.Draw(gradient)
        for i in range(100):
            alpha = int(100 * (i / 100))
            gradient_draw.line([(0, CANVAS_H - 100 + i), (CANVAS_W, CANVAS_H - 100 + i)], 
                              fill=(0, 0, 0, alpha))
        
        canvas = Image.alpha_composite(canvas, gradient)
        
        # Save final thumbnail
        out = CACHE_DIR / f"{videoid}_simple.png"
        canvas.save(out, "PNG", quality=95)
        print(f"[SUCCESS] Thumbnail saved: {out}")
        
        # Clean up
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except:
                pass
        
        return str(out)
        
    except Exception as e:
        print(f"[ERROR] get_thumb failed: {e}")
        traceback.print_exc()
        
        # Fallback
        if os.path.exists(FALLBACK_THUMB):
            print("[FALLBACK] Using default thumbnail")
            return FALLBACK_THUMB
        
        return None
