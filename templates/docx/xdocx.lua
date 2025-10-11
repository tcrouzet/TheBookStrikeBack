-- function Image(img)
--     print(img)
--     img.attributes["custom-style"] = "Figure"
--     return img
--   end

function Block(elem)
    if elem.t == "HorizontalRule" then
      return pandoc.RawBlock('openxml', '<w:p><w:pPr><w:pStyle w:val="Spacer"/></w:pPr><w:r><w:t>*</w:t></w:r></w:p>')
    else
      return elem
    end
  end
  
  local in_sup = false
  local in_sub = false
  local sup_content = {}
  local sub_content = {}
  
  function Inline(elem)
    return InlineSub(InlineSup(elem))
  end
  
  
  function InlineSup(elem)
    if elem.t == "RawInline" and elem.format == "html" then
      if elem.text:match("<sup>") then
        in_sup = true
        sup_content = {}
        return {}  -- Supprimer la balise ouvrante
      elseif elem.text:match("</sup>") then
        if in_sup then
          in_sup = false
          local content = table.concat(sup_content, "")
          -- Retourner le texte avec le style "Exposant"
          return {pandoc.RawInline('openxml', 
            '<w:r><w:rPr><w:rStyle w:val="Exposant"/></w:rPr><w:t>' .. content .. '</w:t></w:r>')}
        end
      end
    elseif in_sup then
      if elem.t == "Str" then
        table.insert(sup_content, elem.text)
        return {}  -- Supprimer le texte accumulé
      elseif elem.t == "Space" then
        table.insert(sup_content, " ")
        return {}  -- Supprimer les espaces accumulés
      end
    end
    return elem
  end
  
  function InlineSub(elem)
    if elem.t == "RawInline" and elem.format == "html" then
      if elem.text:match("<sub>") then
        in_sub = true
        sub_content = {}
        return {}  -- Supprimer la balise ouvrante
      elseif elem.text:match("</sub>") then
        if in_sub then
          in_sub = false
          local content = table.concat(sub_content, "")
          -- Retourner le texte avec le style "Exposant"
          return {pandoc.RawInline('openxml', 
            '<w:r><w:rPr><w:rStyle w:val="Indice"/></w:rPr><w:t>' .. content .. '</w:t></w:r>')}
        end
      end
    elseif in_sub then
      if elem.t == "Str" then
        table.insert(sub_content, elem.text)
        return {}  -- Supprimer le texte accumulé
      elseif elem.t == "Space" then
        table.insert(sub_content, " ")
        return {}  -- Supprimer les espaces accumulés
      end
    end
    return elem
  end
  