-- Aseprite headless build script: imports recorded passes as stacked layers
-- Usage: aseprite -b --script-param steps_dir=... --script-param out_file=... --script build.lua

local steps_dir = app.params["steps_dir"]
local out_file = app.params["out_file"]

if not steps_dir or not out_file then
  error("Missing required script-param: steps_dir or out_file")
end

local passes = {
  { name = "01_Silhouette", file = steps_dir .. "/01_silhouette.png" },
  { name = "02_BlockIn",    file = steps_dir .. "/02_blockin.png" },
  { name = "03_Shading",    file = steps_dir .. "/03_shading.png" },
  { name = "04_Cleanup",    file = steps_dir .. "/04_cleanup.png" }
}

local sprite = nil

for i, pass in ipairs(passes) do
  local img = Image{ fromFile = pass.file }
  if img then
    if sprite == nil then
      sprite = Sprite(img.width, img.height, ColorMode.RGB)
      local layer = sprite.layers[1]
      layer.name = pass.name
      sprite:newCel(layer, 1, img, Point(0, 0))
    else
      local layer = sprite:newLayer()
      layer.name = pass.name
      sprite:newCel(layer, 1, img, Point(0, 0))
    end
  end
end

if sprite then
  sprite:saveAs(out_file)
  print("Saved layered Aseprite project to " .. out_file)
end
