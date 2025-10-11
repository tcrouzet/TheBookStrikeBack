function Str(elem)
  local text = elem.text
  -- Remplace les espaces insécables par des spans avec classe

  text = text:gsub('\u{00A0}:', '<span class="thin-space-before">:</span>')
  text = text:gsub('\u{00A0}!', '<span class="thin-space-before">!</span>')
  text = text:gsub('\u{00A0};', '<span class="thin-space-before">;</span>')
  text = text:gsub('\u{00A0}»', '<span class="thin-space-before">»</span>')
  text = text:gsub('\u{00A0}—', '<span class="thin-space-before">—</span>')
  text = text:gsub('\u{00A0}??', '<span class="thin-space-before">?</span>')
  -- text = text:gsub('\u{00A0}%%', '<span class="thin-space-before">%</span>')

  text = text:gsub('«\u{00A0}', '<span class="thin-space-after">«</span>')
  text = text:gsub('—\u{00A0}', '<span class="thin-space-after">—</span>')
  text = text:gsub('/\u{00A0}', '<span class="thin-space-after">/</span>')
  
  text = text:gsub('\u{00A0}', '<span class="thin-space">\u{00A0}\u{00A0}</span>')

  return pandoc.RawInline('html', text)
end