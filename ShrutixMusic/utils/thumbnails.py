async def get_thumb_minimal(videoid: str):
    """Minimal thumbnail - only YouTube thumbnail with bot name at bottom"""
    
    try:
        # Fetch YouTube data
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        data = await results.next()
        
        if not data or "result" not in data:
            return FALLBACK_THUMB if os.path.exists(FALLBACK_THUMB) else None
        
        result = data["result"][0]
        thumburl = result["thumbnails"][0]["url"].split("?")[0] if result.get("thumbnails") else ""
        
        if not thumburl:
            return FALLBACK_THUMB if os.path.exists(FALLBACK_THUMB) else None
        
        # Download thumbnail
        thumb_path = CACHE_DIR / f"yt_{videoid}.jpg"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
        
        # Load and resize YouTube thumbnail
        canvas = Image.open(thumb_path).convert("RGBA")
        canvas = canvas.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        
        draw = ImageDraw.Draw(canvas)
        
        # Add ONLY the bot name at bottom
        try:
            font = ImageFont.truetype(FONT_BOLD_PATH, 36)
        except:
            font = ImageFont.load_default()
        
        bot_text = "@Allicemusicbot"
        bot_width = draw.textlength(bot_text, font=font)
        bot_x = (CANVAS_W - bot_width) // 2
        bot_y = CANVAS_H - 60
        
        # Simple white text with shadow
        draw.text((bot_x + 2, bot_y + 2), bot_text, fill=(0, 0, 0, 150), font=font)
        draw.text((bot_x, bot_y), bot_text, fill=(255, 255, 255, 255), font=font)
        
        # Save
        out = CACHE_DIR / f"{videoid}_minimal.png"
        canvas.save(out, "PNG", quality=95)
        
        # Cleanup
        if thumb_path.exists():
            os.remove(thumb_path)
        
        return str(out)
        
    except:
        return FALLBACK_THUMB if os.path.exists(FALLBACK_THUMB) else None
