-- myproject: starter Ethos Lua project.
-- Registers one widget and one system tool. Replace them with your own.
-- Docs: https://frskyrc.github.io/ethos-lua-doc/

-- Files used from callbacks need absolute paths: relative paths only resolve
-- to this folder while main.lua is loading. Keep this in sync with
-- "tgt_name" in .vscode/deploy.json (the folder name on the radio).
local BASE = "SCRIPTS:/myproject/"

-- Loaded once, at load time (relative paths are fine here).
local util = assert(loadfile("lib/util.lua"))()
local widget = assert(loadfile("widget.lua"))(util)
local tool = assert(loadfile("tool.lua"))(util, BASE)

local function init()
  system.registerWidget(widget)
  system.registerSystemTool(tool)
end

return { init = init }
