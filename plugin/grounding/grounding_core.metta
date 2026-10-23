; Grounding policy: how source evidence is folded into an LLM premise.
;
; Pure MeTTa with one dependency, Truth_Revision from Omega's lib_nal.metta.
; It mirrors omega_grounding.evidence.combine in Python, which the benchmark
; uses; tests/test_metta_parity.py checks that the two agree.
;
; Evidence comes from the Python bridge as
;   (evidence $verdict (stv $f $c) (correction $statement-or-none) $provenance)

; Omega's failure-mode report: LLM-assigned confidence runs ~15 points high.
(= (grounding-discount (stv $f $c) $amount)
   (stv $f (max 0.0 (- $c $amount))))

; Action tiers from docs/reference-orchestration.md.
(= (grounding-tier (stv $f $c))
   (if (>= $f 0.6)
       (if (>= $c 0.5) ACT (grounding-tier-low $f $c))
       (grounding-tier-low $f $c)))

(= (grounding-tier-low $f $c)
   (if (>= $f 0.3)
       (if (>= $c 0.2) HYPOTHESIZE IGNORE)
       IGNORE))

; Evidence with no confidence (UNKNOWN) leaves the prior as it is; anything
; else is merged with NAL revision, exactly as |- merges two premises.
(= (grounding-revise $prior (stv $ef $ec))
   (if (< $ec 0.001)
       $prior
       (Truth_Revision $prior (stv $ef $ec))))

; A correction replaces the premise only when the LLM was asserting it.
(= (grounding-use-correction $correction (stv $f $c))
   (if (== $correction none) False (>= $f 0.5)))

(= (grounding-result $verdict $statement $truth $provenance)
   (let $tier (grounding-tier $truth)
     (grounded $verdict ($statement $truth) $tier $provenance)))

(= (grounding-combine ($statement $llmTruth)
                      (evidence $verdict (stv $ef $ec) (correction $correction) $provenance)
                      $discount)
   (if (grounding-use-correction $correction $llmTruth)
       (grounding-result CORRECTED $correction (stv 1.0 $ec) $provenance)
       (let* (($prior (grounding-discount $llmTruth $discount))
              ($truth (grounding-revise $prior (stv $ef $ec))))
         (grounding-result $verdict $statement $truth $provenance))))
