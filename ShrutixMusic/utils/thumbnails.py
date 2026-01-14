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

# Modern music theme colors
GRADIENT_START = (30, 144, 255, 255)    # Dodger Blue
GRADIENT_END = (138, 43, 226, 255)      # Blue Violet
ACCENT_PURPLE = (147, 112, 219, 255)    # Medium Purple
ACCENT_PINK = (255, 105, 180, 255)      # Hot Pink
ACCENT_GREEN = (50, 205, 50, 255)       # Lime Green
TEXT_WHITE = (255, 255, 255, 255)
TEXT_LIGHT = (230, 230, 230, 255)
TEXT_SHADOW = (20, 20, 20, 200)
NEON_BLUE = (0, 191, 255, 255)
NEON_PINK = (255, 20, 147, 255)

# Font paths
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

def create_gradient(width, height, color1, color2, horizontal=False):
    """Create a smooth gradient background"""
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

def add_rounded_corners(image, radius):
    """Add rounded corners to image"""
    try:
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius=radius, fill=255)
        
        result = image.copy()
        result.putalpha(mask)
        return result
    except Exception as e:
        print(f"[add_rounded_corners Error] {e}")
        return image

def add_modern_shadow(image, offset=8, blur_radius=15, shadow_color=(0, 0, 0, 100)):
    """Add modern shadow effect"""
    try:
        shadow = Image.new('RGBA', 
                          (image.size[0] + offset*2, image.size[1] + offset*2), 
                          (0, 0, 0, 0))
        
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [offset, offset, 
             image.size[0] + offset, image.size[1] + offset],
            radius=25,
            fill=shadow_color
        )
        
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
        return shadow
    except Exception as e:
        print(f"[add_modern_shadow Error] {e}")
        return image

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text with ellipsis if too long"""
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
                    # Add ellipsis to last line
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

def fit_title_font(draw, text, max_width, font_path, max_lines=2, start_size=42, min_size=32):
    """Find optimal font size for title"""
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
        
        font = ImageFont.truetype(font_path, min_size)
        return font, wrap_text(draw, text, font, max_width, max_lines)
    except Exception as e:
        print(f"[fit_title_font Error] {e}")
        try:
            font = ImageFont.truetype(font_path, min_size)
            return font, text[:40]
        except:
            return ImageFont.load_default(), text[:40]

def add_glow_effect(draw, text, position, font, glow_color, iterations=3):
    """Add glow effect to text"""
    x, y = position
    for i in range(iterations, 0, -1):
        offset = i
        alpha = 100 // (i * 2)
        glow_color_with_alpha = (glow_color[0], glow_color[1], glow_color[2], alpha)
        draw.text((x + offset, y + offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x - offset, y + offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x + offset, y - offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x - offset, y - offset), text, fill=glow_color_with_alpha, font=font)

def create_music_visualizer(width, height, count=20):
    """Create decorative music visualizer bars"""
    try:
        visualizer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(visualizer)
        
        bar_width = width // (count * 2)
        spacing = bar_width
        
        colors = [ACCENT_PURPLE, ACCENT_PINK, NEON_BLUE, ACCENT_GREEN, NEON_PINK]
        
        for i in range(count):
            x = i * (bar_width + spacing) + spacing
            # Random height for dynamic look
            bar_height = random.randint(height // 4, height - 50)
            bar_y = height - bar_height
            
            color = colors[i % len(colors)]
            
            # Draw bar with gradient
            for h in range(bar_height):
                alpha = int(255 * (h / bar_height))
                draw.rectangle(
                    [x, bar_y + h, x + bar_width, bar_y + h + 1],
                    fill=(color[0], color[1], color[2], alpha)
                )
        
        return visualizer
    except Exception as e:
        print(f"[create_music_visualizer Error] {e}")
        return Image.new('RGBA', (width, height), (0, 0, 0, 0))

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video data
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

        # Create canvas with gradient background
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        
        # Add gradient background
        gradient = create_gradient(CANVAS_W, CANVAS_H, 
                                 GRADIENT_START[:3], 
                                 GRADIENT_END[:3])
        canvas.paste(gradient, (0, 0))
        
        draw = ImageDraw.Draw(canvas)
        
        # Add decorative music visualizer at bottom
        visualizer_height = 120
        visualizer = create_music_visualizer(CANVAS_W, visualizer_height)
        canvas.paste(visualizer, (0, CANVAS_H - visualizer_height), visualizer)
        
        # Add curved overlay for depth
        overlay = Image.new('RGBA', (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Create curved shape for design
        curve_points = [
            (0, CANVAS_H),
            (CANVAS_W, CANVAS_H),
            (CANVAS_W, CANVAS_H - 150),
            (CANVAS_W // 2 + 200, CANVAS_H - 250),
            (CANVAS_W // 2 - 200, CANVAS_H - 250),
            (0, CANVAS_H - 150)
        ]
        overlay_draw.polygon(curve_points, fill=(0, 0, 0, 50))
        
        # Add second smaller curve
        curve_points2 = [
            (0, CANVAS_H),
            (CANVAS_W, CANVAS_H),
            (CANVAS_W, CANVAS_H - 100),
            (CANVAS_W // 2 + 150, CANVAS_H - 180),
            (CANVAS_W // 2 - 150, CANVAS_H - 180),
            (0, CANVAS_H - 100)
        ]
        overlay_draw.polygon(curve_points2, fill=(0, 0, 0, 30))
        
        canvas = Image.alpha_composite(canvas, overlay)
        
        # Prepare thumbnail (square with rounded corners)
        thumb_size = 400
        thumb_padding = 60
        thumb_x = thumb_padding
        thumb_y = (CANVAS_H - thumb_size) // 2
        
        # Resize and crop thumbnail to square
        thumb = base_img.resize((thumb_size, thumb_size), Image.LANCZOS)
        
        # Add rounded corners to thumbnail
        thumb = add_rounded_corners(thumb, 30)
        
        # Add modern shadow
        shadow = add_modern_shadow(thumb, offset=12, blur_radius=20)
        shadow_x = thumb_x - 12
        shadow_y = thumb_y - 12
        canvas.paste(shadow, (shadow_x, shadow_y), shadow)
        
        # Place thumbnail with decorative border
        border_size = thumb_size + 10
        border = Image.new('RGBA', (border_size, border_size), ACCENT_PURPLE)
        border = add_rounded_corners(border, 35)
        canvas.paste(border, (thumb_x - 5, thumb_y - 5), border)
        
        # Place thumbnail
        canvas.paste(thumb, (thumb_x, thumb_y), thumb)
        
        # Add play button overlay
        play_size = 80
        play_x = thumb_x + (thumb_size - play_size) // 2
        play_y = thumb_y + (thumb_size - play_size) // 2
        
        play_bg = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 150))
        play_draw = ImageDraw.Draw(play_bg)
        play_draw.ellipse([0, 0, play_size, play_size], fill=NEON_PINK)
        
        # Play triangle
        triangle_points = [
            (play_size * 0.35, play_size * 0.25),
            (play_size * 0.35, play_size * 0.75),
            (play_size * 0.75, play_size * 0.5)
        ]
        play_draw.polygon(triangle_points, fill=TEXT_WHITE)
        
        play_bg = play_bg.filter(ImageFilter.GaussianBlur(2))
        canvas.paste(play_bg, (play_x, play_y), play_bg)
        
        # Content area (right side)
        content_x = thumb_x + thumb_size + 80
        content_width = CANVAS_W - content_x - 60
        
        # Branding/Logo
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 36)
        brand_text = "🎵 Shrutix Music"
        brand_y = thumb_y - 10
        
        # Add glow effect to branding
        add_glow_effect(draw, brand_text, (content_x, brand_y), brand_font, NEON_BLUE)
        draw.text((content_x, brand_y), brand_text, fill=TEXT_WHITE, font=brand_font)
        
        # "NOW PLAYING" badge
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 28)
        np_text = "▶️ NOW PLAYING"
        np_width = draw.textlength(np_text, font=np_font)
        np_x = content_x
        np_y = brand_y + 60
        
        # Badge background
        badge_padding = 20
        badge_height = 45
        badge_bg = Image.new('RGBA', (int(np_width) + badge_padding * 2, badge_height), (0, 0, 0, 0))
        badge_draw = ImageDraw.Draw(badge_bg)
        badge_draw.rounded_rectangle(
            [0, 0, np_width + badge_padding * 2, badge_height],
            radius=badge_height // 2,
            fill=NEON_PINK
        )
        
        # Add badge to canvas
        badge_pos = (np_x - badge_padding, np_y)
        canvas.paste(badge_bg, badge_pos, badge_bg)
        draw.text((np_x, np_y + badge_height // 2 - 12), np_text, fill=TEXT_WHITE, font=np_font)
        
        # Title section
        title_y = np_y + badge_height + 40
        title_font, title_wrapped = fit_title_font(
            draw, title, content_width - 40, FONT_BOLD_PATH,
            max_lines=2, start_size=38, min_size=32
        )
        
        # Title with shadow
        draw.multiline_text((content_x + 3, title_y + 3), 
                          title_wrapped, fill=TEXT_SHADOW,
                          font=title_font, spacing=8, align='left')
        draw.multiline_text((content_x, title_y), 
                          title_wrapped, fill=TEXT_WHITE,
                          font=title_font, spacing=8, align='left')
        
        # Metadata section with icons
        meta_start_y = title_y + 120
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        
        # Channel info
        channel_icon = "📺"
        channel_text = f"  {channel}"
        draw.text((content_x, meta_start_y), channel_icon, fill=ACCENT_GREEN, font=icon_font)
        draw.text((content_x + 40, meta_start_y), channel_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Views info
        views_icon = "👁️"
        views_text = f"  {views}"
        draw.text((content_x, meta_start_y + 50), views_icon, fill=NEON_BLUE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 50), views_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Duration info
        duration_icon = "⏱️"
        duration_text = f"  {duration}"
        draw.text((content_x, meta_start_y + 100), duration_icon, fill=ACCENT_PURPLE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 100), duration_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Add decorative elements
        
        # Top right decorative circle
        circle_size = 120
        circle_x = CANVAS_W - circle_size - 40
        circle_y = 40
        circle_img = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle_img)
        circle_draw.ellipse([0, 0, circle_size, circle_size], 
                          outline=ACCENT_PINK, width=4)
        
        # Add smaller inner circle
        inner_circle_size = circle_size - 30
        circle_draw.ellipse(
            [(circle_size - inner_circle_size) // 2, 
             (circle_size - inner_circle_size) // 2,
             (circle_size + inner_circle_size) // 2,
             (circle_size + inner_circle_size) // 2],
            outline=NEON_BLUE, width=2
        )
        
        canvas.paste(circle_img, (circle_x, circle_y), circle_img)
        
        # Bottom right music note
        music_font = ImageFont.truetype(FONT_BOLD_PATH, 48)
        music_note = "♪"
        music_x = CANVAS_W - 80
        music_y = CANVAS_H - 120
        add_glow_effect(draw, music_note, (music_x, music_y), music_font, NEON_PINK, iterations=5)
        draw.text((music_x, music_y), music_note, fill=ACCENT_PURPLE, font=music_font)
        
        # Add subtle particles/glitter
        for _ in range(50):
            x = random.randint(0, CANVAS_W)
            y = random.randint(0, CANVAS_H // 2)
            size = random.randint(1, 3)
            color = random.choice([NEON_BLUE, ACCENT_PINK, ACCENT_PURPLE, ACCENT_GREEN])
            draw.ellipse([x, y, x + size, y + size], fill=color)
        
        # Save final thumbnail
        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95, optimize=True)
        
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
        
        # Fallback to default thumbnail
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
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception as cleanup_error:
                print(f"[Final Cleanup Error] {cleanup_error}")
