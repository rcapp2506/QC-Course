# Lesson: RSA and Shor's Algorithm

`rsa_shor_lesson.tex` — a detailed, self-contained lesson (English) covering:

1. **Asymmetric cryptography** — symmetric vs. public-key, trapdoor one-way functions.
2. **Number theory with theorems** (stated *and* explained/proved): Bézout, modular
   inverses, Euler's totient, **Fermat's little theorem**, **Euler's theorem**, the
   **Chinese Remainder Theorem**.
3. **RSA** — key generation, encryption/decryption, a full **correctness proof**, a
   worked-by-hand example, and the security reduction to factoring.
4. **Shor's algorithm** — the factoring→order-finding reduction (with proof and the
   success-probability lemma), quantum phase estimation of the modular-multiplication
   operator, continued-fraction recovery, a step-by-step **recipe**, and worked
   examples factoring 15 and 21 — plus a resource reality check and a post-quantum note.

It is the companion to `../IBM/shor.ipynb` and `../IQM/shor.ipynb`; the final section
maps each part of the lesson onto specific notebook cells/functions.

## Build

Requires a TeX distribution (TeX Live / MiKTeX). Packages used: `amsmath`, `amssymb`,
`amsthm`, `mathtools`, `geometry`, `enumitem`, `xcolor`, `tcolorbox`, `hyperref`.

```bash
pdflatex rsa_shor_lesson.tex
pdflatex rsa_shor_lesson.tex   # second pass resolves cross-references / ToC
```

Produces `rsa_shor_lesson.pdf` (9 pages).
