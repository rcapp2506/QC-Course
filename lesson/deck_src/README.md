# Source of `../RSA_Shor_lecture.pptx`

`build_deck.py` generates the lecture deck from the course template
(`../Quantum Computing - Course - 2025-26.pptx`, copied as `template.pptx` next to the
script) with python-pptx. Equations are written in LaTeX and converted to **native,
editable PowerPoint equations** (LaTeX → MathML via `latex2mathml` → OMML via Office's
`MML2OMML.XSL`, copied from the local Office install as `mml2omml.xsl`).

Requirements: Python ≥ 3.9 with `python-pptx lxml latex2mathml`; for `render.sh`
(build + validate + PNG export + QA contact sheets) also PowerPoint on the Windows host
(the export is driven through COM from WSL via `powershell.exe`).

```bash
cp "../Quantum Computing - Course - 2025-26.pptx" template.pptx
cp "/mnt/c/Program Files/Microsoft Office/root/Office16/MML2OMML.XSL" mml2omml.xsl
python build_deck.py RSA_Shor_lecture.pptx
```

`assets/` holds the figures used in the slides (histograms and circuit from the notebooks).
The deck can of course also be edited directly in PowerPoint.
