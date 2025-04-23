
function HorizontalRule(el)
    return pandoc.RawBlock('latex', '\\starrule')
end

-- function Note(el)
--     return pandoc.Note(pandoc.List({pandoc.Str("Test")}))
-- end


function Inlines(inlines)

    if in_note then
        return inlines
    end

    local i = 1
    local result = {}
    
    while i <= #inlines do
        local el = inlines[i]
        
        -- Détecte les balises d'ouverture
        if el.t == "RawInline" and el.format == "html" then
            if el.text == "<sup>" or el.text == "<sub>" then
                local tag_type = el.text:match("<(.-)>")  -- Extrait "sup" ou "sub"
                local content = ""
                local closing_tag = "</" .. tag_type .. ">"
                i = i + 1
                
                -- Collecte tout jusqu'à la balise de fermeture
                while i <= #inlines do
                    el = inlines[i]
                    if el.t == "RawInline" and el.format == "html" and el.text == closing_tag then
                        -- Fin de la balise
                        if tag_type == "sup" then
                            tag_type = "super"
                        end
                        local latex_cmd = "\\text" .. tag_type .. "script{" .. content .. "}"
                        table.insert(result, pandoc.RawInline("latex", latex_cmd))
                        break
                    else
                        -- Ajoute le contenu
                        content = content .. pandoc.utils.stringify({el})
                    end
                    i = i + 1
                end
            else
                -- Autre RawInline, l'ajouter normalement
                table.insert(result, el)
            end
        elseif el.t == "Str" then
            -- Remplacer uniquement les espaces insécables avant la ponctuation double française
            -- et après guillemets ouvrants ou avant guillemets fermants
            local text = el.text
            
            -- Espace insécable (U+00A0) encodé en UTF-8 comme \194\160
            local NBSP = "\194\160"
            
            -- 1. Remplacer les espaces insécables avant ponctuation double
            text = text:gsub(NBSP .. "([;:!?])", "%1")
            
            -- 2. Remplacer les espaces insécables après guillemet ouvrant français («)
            text = text:gsub("«" .. NBSP, "«")
            
            -- 3. Remplacer les espaces insécables avant guillemet fermant français (»)
            text = text:gsub(NBSP .. "»", "»")
            
            -- 4. Remplacer les espaces insécables après tiret cadratin (—)
            text = text:gsub("—" .. NBSP, "—")
            
            -- 5. Remplacer tous les autres espaces insécables par \,
            -- text = text:gsub(NBSP, "\\,")
            text = text:gsub(NBSP .. "([%%$&#_{}~^\\])", "\\,\\%1")  -- Traiter les cas spéciaux
            text = text:gsub(NBSP, "\\,")                           -- Puis les cas généraux
            
            -- 6. Échapper les caractères spéciaux pour LaTeX
            text = text:gsub("&", "\\&")
            
            table.insert(result, pandoc.RawInline("latex", text))
        else
            -- Élément normal, l'ajouter
            table.insert(result, el)
        end
        
        i = i + 1
    end
    
    return result
end