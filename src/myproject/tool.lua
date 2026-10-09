-- System tool: a settings page saved to a file, released on close.
local util, BASE = ...

local SETTINGS = BASE .. "settings.lua"     -- absolute: used from callbacks
local state                                  -- owned by the open page; nil when closed

local function load()
  local chunk = loadfile(SETTINGS)
  local ok, t = pcall(chunk or function() return nil end)
  t = (ok and type(t) == "table") and t or {}
  t.greeting = t.greeting or "@i18n(tool.default_greeting)@"
  return t
end

local function save(t)
  local f = io.open(SETTINGS, "w")
  if not f then return util.log("could not write %s", SETTINGS) end
  f:write(string.format("return { greeting = %q }\n", t.greeting))
  f:close()
end

local function create()
  state = { settings = load(), dirty = false }
  local line = form.addLine("@i18n(tool.greeting)@")
  form.addTextField(line, nil, function() return state.settings.greeting end,
    function(v) state.settings.greeting = v; state.dirty = true end)
  line = form.addLine("@i18n(tool.say_it)@")
  form.addButton(line, nil, { text = "@i18n(tool.print)@", press = function() util.log("%s", state.settings.greeting) end })
  return state
end

local function close()
  if state and state.dirty then save(state.settings) end   -- write once, on close
  state = nil
end

return {
  name = "@i18n(project.name)@",
  icon = lcd.loadMask("icon.png"),   -- required; black shapes on white (dark = drawn)
  create = create,
  close = close,
}
