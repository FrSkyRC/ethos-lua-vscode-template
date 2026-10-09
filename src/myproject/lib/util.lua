-- Small shared helpers. Loaded once from main.lua.
local util = {}

-- Fonts from largest to smallest, built once.
local FONTS = { FONT_XXL, FONT_XL, FONT_L, FONT_M, FONT_S }

-- Pick the largest font in which `text` fits a w x h box.
-- Returns font, text width, text height. Measuring is not free, so callers
-- cache the result and only call this when the text or box size changes.
function util.fitFont(text, w, h)
  for i = 1, #FONTS do
    lcd.font(FONTS[i])
    local tw, th = lcd.getTextSize(text)
    if tw <= w and th <= h then return FONTS[i], tw, th end
  end
  local tw, th = lcd.getTextSize(text)
  return FONTS[#FONTS], tw, th
end

-- Prefix print() output so it is easy to find in the shared console / serial log.
function util.log(fmt, ...)
  print(string.format("[myproject] " .. fmt, ...))
end

return util
