-- Widget: shows any source the pilot chooses, in the largest font that fits.
-- Demonstrates create / wakeup / paint / configure / read / write and the
-- "redraw only on change" pattern.
local util = ...

local function create()
  return { source = nil, shown = nil, text = "--", fit = nil, fitKey = nil }
end

local function wakeup(w)
  if not w.source then return end
  local v = w.source:value()
  -- compare at display precision so sensor noise doesn't trigger redraws
  local shown = v and math.floor(v * 10 ^ w.source:decimals() + 0.5)
  if shown ~= w.shown then
    w.shown = shown
    w.text = v and w.source:stringValue() or "--"
    lcd.invalidate()
  end
end

local function paint(w)
  local ww, wh = lcd.getWindowSize()
  local key = ww * 100000 + wh * 100 + #w.text
  if key ~= w.fitKey then                       -- re-measure only when needed
    w.fitKey = key
    w.fit = util.fitFont(w.text, ww - 8, wh - 4)
  end
  lcd.font(w.fit)
  local _, th = lcd.getTextSize(w.text)
  lcd.color(lcd.themeColor(THEME_DEFAULT_COLOR))
  lcd.drawText(ww / 2, (wh - th) / 2, w.source and w.text or "@i18n(widget.configure)@", CENTERED)
end

local function configure(w)
  local line = form.addLine("@i18n(widget.source)@")
  form.addSourceField(line, nil, function() return w.source end,
    function(v) w.source = v; w.shown = nil end)
end

local function read(w)
  w.source = storage.read("source")
end

local function write(w)
  storage.write("source", w.source)
end

return {
  key = "myproj",              -- unique, 7 characters max
  name = "@i18n(project.name)@",  -- resolved per language at deploy/package time
  create = create, wakeup = wakeup, paint = paint,
  configure = configure, read = read, write = write,
}
