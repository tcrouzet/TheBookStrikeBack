-- Filtre Pandoc (HTML/EPUB) : CodeBlock sans classe -> <p class="right">…</p>
local function html_escape(s)
  s = s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;")
  return s
end

function CodeBlock(el)
  if #el.classes == 0 and (FORMAT:match("html") or FORMAT:match("epub")) then
    local content = el.text:gsub("\r\n", "\n")
    content = html_escape(content)
    content = content:gsub("%*([^%*]+)%*", "<em>%1</em>")
    content = content:gsub("\n", "<br />")
    return pandoc.RawBlock("html", '<p class="tab">' .. content .. '</p>')
  end
end