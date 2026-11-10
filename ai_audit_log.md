# AI Code Audit Log — NetArchitect (CIC-307)

Requirement: at least two **real** cases where AI suggested flawed networking code, with diagnosis and fix, validated by packet-flow analysis.
Rule: record only real incidents from this build. Never invent entries.

## Entry template

### Entry N — <short title>
- **Date / phase:**
- **AI tool & model:**
- **Prompt given:**
```
<exact prompt>
```
- **AI-generated code (buggy):**
```python
<exact code>
```
- **Symptom:** what went wrong, how noticed (test name / verifier output)
- **Packet-flow analysis:** `netarch trace ...` output before fix, showing the wrong hop / drop / leak
- **Root cause:** networking explanation (RFC / standard from docs/standards.md)
- **Fix:**
```python
<fixed code>
```
- **Packet-flow after fix:** trace output
- **Regression test:** `tests/...::test_name`

---

## Entries
_None yet._
