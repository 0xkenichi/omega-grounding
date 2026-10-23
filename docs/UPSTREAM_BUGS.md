# Draft bug report for singnet/Omega (not posted)

**Title:** `(library Omega X)` resolves to several paths after `petta_lib_chromadb` is git-imported, so MeTTa plugins get their functions defined twice

**Environment:** Omega `main` at 63a7826, PeTTa v1.0.4 (as pinned in the Dockerfile), SWI-Prolog 10.0.2.

**What happens.** `lib_omega.metta` line 30 runs `!(git-import! "https://github.com/patham9/petta_lib_chromadb.git")`. After that, `(library Omega ./src/loop)` evaluates to three spellings of the same file:

```
./repos/petta_lib_chromadb/../Omega/./src/loop
./repos/Omega/../Omega/./src/loop
<PeTTa>/src/../lib/../Omega/./src/loop
```

A later `!(import! &self (library Omega <file>))` loads the file more than once, so every function in it gets duplicate clauses and returns duplicate results. Nested calls multiply this: in our plugin a single skill call returned 16, and later 64, identical results to the agent.

**Repro.** From the PeTTa root:

```metta
!(import! &self (library lib_import))
!(git-import! "https://github.com/singnet/Omega.git")
!(import! &self (library Omega lib_omega))
!(import! &self (library Omega ./plugins/openclaw/openclaw))
!(println! (collapse (match &self (= (openclaw-collect-results $i) $body) found)))
```

This prints `(found found)`; `(found)` is expected. The bundled `openclaw` plugin is affected, and so is any plugin that imports its own MeTTa through `(library Omega ...)`. Bisecting `lib_omega.metta` shows the duplication starts at the `petta_lib_chromadb` git-import.

**Workaround** (used in omega-grounding's plugin): import from the first resolution only.

```metta
!(import! &self (car-atom (collapse (library Omega ./plugins/<name>/<file>))))
```

**Likely fix:** in PeTTa, either canonicalise candidate paths (resolve `..`) before `import_once` keys them, or make `library/3` return only the first existing candidate. The `resolve_library_path` → `once(...)` structure suggests a single result was intended.

**Related:** `lib_omega.metta` still imports the removed `./src/context` (open PR #399).
