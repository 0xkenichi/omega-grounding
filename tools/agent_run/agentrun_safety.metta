; Safety plugin for tools/agent_run.
;
; The run is not sandboxed (Landlock is Linux-only), so the agent gets no shell, file,
; web, memory or raw-MeTTa skills. NAL/PLN inference stays available through `nal`,
; which only evaluates (|- ...) / (|~ ...) built from whitelisted parts
; (agentrun_channel.allowed_inference), so no code can ride inside a premise.

(= (loadOmegaPlugin)
    (progn
        (remove-skill shell)
        (remove-skill read-file)
        (remove-skill write-file)
        (remove-skill write-file-b64)
        (remove-skill append-file)
        (remove-skill delete-file)
        (remove-skill get-io-policy)
        (remove-skill websearch)
        (remove-skill metta)
        (remove-skill remember)
        (remove-skill query)
        (add-skill
            nal
            "Run one NAL (|-) or PLN (|~) inference step on premises, e.g. (|- ((--> a b) (stv 1.0 0.9)) ((--> b c) (stv 1.0 0.9))). Only inference expressions are accepted."
            (sexpression))
        (add-prompt-extension
            agentrun
            "This session has no shell, file, web or long-term memory access. For inference use the nal skill in place of metta.")
        (log INFO "agentrun-safety" "Removed shell, file, web, memory and metta skills; added nal")))

(= (nal $str)
    (if (py-call (agentrun_channel.allowed_inference $str))
        (let $code (sread $str)
            (repr (collapse (eval $code))))
        (Error (nal $str) "Only (|- ...) or (|~ ...) inference expressions are accepted")))
