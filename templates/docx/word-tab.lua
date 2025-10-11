-- CodeBlock -> paragraphe DOCX avec style "tab" + gestion italique *...* et sauts de ligne
local PAR_STYLE = "tab"  -- ID du style paragraphe dans model.docx (change si besoin, ex: "Tab")

local function xml_escape(s)
  return (s
    :gsub("&", "&amp;")
    :gsub("<", "&lt;")
    :gsub(">", "&gt;"))
end

local function make_run(text, italic)
  text = xml_escape(text)
  local rPr = italic and "<w:rPr><w:i/></w:rPr>" or ""
  return string.format('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>', rPr, text)
end

-- Transforme "foo *bar* baz" en runs {text, italic}
local function runs_emphasis_pairs(s)
  local runs, pos = {}, 1
  while true do
    local a = s:find("%*", pos)
    if not a then
      if pos <= #s then table.insert(runs, { text = s:sub(pos), italic = false }) end
      break
    end
    local b = s:find("%*", a + 1)
    if not b then
      -- pas de fermeture -> tout le reste en normal
      table.insert(runs, { text = s:sub(pos), italic = false })
      break
    end
    if a > pos then
      table.insert(runs, { text = s:sub(pos, a - 1), italic = false })
    end
    table.insert(runs, { text = s:sub(a + 1, b - 1), italic = true })
    pos = b + 1
  end
  return runs
end

function CodeBlock(el)
  if #el.classes == 0 and FORMAT:match("docx") then
    local s = el.text:gsub("\r\n", "\n")
    local out = {}
    table.insert(out, '<w:p><w:pPr><w:pStyle w:val="' .. PAR_STYLE .. '"/></w:pPr>')
    local first = true
    for line in (s .. "\n"):gmatch("([^\n]*)\n") do
      if not first then
        table.insert(out, "<w:r><w:br/></w:r>")
      end
      local runs = runs_emphasis_pairs(line)
      for _, r in ipairs(runs) do
        table.insert(out, make_run(r.text, r.italic))
      end
      first = false
    end
    table.insert(out, "</w:p>")
    return pandoc.RawBlock("openxml", table.concat(out))
  end
  -- sinon laisser le comportement par défaut
  return nil
end