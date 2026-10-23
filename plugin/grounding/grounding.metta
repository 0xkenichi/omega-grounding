; Omega plugin: ground NAL premises in external sources before reasoning.
;
; Adds the `ground` skill. The agent passes a premise exactly as it would
; pass it to |-; the plugin looks the statement up (Wikidata, Ethereum),
; corrects swapped relations and wrong values, and returns the premise with a
; truth value calibrated to the source instead of to the LLM's own estimate.
; See README.md in this directory for installation.

!(import! &self (library Omega ./plugins/grounding/grounding.py))
!(import! &self (library Omega ./plugins/grounding/grounding_core))

(= (groundingEnabled) (empty))
(= (groundingLlmDiscount) (empty))
(= (groundingRemember) (empty))

(= (loadOmegaPlugin)
    (progn
        ; Enable or disable the integration.
        (configure groundingEnabled enabled)
        ; Points subtracted from LLM-assigned confidence before revision.
        (configure groundingLlmDiscount "0.15")
        ; Store every grounded premise, with provenance, in long-term memory.
        (configure groundingRemember enabled)
        (if (== (groundingEnabled) enabled)
            (progn
                (add-skill
                    ground
                    "Check a NAL premise against external sources before reasoning with it. Pass the premise as you would pass it to |-, e.g. ((--> dolphin mammal) (stv 1.0 0.9)) or ((--> (× usdc 6) decimals) (stv 1.0 0.9)). Returns the premise to use, with a source-calibrated truth value, provenance and an ACT/HYPOTHESIZE/IGNORE tier."
                    (premise))
                (add-prompt-extension
                    grounding
                    "GROUNDING: before using a factual premise in |- or |~, call ground on it and reason with the premise it returns, not your own. If the verdict is CORRECTED, use the corrected statement. Act only on conclusions whose premises were grounded or whose tier is ACT.")
                (log INFO "grounding-plugin" "Grounding is enabled"))
            (log INFO "grounding-plugin" "Grounding is disabled"))))

(= (ground $premise)
    (let* (($parsed (sread $premise))
           ($evidence (sread (py-call (grounding.lookup $premise))))
           ($discount (py-call (grounding.to_float (groundingLlmDiscount))))
           ($result (grounding-combine $parsed $evidence $discount))
           ($text (repr $result)))
        (progn
            (if (== (groundingRemember) enabled)
                (remember $text)
                ())
            $text)))
