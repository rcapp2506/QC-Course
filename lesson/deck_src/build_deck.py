"""Build the RSA & Shor lecture deck on the course template (python-pptx + native OMML equations)."""
import copy, re, sys, os
from lxml import etree
import latex2mathml.converter as l2m
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
OUT = sys.argv[1] if len(sys.argv) > 1 else "RSA_Shor_lecture.pptx"

BLUE = RGBColor(0x05, 0x63, 0xC1)
RED = RGBColor(0xC0, 0x00, 0x00)
NAVY = RGBColor(0x00, 0x20, 0x60)
GREY = RGBColor(0x40, 0x40, 0x40)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF2, 0xF2, 0xF2)
LIGHTBLUE = RGBColor(0xDE, 0xEB, 0xF7)
LIGHTRED = RGBColor(0xFB, 0xE5, 0xE5)
LINEGREY = RGBColor(0xBF, 0xBF, 0xBF)
GREEN = RGBColor(0x37, 0x86, 0x3C)

NOTEBOOK_URL = "https://github.com/rcapp2506/QC-Course/blob/main/IBM/22_Shor_Period_Finding_to_RSA.ipynb"
NOTEBOOK_IQM_URL = "https://github.com/rcapp2506/QC-Course/blob/main/IQM/22_Shor_Period_Finding_to_RSA.ipynb"

# ----------------------------------------------------------------------------- math
XSL = etree.XSLT(etree.parse("mml2omml.xsl"))
M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
A14 = "http://schemas.microsoft.com/office/drawing/2010/main"
WRAP = ('<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:a14="http://schemas.microsoft.com/office/drawing/2010/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
        '<mc:Choice Requires="a14"><a14:m/></mc:Choice>'
        '<mc:Fallback><a:r><a:rPr lang="en-US"/><a:t>[equation]</a:t></a:r></mc:Fallback></mc:AlternateContent>')


def _replace_braced(s, cmd, fmt):
    """Replace every cmd{...} (balanced braces) by fmt.format(inner)."""
    out, i = "", 0
    while True:
        j = s.find(cmd + "{", i)
        if j < 0:
            return out + s[i:]
        out += s[i:j]
        k, depth = j + len(cmd) + 1, 1
        while depth:
            depth += {"{": 1, "}": -1}.get(s[k], 0); k += 1
        out += fmt.format(s[j + len(cmd) + 1:k - 1]); i = k


def tex(s):
    """Normalise the lesson's LaTeX to what latex2mathml renders well."""
    s = _replace_braced(s, r"\ket", r"\left| {} \right\rangle")
    s = _replace_braced(s, r"\pmod", r"\;\left(\mathrm{{mod}}\ {}\right)")
    s = s.replace(r"\bmod", r"\;\mathrm{mod}\;")
    s = s.replace(r"\qquad", r"\ \ \ \ \ \ ").replace(r"\quad", r"\ \ \ ").replace(r"\;", r"\ ").replace(r"\!", "")
    s = s.replace(r"\gcd", r"\mathrm{gcd}").replace(r"\ord", r"\mathrm{ord}")
    s = s.replace(r"\tfrac", r"\frac").replace(r"\dfrac", r"\frac")
    s = re.sub(r"\\(bigl|bigr|Bigl|Bigr|big|Big)", "", s)
    s = s.replace(r"\Zn", r"(\mathbb{Z}/N\mathbb{Z})^{*}").replace(r"\Z", r"\mathbb{Z}")
    return s


def omml(latex, size_pt, color=None):
    mml = etree.fromstring(l2m.convert(tex(latex)).encode())
    # MML2OMML.XSL treats every <mo> between two fence <mo>s as a separator and drops the
    # rest: wrap the fenced content into a single inner <mrow> so it becomes one <m:e>.
    MML = "http://www.w3.org/1998/Math/MathML"
    for mrow in list(mml.iter(f"{{{MML}}}mrow")):
        ch = list(mrow)
        if len(ch) >= 3 and ch[0].tag == f"{{{MML}}}mo" and ch[0].get("fence") == "true" \
                and ch[-1].tag == f"{{{MML}}}mo" and ch[-1].get("fence") == "true":
            inner = etree.Element(f"{{{MML}}}mrow")
            for c_ in ch[1:-1]:
                mrow.remove(c_); inner.append(c_)
            mrow.insert(1, inner)
    root = XSL(mml).getroot()
    if root.tag != f"{{{M}}}oMathPara":
        para = etree.Element(f"{{{M}}}oMathPara")
        para.append(root)
        root = para
    for r in root.iter(f"{{{M}}}r"):
        rpr = r.find(f"{{{A}}}rPr")
        if rpr is None:
            rpr = etree.Element(f"{{{A}}}rPr")
            r.insert(0, rpr)
        rpr.set("lang", "en-US")
        rpr.set("sz", str(int(size_pt * 100)))
        if color is not None:
            for old in rpr.findall(f"{{{A}}}solidFill"):
                rpr.remove(old)
            sf = etree.SubElement(rpr, f"{{{A}}}solidFill")
            c = etree.SubElement(sf, f"{{{A}}}srgbClr")
            c.set("val", "%02X%02X%02X" % (color[0], color[1], color[2]))
    return root


def add_math(paragraph, latex, size_pt=20, color=None, align="l"):
    p = paragraph._p
    ac = etree.fromstring(WRAP)
    ac.find(f".//{{{A14}}}m").append(omml(latex, size_pt, color))
    p.append(ac)
    # oMathPara justification
    para = ac.find(f".//{{{M}}}oMathPara")
    ppr = etree.SubElement(para, f"{{{M}}}oMathParaPr")
    para.insert(0, ppr)
    j = etree.SubElement(ppr, f"{{{M}}}jc")
    j.set(f"{{{M}}}val", {"l": "left", "c": "center", "r": "right"}[align])


# ----------------------------------------------------------------------------- text helpers
def _bullet(p, level=0, char="•"):
    pPr = p._p.get_or_add_pPr()
    marL = 285750 * (level + 1)
    pPr.set("marL", str(marL))
    pPr.set("indent", str(-285750))
    for tag in ("buFont", "buChar", "buNone"):
        for e in pPr.findall(f"{{{A}}}{tag}"):
            pPr.remove(e)
    bf = etree.SubElement(pPr, f"{{{A}}}buFont")
    bf.set("typeface", "Arial")
    bc = etree.SubElement(pPr, f"{{{A}}}buChar")
    bc.set("char", char)


def _run(p, text, size=None, color=None, bold=None, italic=None, underline=None, link=None, font=None):
    r = p.add_run()
    r.text = text
    f = r.font
    if size: f.size = Pt(size)
    if color is not None: f.color.rgb = color
    if bold is not None: f.bold = bold
    if italic is not None: f.italic = italic
    if underline is not None: f.underline = underline
    if font: f.name = font
    if link:
        r.hyperlink.address = link
    return r


def textbox(slide, x, y, w, h, items, size=20, color=BLUE, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
            after=6, name=None, margin=None):
    """items: list of str | dict(t=str|[(str,opts)|str], bullet=bool, level=int, size, color, bold, after, align)
                          | dict(math=latex, size, color, align='l'|'c')"""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name: tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if margin is not None:
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(margin)
    first = True
    for it in items:
        if isinstance(it, str):
            it = {"t": it}
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = {None: align, "l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[it.get("align")]
        p.space_after = Pt(it.get("after", after))
        if "math" in it:
            add_math(p, it["math"], it.get("size", size + 2), it.get("color", color), it.get("align", "l") or "l")
            continue
        if it.get("bullet"):
            _bullet(p, it.get("level", 0), it.get("char", "•"))
        runs = it["t"] if isinstance(it["t"], list) else [it["t"]]
        for r in runs:
            if isinstance(r, str):
                r = (r, {})
            t, o = r
            _run(p, t, size=o.get("size", it.get("size", size)), color=o.get("color", it.get("color", color)),
                 bold=o.get("bold", it.get("bold")), italic=o.get("italic", it.get("italic")),
                 underline=o.get("underline"), link=o.get("link"), font=o.get("font"))
    return tb


def rect(slide, x, y, w, h, fill=None, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE, radius=None, name=None,
         shadow=False):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if name: s.name = name
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = Pt(line_w)
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if not shadow:
        # remove theme shadow/effects
        spPr = s._element.spPr
        etree.SubElement(spPr, f"{{{A}}}effectLst")
    s.text_frame.text = ""
    return s


def card(slide, x, y, w, h, header, items, fill=LIGHT, header_color=NAVY, size=16, color=GREY, after=4,
         header_size=None, line=LINEGREY, name=None):
    rect(slide, x, y, w, h, fill=fill, line=line, line_w=0.75, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06, name=name)
    its = []
    if header:
        its.append({"t": header, "bold": True, "color": header_color, "size": header_size or size + 2, "after": 6})
    its += items
    return textbox(slide, x + 0.12, y + 0.08, w - 0.24, h - 0.16, its, size=size, color=color, after=after)


def arrow(slide, x, y, w, h, fill=BLUE, shape=MSO_SHAPE.RIGHT_ARROW):
    return rect(slide, x, y, w, h, fill=fill, line=None, shape=shape)


def picture(slide, path, x, y, w=None, h=None, name=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    pic = slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)
    if name: pic.name = name
    return pic


# ----------------------------------------------------------------------------- template plumbing
prs = Presentation("template.pptx")
E = 914400
# harvest reusable template pictures before dropping the slides
os.makedirs("assets", exist_ok=True)
tpl_slides = list(prs.slides)
def save_pic(slide_no, shape_name, out):
    for sh in tpl_slides[slide_no - 1].shapes:
        if sh.name == shape_name and sh.shape_type == 13:
            open(out, "wb").write(sh.image.blob); return out
    raise KeyError((slide_no, shape_name))
SHOR_PHOTO = save_pic(54, "Immagine 15", "assets/shor_photo.jpg")
END_PIC = None
for sh in tpl_slides[60].shapes:
    if sh.shape_type == 13:
        END_PIC = "assets/end_pic." + sh.image.ext; open(END_PIC, "wb").write(sh.image.blob)

sldIdLst = prs.slides._sldIdLst
for sldId in list(sldIdLst):
    prs.part.drop_rel(sldId.rId); sldIdLst.remove(sldId)
LAY_TITLE_ONLY = [l for l in prs.slide_layouts if l.name == "Solo titolo"][0]
LAY_BLANK = [l for l in prs.slide_layouts if l.name == "Vuota"][0]

BAND_H = 1153391  # EMU, from the template


def new_slide(title, notes=None, band=True):
    s = prs.slides.add_slide(LAY_TITLE_ONLY)
    tree = s.shapes._spTree
    if band:
        b = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Emu(BAND_H))
        b.name = "Band"
        b.fill.solid(); b.fill.fore_color.rgb = NAVY; b.line.fill.background()
        etree.SubElement(b._element.spPr, f"{{{A}}}effectLst")
        tree.remove(b._element); tree.insert(2, b._element)   # behind the title
    t = s.shapes.title
    t.left, t.top, t.width, t.height = Emu(838200), Emu(275069), Emu(10515600), Emu(603250)
    t.fill.solid(); t.fill.fore_color.rgb = RED
    t.line.color.rgb = WHITE; t.line.width = Pt(0.75)
    tf = t.text_frame
    tf.text = ""
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, title, size=36, color=WHITE)
    bodyPr = tf._txBody.find(f"{{{A}}}bodyPr")
    for e in list(bodyPr): bodyPr.remove(e)
    etree.SubElement(bodyPr, f"{{{A}}}normAutofit")
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def demo_box(slide, x, y, w, h, label, url):
    """The course's red double-framed 'Demo ...' link box."""
    rect(slide, x, y, w, h, fill=None, line=RED, line_w=2.25, name="DemoFrameOuter")
    rect(slide, x + 0.12, y + 0.12, w - 0.24, h - 0.24, fill=None, line=RED, line_w=1.0, name="DemoFrameInner")
    textbox(slide, x, y, w, h, [{"t": [(label, {"bold": True, "underline": True, "link": url})], "align": "c"}],
            size=28, color=RED, anchor=MSO_ANCHOR.MIDDLE, name="DemoLink")


# ============================================================================= SLIDES
# 1 ---------------------------------------------------------------- title
s = new_slide("", band=False, notes="Lecture for the Quantum Computing course (MSc Physics). Companion to lesson/rsa_shor_lesson.pdf and the 22_Shor_Period_Finding_to_RSA.ipynb notebooks (IBM Aer / IQM).")
big = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(-0.05), prs.slide_width, Inches(3.75))
big.name = "TitleBand"; big.fill.solid(); big.fill.fore_color.rgb = NAVY; big.line.fill.background()
etree.SubElement(big._element.spPr, f"{{{A}}}effectLst")
tree = s.shapes._spTree; tree.remove(big._element); tree.insert(2, big._element)
t = s.shapes.title
t.left, t.top, t.width, t.height = Inches(0.92), Inches(0.40), Inches(11.52), Inches(2.90)
t.fill.solid(); t.fill.fore_color.rgb = RED; t.line.color.rgb = WHITE
tf = t.text_frame; tf.text = ""; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
_run(p, "RSA and Shor’s Algorithm", size=40, color=WHITE, bold=True)
p = tf.add_paragraph(); p.alignment = PP_ALIGN.CENTER
_run(p, "Public-key cryptography, and how a quantum computer breaks it", size=28, color=WHITE)
textbox(s, 0.68, 4.15, 11.98, 1.6, [
    {"t": "Roberto Cappuccio", "align": "c", "size": 24},
    {"t": "Istituto Nazionale di Fisica Nucleare - Pisa", "align": "c", "size": 24},
], color=BLUE)
textbox(s, 0.68, 5.9, 11.98, 0.9, [
    {"t": "Quantum Computing course 2026-27  ·  Laurea Magistrale in Fisica", "align": "c", "size": 18, "color": GREY},
    {"t": "Companion material: rsa_shor_lesson.pdf  ·  22_Shor_Period_Finding_to_RSA.ipynb (IBM Aer simulator / IQM Garnet & Emerald)", "align": "c", "size": 14, "color": GREY},
])

# 2 ---------------------------------------------------------------- roadmap
s = new_slide("Roadmap", notes="Four blocks, ~90 minutes. The number theory is the toolbox; RSA is the construction; Shor is the demolition. The last block is hands-on with the notebook.")
rows = [
    ("1", "Public-key cryptography", "the key-distribution problem, trapdoor one-way functions"),
    ("2", "Number-theory toolbox", "Bézout & modular inverses, Euler’s φ, Fermat/Euler theorems, CRT"),
    ("3", "RSA", "key generation, why decryption works, a worked example, security = factoring"),
    ("4", "Shor’s algorithm", "factoring → order finding, QPE, continued fractions, demo on a simulator and on IQM hardware"),
]
y0 = 1.65
for i, (n, head, sub) in enumerate(rows):
    y = y0 + i * 1.3
    rect(s, 0.9, y, 0.85, 0.85, fill=RED, line=None, shape=MSO_SHAPE.OVAL, name=f"Step{n}")
    textbox(s, 0.9, y, 0.85, 0.85, [{"t": n, "align": "c", "bold": True}], size=28, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, margin=0)
    arrow(s, 2.0, y + 0.17, 0.9, 0.5)
    textbox(s, 3.1, y - 0.05, 9.4, 1.0, [
        {"t": head, "bold": True, "size": 26, "after": 2},
        {"t": sub, "size": 18, "color": GREY},
    ], size=20)

# 3 ---------------------------------------------------------------- symmetric vs asymmetric
s = new_slide("Symmetric vs. asymmetric cryptography", notes="Symmetric ciphers are fast but need a shared secret: n parties need n(n-1)/2 keys. Public-key cryptography (Diffie-Hellman 1976, RSA 1977) removes the problem: encrypt with the public key, decrypt with the private key.")
card(s, 0.7, 1.6, 5.8, 4.2, "Symmetric (AES, ChaCha20, …)", [
    {"t": "One secret key k encrypts and decrypts:", "after": 2},
    {"math": r"c = E_{k}(m), \qquad m = D_{k}(c)", "size": 20, "color": NAVY, "align": "c"},
    {"t": "Fast (GB/s), used for the bulk of every TLS connection", "bullet": True},
    {"t": "Key-distribution problem: Alice and Bob must already share k over a secure channel", "bullet": True},
    {"t": [("n parties → ", {}), ("n(n−1)/2", {"bold": True, "color": RED}), (" shared keys", {})], "bullet": True},
], size=17)
card(s, 6.85, 1.6, 5.8, 4.2, "Asymmetric / public-key (Diffie–Hellman 1976, RSA 1977)", [
    {"t": "Each party publishes pk and keeps sk:", "after": 2},
    {"math": r"c = E_{\mathrm{pk}}(m), \qquad m = D_{\mathrm{sk}}(c)", "size": 20, "color": NAVY, "align": "c"},
    {"t": "Anyone can encrypt to Bob with his public key", "bullet": True},
    {"t": "Only Bob, holder of the private key, can decrypt", "bullet": True},
    {"t": [("n parties → ", {}), ("n", {"bold": True, "color": GREEN}), (" key pairs, no secure channel needed", {})], "bullet": True},
], size=17, fill=LIGHTBLUE)
rect(s, 0.7, 6.05, 11.95, 0.95, fill=LIGHTRED, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
textbox(s, 0.9, 6.05, 11.6, 0.95, [
    {"t": [("1 000 users: ", {"bold": True}), ("499 500", {"bold": True, "color": RED, "size": 24}), (" symmetric keys vs ", {}),
           ("1 000", {"bold": True, "color": GREEN, "size": 24}), (" public/private pairs. In practice: public-key crypto exchanges a symmetric session key, which then does the heavy lifting.", {})]},
], size=17, color=GREY, anchor=MSO_ANCHOR.MIDDLE)

# 4 ---------------------------------------------------------------- trapdoor
s = new_slide("Trapdoor one-way functions", notes="RSA's trapdoor is the factorisation of the modulus. Multiplying is easy, factoring is believed hard classically. Shor's algorithm removes the asymmetry: that is the whole story of this lecture.")
card(s, 0.7, 1.6, 11.95, 1.55, "Definition", [
    {"t": [("A function f is ", {}), ("one-way", {"bold": True}), (" if y = f(x) is easy to compute but x = f⁻¹(y) is computationally infeasible. It is a ", {}),
           ("trapdoor", {"bold": True}), (" one-way function if some extra secret information (the trapdoor) makes inverting f easy again.", {})]},
], size=17, fill=LIGHTBLUE)
# diagram: p,q  --multiply-->  N
rect(s, 1.3, 3.75, 2.6, 1.3, fill=NAVY, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
textbox(s, 1.3, 3.75, 2.6, 1.3, [{"t": "two primes", "align": "c", "size": 16}, {"t": "p ,  q", "align": "c", "size": 30, "bold": True}], color=WHITE, anchor=MSO_ANCHOR.MIDDLE, after=0)
rect(s, 9.4, 3.75, 2.6, 1.3, fill=NAVY, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
textbox(s, 9.4, 3.75, 2.6, 1.3, [{"t": "modulus", "align": "c", "size": 16}, {"t": "N = p·q", "align": "c", "size": 30, "bold": True}], color=WHITE, anchor=MSO_ANCHOR.MIDDLE, after=0)
arrow(s, 4.2, 3.55, 4.9, 0.7, fill=GREEN)
textbox(s, 4.2, 3.55, 4.9, 0.7, [{"t": "multiply: easy, O(n²)", "align": "c", "bold": True}], size=17, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, margin=0)
arrow(s, 4.2, 4.55, 4.9, 0.7, fill=RED, shape=MSO_SHAPE.LEFT_ARROW)
textbox(s, 4.2, 4.55, 4.9, 0.7, [{"t": "factor: hard (classically)", "align": "c", "bold": True}], size=17, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, margin=0)
textbox(s, 0.7, 5.4, 11.95, 1.6, [
    {"t": [("For RSA the trapdoor is the ", {}), ("factorisation of the modulus", {"bold": True}), (": whoever knows p and q can compute the private key; whoever only knows N (everybody) cannot — as far as classical computers go.", {})], "after": 8},
    {"t": [("Shor’s algorithm (1994) destroys this asymmetry on a quantum computer.", {"bold": True, "color": RED})]},
], size=18)

# 5 ---------------------------------------------------------------- Bezout
s = new_slide("Modular arithmetic, Bézout and inverses", notes="Everything in RSA lives in Z/NZ. Bézout gives the modular inverse, computed by the extended Euclidean algorithm in O(log) steps. This is exactly how the public exponent e becomes the private exponent d.")
textbox(s, 0.7, 1.5, 11.95, 1.0, [
    {"t": [("Notation: ", {"bold": True}), ("a ≡ b (mod n) means n | (a − b). The residues Z/nZ = {0, 1, …, n−1} form a commutative ring under + and × modulo n.", {})]},
], size=18)
card(s, 0.7, 2.5, 6.1, 2.55, "Theorem (Bézout’s identity)", [
    {"t": "For integers a, b not both zero there exist integers x, y with", "after": 2},
    {"math": r"a x + b y = \mathrm{gcd}(a, b)", "size": 22, "color": NAVY, "align": "c"},
    {"t": "x, y are computed in O(log min(a, b)) steps by the extended Euclidean algorithm.", "after": 0},
], size=16, fill=LIGHTBLUE)
card(s, 7.0, 2.5, 5.65, 2.55, "Proof idea", [
    {"t": "Let d = ax₀ + by₀ be the least positive element of S = {ax + by}. Divide a by d: a = qd + r with 0 ≤ r < d. Then r = a(1 − qx₀) − b(qy₀) ∈ S ∪ {0}, so minimality forces r = 0: d | a, and likewise d | b. Hence d | gcd(a, b); conversely gcd(a, b) divides every ax + by. So d = gcd(a, b).  ∎"},
], size=14, color=GREY)
card(s, 0.7, 5.2, 11.95, 1.75, "Corollary (modular inverses)", [
    {"t": [("a ∈ Z/nZ has an inverse a⁻¹ (with a·a⁻¹ ≡ 1 mod n) ", {}), ("iff gcd(a, n) = 1", {"bold": True}), (". The inverse is the coefficient x in ax + ny = 1, reduced mod n.", {})], "after": 4},
    {"t": [("This is how RSA turns the public exponent into the private one:  ", {}), ("d ≡ e⁻¹ (mod φ(N))", {"bold": True, "color": RED}), (".", {})]},
], size=16, fill=LIGHT)

# 6 ---------------------------------------------------------------- units & totient
s = new_slide("Units and Euler’s totient function", notes="The units form a group of order phi(n). For a product of two distinct primes phi(pq) = (p-1)(q-1): inclusion-exclusion on the multiples of p and q.")
card(s, 0.7, 1.55, 5.85, 2.3, "Definition (group of units)", [
    {"t": "The invertible residues", "after": 2},
    {"math": r"(\mathbb{Z}/n\mathbb{Z})^{*} = \{\, a : 1 \le a \le n,\ \mathrm{gcd}(a, n) = 1 \,\}", "size": 20, "color": NAVY, "align": "c"},
    {"t": "form an abelian group under multiplication modulo n.", "after": 0},
], size=16, fill=LIGHTBLUE)
card(s, 6.8, 1.55, 5.85, 2.3, "Definition (Euler’s totient)", [
    {"math": r"\varphi(n) = \left| (\mathbb{Z}/n\mathbb{Z})^{*} \right|", "size": 22, "color": NAVY, "align": "c"},
    {"t": "= the number of integers in {1, …, n} coprime to n.", "after": 4},
    {"t": "φ(p) = p − 1 for a prime p;  φ is multiplicative: φ(mn) = φ(m)φ(n) when gcd(m, n) = 1.", "after": 0},
], size=16, fill=LIGHTBLUE)
card(s, 0.7, 4.05, 7.6, 2.9, "Proposition — the case RSA needs", [
    {"t": "If p ≠ q are primes then", "after": 2},
    {"math": r"\varphi(pq) = (p-1)(q-1)", "size": 24, "color": RED, "align": "c"},
    {"t": [("Proof sketch. ", {"bold": True}), ("Among {1, …, pq} the numbers not coprime to pq are the q multiples of p and the p multiples of q, with pq counted twice: φ(pq) = pq − p − q + 1 = (p − 1)(q − 1).  ∎", {})], "after": 0},
], size=16)
card(s, 8.55, 4.05, 4.1, 2.9, "Examples", [
    {"t": "φ(55) = 4 · 10 = 40", "bullet": True},
    {"t": "φ(3233) = 60 · 52 = 3120", "bullet": True},
    {"t": "φ(15) = 2 · 4 = 8", "bullet": True},
    {"t": "φ(561) = 2·10·16 = 320  (561 = 3·11·17)", "bullet": True},
], size=16, fill=LIGHT)

# 7 ---------------------------------------------------------------- Fermat & Euler
s = new_slide("Fermat’s little theorem and Euler’s theorem", notes="Lagrange: the order of an element divides the order of the group. That is the whole proof of Euler's theorem; Fermat is the special case n = p. This is the engine of RSA: exponents can be reduced modulo phi(N).")
card(s, 0.7, 1.55, 5.85, 2.4, "Theorem (Fermat’s little theorem, 1640)", [
    {"t": "If p is prime and p ∤ a, then", "after": 2},
    {"math": r"a^{\,p-1} \equiv 1 \pmod{p}", "size": 24, "color": NAVY, "align": "c"},
    {"t": "Equivalently aᵖ ≡ a (mod p) for every integer a.", "after": 0},
], size=16, fill=LIGHTBLUE)
card(s, 6.8, 1.55, 5.85, 2.4, "Theorem (Euler, 1763)", [
    {"t": "If gcd(a, n) = 1, then", "after": 2},
    {"math": r"a^{\,\varphi(n)} \equiv 1 \pmod{n}", "size": 24, "color": NAVY, "align": "c"},
    {"t": "Fermat is the special case n = p, φ(p) = p − 1.", "after": 0},
], size=16, fill=LIGHTBLUE)
card(s, 0.7, 4.15, 7.3, 2.8, "Proof (one line of group theory)", [
    {"t": "Work in the finite abelian group (Z/nZ)* of order φ(n). By Lagrange’s theorem the order of any element divides the order of the group, so a^φ(n) = 1 in (Z/nZ)*, i.e. a^φ(n) ≡ 1 (mod n).  ∎", "after": 8},
    {"t": [("Euler’s theorem is the engine of RSA: ", {"bold": True, "color": RED}), ("raising to the power φ(N) acts as the identity on units, so exponents can be reduced modulo φ(N).", {})]},
], size=16)
card(s, 8.25, 4.15, 4.4, 2.8, "Try it", [
    {"t": "n = 15, φ(15) = 8, a = 7:", "after": 2},
    {"t": "7¹=7, 7²=49≡4, 7³≡28≡13, 7⁴≡91≡1", "after": 2},
    {"t": "so 7⁸ ≡ 1 as Euler promises — and in fact already 7⁴ ≡ 1: the order of 7 is 4, a divisor of 8.", "after": 6},
    {"t": [("Keep r = 4 in mind: Shor will measure it.", {"bold": True, "color": RED})]},
], size=15, fill=LIGHT)

# 8 ---------------------------------------------------------------- CRT
s = new_slide("The Chinese Remainder Theorem", notes="CRT is used twice: to prove RSA correct (combine the mod p and mod q congruences) and to speed up real RSA decryption by about 4x.")
card(s, 0.7, 1.55, 11.95, 2.55, "Theorem (CRT)", [
    {"t": "If gcd(m, n) = 1, the system  x ≡ a (mod m),  x ≡ b (mod n)  has a unique solution modulo mn. Equivalently the map", "after": 2},
    {"math": r"\mathbb{Z}/mn\mathbb{Z} \longrightarrow \mathbb{Z}/m\mathbb{Z} \times \mathbb{Z}/n\mathbb{Z}, \qquad x \longmapsto (x \bmod m,\ x \bmod n)", "size": 22, "color": NAVY, "align": "c"},
    {"t": "is a ring isomorphism (and hence a bijection of unit groups: this is why φ is multiplicative).", "after": 0},
], size=16, fill=LIGHTBLUE)
card(s, 0.7, 4.3, 5.85, 2.65, "Why we need it", [
    {"t": [("To prove RSA correct: ", {"bold": True}), ("we show m^ed ≡ m modulo p and modulo q separately, then CRT glues the two into a congruence modulo N = pq.", {})], "bullet": True},
    {"t": [("To speed RSA up: ", {"bold": True}), ("decrypting modulo p and q separately (two exponentiations with half-size numbers) is ≈ 4× faster than modulo N. Every real implementation does it.", {})], "bullet": True},
], size=15)
card(s, 6.8, 4.3, 5.85, 2.65, "Example (used later to decrypt by hand)", [
    {"t": "Solve  x ≡ 2 (mod 5),  x ≡ 7 (mod 11).", "after": 4},
    {"t": "Candidates ≡ 7 mod 11: 7, 18, 29, 40, 51 …", "bullet": True},
    {"t": "7 ≡ 2 (mod 5) already  →  x = 7 (unique mod 55).", "bullet": True},
    {"t": "Textbook formula: x = a·n·(n⁻¹ mod m) + b·m·(m⁻¹ mod n)  mod mn.", "bullet": True, "size": 14},
], size=15, fill=LIGHT)

# 9 ---------------------------------------------------------------- RSA key generation
s = new_slide("RSA — key generation (Recipe R1)", notes="Five steps. The security-relevant secrets are p, q and phi(N); knowing any one of them breaks the scheme. Note the role of each theorem: Bezout gives d, Euler/CRT will prove correctness.")
steps = [
    ("1", "Choose two large distinct primes p, q", "e.g. 1024 bits each for a 2048-bit key"),
    ("2", "Compute N = p·q and φ(N) = (p − 1)(q − 1)", "N is public, φ(N) is secret"),
    ("3", "Choose a public exponent e with 1 < e < φ(N), gcd(e, φ(N)) = 1", "commonly e = 65537 — next slide"),
    ("4", "Compute d ≡ e⁻¹ (mod φ(N))", "extended Euclidean algorithm (Bézout)"),
    ("5", "Public key pk = (N, e)      Private key sk = (N, d)", "discard or guard p, q, φ(N): knowing any of them breaks the scheme"),
]
for i, (n, head, sub) in enumerate(steps):
    y = 1.55 + i * 0.93
    rect(s, 0.8, y + 0.05, 0.65, 0.65, fill=RED, line=None, shape=MSO_SHAPE.OVAL)
    textbox(s, 0.8, y + 0.05, 0.65, 0.65, [{"t": n, "align": "c", "bold": True}], size=20, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, margin=0)
    textbox(s, 1.65, y - 0.05, 6.9, 0.9, [{"t": head, "bold": True, "size": 19, "after": 0}, {"t": sub, "size": 14, "color": GREY}], size=18)
card(s, 8.8, 1.55, 3.85, 4.6, "Encrypt / decrypt", [
    {"t": "message m with 0 ≤ m < N", "after": 6},
    {"math": r"c = m^{e} \bmod N", "size": 24, "color": NAVY, "align": "c"},
    {"math": r"m = c^{d} \bmod N", "size": 24, "color": NAVY, "align": "c"},
    {"t": "Both are one modular exponentiation: square-and-multiply, O((log N)³) bit operations.", "after": 4, "size": 14},
], size=16, fill=LIGHTBLUE)
textbox(s, 1.65, 6.3, 11.0, 0.7, [{"t": [("Signatures run the same trapdoor backwards: ", {"bold": True}), ("σ = m^d mod N is produced with the private key and verified by anyone via σ^e ≡ m (mod N).", {})]}], size=15, color=GREY)

# 10 --------------------------------------------------------------- why 65537
s = new_slide("Why is the public exponent usually e = 65537?", notes="65537 = 2^16 + 1 is the fourth Fermat prime F4. Its binary expansion has only two 1 bits, so square-and-multiply costs 16 squarings and one multiplication. Being prime, gcd(e, phi(N)) = 1 unless 65537 divides phi(N). It is large enough to avoid the low-exponent attacks that bite e = 3, and it is the value fixed by the standards, so every library agrees.")
textbox(s, 0.7, 1.5, 11.95, 1.0, [
    {"math": r"65537 = 2^{16} + 1 = F_{4} = 1\,0000\,0000\,0000\,0000\,1_{2}", "size": 24, "color": NAVY, "align": "c", "after": 2},
    {"t": "the fourth (and largest known) Fermat prime — a 17-bit number with only two 1-bits", "align": "c", "size": 15, "color": GREY},
], size=18)
card(s, 0.7, 2.55, 3.85, 3.0, "1 · Fast", [
    {"t": "Square-and-multiply follows the bits of e: only two 1-bits →", "after": 2},
    {"t": [("16 squarings + 1 multiplication", {"bold": True, "color": RED})], "after": 4},
    {"t": "Encryption and signature verification (the operations done by every client) are almost free; the cost sits in d, which is ~2048 random bits anyway.", "size": 14, "after": 0},
], size=15, fill=LIGHTBLUE)
card(s, 4.75, 2.55, 3.85, 3.0, "2 · Always invertible", [
    {"t": "Recipe R1 needs gcd(e, φ(N)) = 1.", "after": 4},
    {"t": [("e prime ⇒ ", {}), ("fails only if 65537 | φ(N)", {"bold": True, "color": RED})], "after": 4},
    {"t": "i.e. only if p ≡ 1 or q ≡ 1 (mod 65537): probability ≈ 2/65537 — then just pick another prime.", "size": 14, "after": 0},
], size=15, fill=LIGHTBLUE)
card(s, 8.8, 2.55, 3.85, 3.0, "3 · Large enough to be safe", [
    {"t": "Tiny e (e = 3) is even faster but exposes textbook RSA to low-exponent attacks:", "after": 4},
    {"t": "if m³ < N the cipher-text is m³ exactly — take a cube root", "bullet": True, "size": 14},
    {"t": "Håstad broadcast / Coppersmith: same m sent to e recipients", "bullet": True, "size": 14},
    {"t": "65537 leaves no such room and costs only 17 operations.", "size": 14, "after": 0},
], size=15, fill=LIGHTBLUE)
tbl_rows = [("e", "1-bits", "squarings + multiplications", "remarks"),
            ("3", "2", "1 + 1", "fastest; unsafe without proper padding"),
            ("17", "2", "4 + 1", "used in small textbook examples (N = 3233)"),
            ("65537", "2", "16 + 1", "the standard choice (PKCS #1, FIPS 186, every TLS certificate)"),
            ("random 2048-bit", "≈1024", "2047 + ≈1023", "no benefit: security does not depend on e being random")]
tb = s.shapes.add_table(len(tbl_rows), 4, Inches(0.7), Inches(5.7), Inches(11.95), Inches(1.3)).table
tb.columns[0].width = Inches(2.2); tb.columns[1].width = Inches(1.3); tb.columns[2].width = Inches(3.0); tb.columns[3].width = Inches(5.45)
for r, row in enumerate(tbl_rows):
    for c, val in enumerate(row):
        cell = tb.cell(r, c); cell.text = ""
        p = cell.text_frame.paragraphs[0]
        _run(p, val, size=12 if r else 12, color=WHITE if r == 0 else (RED if row[0] == "65537" else GREY), bold=(r == 0 or row[0] == "65537"))
        cell.margin_top = cell.margin_bottom = Inches(0.02)
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY if r == 0 else (LIGHTRED if row[0] == "65537" else (LIGHT if r % 2 else WHITE))
for r in range(len(tbl_rows)):
    tb.rows[r].height = Inches(0.26)

# 11 --------------------------------------------------------------- correctness
s = new_slide("Why decryption works — RSA correctness", notes="ed = 1 + k phi(N). Modulo p: either p | m (trivial) or Fermat gives m^(p-1) = 1 and (p-1) divides phi(N). Same modulo q. CRT combines. Note that the proof covers m not coprime to N as well.")
card(s, 0.7, 1.55, 11.95, 1.45, "Theorem (RSA correctness)", [
    {"t": "With the parameters of Recipe R1, for every integer m with 0 ≤ m < N:", "after": 2},
    {"math": r"\left(m^{e}\right)^{d} \equiv m \pmod{N}", "size": 24, "color": RED, "align": "c"},
], size=16, fill=LIGHTBLUE)
card(s, 0.7, 3.15, 3.8, 3.8, "Step 0 — unpack d", [
    {"t": "By construction ed ≡ 1 (mod φ(N)), so", "after": 2},
    {"math": r"ed = 1 + k\,\varphi(N) = 1 + k(p-1)(q-1)", "size": 18, "color": NAVY, "align": "c"},
    {"t": "for some integer k ≥ 0.", "after": 0},
], size=15)
card(s, 4.75, 3.15, 3.8, 3.8, "Step 1 — modulo p", [
    {"t": "If p | m: m^ed ≡ 0 ≡ m (mod p). Otherwise gcd(m, p) = 1 and Fermat gives m^(p−1) ≡ 1, so", "after": 2},
    {"math": r"m^{ed} = m\cdot\left(m^{\,p-1}\right)^{k(q-1)} \equiv m \pmod{p}", "size": 17, "color": NAVY, "align": "c"},
    {"t": "Step 2 — modulo q: identical argument.", "bold": True, "after": 0},
], size=15)
card(s, 8.8, 3.15, 3.85, 3.8, "Step 3 — CRT", [
    {"t": "m^ed − m is divisible by both p and q, which are coprime, hence by N = pq:", "after": 2},
    {"math": r"m^{ed} \equiv m \pmod{N} \quad\blacksquare", "size": 18, "color": NAVY, "align": "c"},
    {"t": "Everything used: Bézout (d exists), Fermat (the exponent collapses), CRT (glue).", "after": 0, "color": RED, "bold": True},
], size=15)

# 12 --------------------------------------------------------------- worked example
s = new_slide("RSA by hand: p = 5, q = 11", notes="Small enough to do live on the board. Decryption uses CRT and Fermat to keep the numbers tiny: 3^27 mod 5 reduces the exponent mod 4, 2^27 mod 11 reduces it mod 10.")
card(s, 0.7, 1.55, 3.85, 5.4, "Key generation", [
    {"t": "N = 5 · 11 = 55", "bullet": True},
    {"t": "φ(N) = 4 · 10 = 40", "bullet": True},
    {"t": "e = 3  (gcd(3, 40) = 1)", "bullet": True},
    {"t": "d: 3d ≡ 1 (mod 40). Since 3·27 = 81 = 2·40 + 1, d = 27", "bullet": True},
    {"t": [("pk = (55, 3)", {"bold": True, "color": GREEN})], "after": 2},
    {"t": [("sk = (55, 27)", {"bold": True, "color": RED})]},
], size=16, fill=LIGHTBLUE)
card(s, 4.75, 1.55, 3.85, 5.4, "Encrypt m = 7", [
    {"math": r"c = 7^{3} \bmod 55 = 343 \bmod 55 = 13", "size": 16, "color": NAVY, "align": "l"},
    {"t": "343 = 6·55 + 13", "size": 14, "color": GREY, "after": 10},
    {"t": "Decrypt c = 13 (with CRT)", "bold": True, "size": 18, "color": NAVY, "after": 4},
    {"t": "mod 5: 13 ≡ 3,  3²⁷ ≡ 3^(27 mod 4) = 3³ = 27 ≡ 2", "bullet": True, "size": 14},
    {"t": "mod 11: 13 ≡ 2,  2²⁷ ≡ 2^(27 mod 10) = 2⁷ = 128 ≡ 7", "bullet": True, "size": 14},
    {"t": "CRT: x ≡ 2 (mod 5), x ≡ 7 (mod 11)  ⇒  x = 7  ✓", "bullet": True, "size": 14},
], size=16)
card(s, 8.8, 1.55, 3.85, 5.4, "The textbook ‘big’ example", [
    {"t": "(18_RSA.ipynb in the course repo)", "size": 13, "color": GREY, "after": 6},
    {"t": "p = 61, q = 53 → N = 3233", "bullet": True},
    {"t": "φ(N) = 60 · 52 = 3120", "bullet": True},
    {"t": "e = 17, d = 2753  (17 · 2753 = 46801 = 15·3120 + 1)", "bullet": True},
    {"t": "m = 65 → c = 65¹⁷ mod 3233 = 2790", "bullet": True},
    {"t": "2790²⁷⁵³ mod 3233 = 65  ✓", "bullet": True},
    {"t": "Real keys: N has ~617 decimal digits.", "size": 14, "color": RED, "bold": True, "after": 0},
], size=15, fill=LIGHT)

# 13 --------------------------------------------------------------- security
s = new_slide("Security: what an attacker must do", notes="Knowing phi(N) is equivalent to factoring: p+q = N - phi(N) + 1 and p, q are the roots of a quadratic. So everything rests on factoring. The best classical algorithm, GNFS, is sub-exponential; the record is RSA-250 (829 bits, 2020, ~2700 core-years).")
card(s, 0.7, 1.55, 6.3, 2.75, "Proposition — knowing φ(N) is as hard as factoring", [
    {"t": "Given N = pq, recovering φ(N) is computationally equivalent to factoring N.", "after": 4},
    {"t": [("Proof. ", {"bold": True}), ("From φ(N) = N − (p + q) + 1 we get s := p + q = N − φ(N) + 1; then p, q are the roots of", {})], "after": 2},
    {"math": r"t^{2} - s\,t + N = 0, \qquad p, q = \frac{s \pm \sqrt{s^{2} - 4N}}{2} \quad\blacksquare", "size": 18, "color": NAVY, "align": "c"},
], size=15, fill=LIGHTBLUE)
card(s, 7.25, 1.55, 5.4, 2.75, "Best classical attack", [
    {"t": "General Number Field Sieve — sub-exponential but super-polynomial:", "after": 2},
    {"math": r"\exp\!\left( O\!\left( (\log N)^{1/3} (\log\log N)^{2/3} \right) \right)", "size": 18, "color": NAVY, "align": "c"},
    {"t": [("Record: RSA-250 (829 bits), 2020, ≈ 2 700 core-years. RSA-2048 is far out of reach.", {"bold": True, "color": RED})], "size": 14, "after": 0},
], size=15)
card(s, 0.7, 4.5, 11.95, 2.45, "Textbook RSA vs real RSA", [
    {"t": "Textbook RSA as above is deterministic, hence insecure in practice: equal messages give equal cipher-texts; a small m with e = 3 may satisfy m³ < N so c = m³ exactly; chosen-cipher-text tricks exploit multiplicativity (c₁c₂ = (m₁m₂)^e).", "after": 6},
    {"t": [("Real deployments add randomised padding — RSA-OAEP for encryption, RSA-PSS for signatures — and use e = 65537. ", {"bold": True}),
           ("None of this changes the number theory: the security still reduces to the integer-factorisation problem.", {})], "after": 0},
], size=15, fill=LIGHT)

# 14 --------------------------------------------------------------- Shor overview
s = new_slide("Shor’s algorithm (1994)", notes="Structure first: a classical reduction (factoring to order finding) wrapping a single quantum subroutine (order finding by phase estimation). Polynomial in log N, versus sub-exponential for GNFS.")
picture(s, SHOR_PHOTO, 10.3, 1.5, w=2.35, name="ShorPhoto")
textbox(s, 10.3, 2.85, 2.35, 0.4, [{"t": "Peter Shor, 1994", "align": "c"}], size=12, color=BLUE)
textbox(s, 0.7, 1.5, 9.3, 1.2, [
    {"t": [("Factors N in time polynomial in log N on a quantum computer — ", {}), ("breaking RSA asymptotically.", {"bold": True, "color": RED})], "after": 4},
    {"t": "Its heart is a purely classical reduction wrapped around one quantum subroutine:", "after": 0},
], size=18)
boxes = [("Classical", "pick a random a,\ncheck gcd(a, N)", NAVY), ("Quantum", "find the order r of a:\na^r ≡ 1 (mod N)\n(phase estimation + continued fractions)", RED),
         ("Classical", "if r even and a^(r/2) ≢ −1:\nfactors = gcd(a^(r/2) ± 1, N)", NAVY)]
for i, (lab, body, colr) in enumerate(boxes):
    x = 0.7 + i * 3.25
    rect(s, x, 3.0, 2.85, 1.9, fill=colr, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
    textbox(s, x, 3.0, 2.85, 1.9, [{"t": lab, "align": "c", "bold": True, "size": 18, "after": 4}] +
            [{"t": line, "align": "c", "size": 14, "after": 0} for line in body.split("\n")], color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    if i < 2:
        arrow(s, x + 2.9, 3.7, 0.3, 0.5, fill=GREY)
textbox(s, 0.7, 5.15, 9.3, 1.9, [
    {"t": [("Cost: ", {"bold": True}), ("Õ((log N)²) quantum gates and O(log N) qubits per run, plus O((log N)³) classical post-processing — polynomial in the input size.", {})], "bullet": True},
    {"t": [("It is probabilistic: ", {"bold": True}), ("each run succeeds with constant probability; failures are detected cheaply and the run is repeated.", {})], "bullet": True},
    {"t": [("Same machinery solves discrete logarithms", {"bold": True}), (" — so Diffie–Hellman and elliptic-curve cryptography fall too.", {})], "bullet": True},
], size=16)

# 15 --------------------------------------------------------------- step 1
s = new_slide("Step 1 — reduce factoring to order finding", notes="The whole quantum part is only needed to find r. The theorem is elementary: N divides (x-1)(x+1) but neither factor, so its primes split between the two gcds.")
card(s, 0.7, 1.55, 4.3, 1.9, "Definition (multiplicative order)", [
    {"t": "For a with gcd(a, N) = 1, the order r = ord_N(a) is the smallest positive integer with", "after": 2},
    {"math": r"a^{r} \equiv 1 \pmod{N}", "size": 20, "color": NAVY, "align": "c"},
], size=15, fill=LIGHTBLUE)
card(s, 5.2, 1.55, 7.45, 1.9, "Theorem (order finding yields factors)", [
    {"t": [("Let N be odd and composite, a coprime to N with order r. If ", {}), ("(i) r is even", {"bold": True}), (" and ", {}), ("(ii) a^(r/2) ≢ −1 (mod N)", {"bold": True}), (", then", {})], "after": 2},
    {"math": r"\mathrm{gcd}\!\left(a^{r/2} - 1,\, N\right) \quad\text{and}\quad \mathrm{gcd}\!\left(a^{r/2} + 1,\, N\right)", "size": 18, "color": RED, "align": "c", "after": 2},
    {"t": "are non-trivial factors of N.", "bold": True, "color": RED, "align": "c", "after": 0},
], size=15, fill=LIGHTBLUE)
card(s, 0.7, 3.65, 7.45, 3.3, "Proof", [
    {"t": "Set x = a^(r/2) mod N. Then x² = a^r ≡ 1, so", "after": 2},
    {"math": r"N \mid x^{2} - 1 = (x-1)(x+1)", "size": 20, "color": NAVY, "align": "c"},
    {"t": "If N divided x − 1 we would have x ≡ 1, contradicting the minimality of r (since r/2 < r). If N divided x + 1 we would have x ≡ −1, excluded by (ii). Hence N divides the product but neither factor: its prime factors are split between x − 1 and x + 1, and gcd(x − 1, N) is a proper divisor > 1 of N (and so is gcd(x + 1, N)).  ∎", "after": 0},
], size=15)
card(s, 8.4, 3.65, 4.25, 3.3, "Why (i) and (ii) matter", [
    {"t": "r odd → a^(r/2) is not an integer power: no square root of 1 to exploit.", "bullet": True},
    {"t": "a^(r/2) ≡ −1 → the trivial square root of 1: both gcds are N and 1.", "bullet": True},
    {"t": [("Either failure → pick another a.", {"bold": True, "color": RED})], "after": 0},
], size=15, fill=LIGHT)

# 16 --------------------------------------------------------------- gamble
s = new_slide("The gamble usually pays off", notes="With k distinct odd prime factors the two conditions hold with probability at least 1 - 2^(-k) >= 1/2 for a random a. Example on the board: a = 3, N = 35, r = 12. The plot is the periodic function 3^x mod 35 from the notebook.")
card(s, 0.7, 1.55, 6.0, 2.0, "Lemma", [
    {"t": "If N has k distinct odd prime factors and a is drawn uniformly from (Z/NZ)*, then conditions (i)–(ii) both hold with probability at least", "after": 2},
    {"math": r"1 - 2^{-k} \;\ge\; \tfrac{1}{2}", "size": 22, "color": NAVY, "align": "c"},
], size=15, fill=LIGHTBLUE)
textbox(s, 0.7, 3.6, 6.0, 1.1, [{"t": "So two or three random choices of a suffice on average; if a fails, pick another. (Idea of proof: by CRT the order of a mod N combines the orders modulo each prime, and the ‘bad’ cases need all their 2-adic parts to line up.)"}], size=13, color=GREY)
card(s, 0.7, 4.75, 6.0, 2.2, "Example: N = 35, a = 3", [
    {"t": "Powers of 3 mod 35: 3, 9, 27, 11, 33, 29, 17, 16, 13, 4, 12, 1  →  r = 12 (even ✓)", "after": 2},
    {"math": r"3^{6} = 729 \equiv 29 \not\equiv -1 \pmod{35} \ \checkmark", "size": 17, "color": NAVY, "align": "l"},
    {"math": r"\mathrm{gcd}(29-1, 35) = 7, \qquad \mathrm{gcd}(29+1, 35) = 5", "size": 17, "color": RED, "align": "l"},
], size=14)
picture(s, "assets/aer_cell3_1.png", 6.95, 1.55, w=5.7, name="PeriodicPlot")
textbox(s, 6.95, 5.9, 5.7, 1.0, [{"t": "The function x ↦ aˣ mod N is periodic with period r: finding r is a period-finding problem — exactly what the quantum Fourier transform is good at.", "align": "l"}], size=14, color=GREY)

# 17 --------------------------------------------------------------- U and eigenstates
s = new_slide("Step 2 — the operator U and its eigenstates", notes="U is a permutation of the residues, hence unitary. Its eigenphases are s/r: the order sits in the spectrum. We cannot prepare a single eigenstate, but |1> is their uniform superposition, and that is all QPE needs.")
textbox(s, 0.7, 1.5, 11.95, 1.0, [
    {"t": "Classically, finding r is as hard as factoring. Quantumly it is easy — via Quantum Phase Estimation of the modular-multiplication operator", "after": 2},
    {"math": r"U\,\ket{y} = \ket{a\,y \bmod N}, \qquad y \in \{0, 1, \dots, N-1\} \qquad\text{(a permutation of the residues ⇒ unitary)}", "size": 20, "color": NAVY, "align": "c"},
], size=16)
card(s, 0.7, 2.75, 7.0, 2.6, "Proposition (eigenstructure of U)", [
    {"t": "For each s ∈ {0, 1, …, r − 1} the state", "after": 2},
    {"math": r"\ket{u_s} = \frac{1}{\sqrt{r}} \sum_{k=0}^{r-1} e^{-2\pi i\, s k / r}\, \ket{a^{k} \bmod N}", "size": 19, "color": NAVY, "align": "c"},
    {"t": "is an eigenvector of U with eigenvalue e^{2πi s/r}. Moreover", "after": 2},
    {"math": r"U\ket{u_s} = e^{2\pi i\, s/r}\ket{u_s}, \qquad \frac{1}{\sqrt{r}} \sum_{s=0}^{r-1} \ket{u_s} = \ket{1}", "size": 19, "color": NAVY, "align": "c"},
], size=15, fill=LIGHTBLUE)
card(s, 7.9, 2.75, 4.75, 2.6, "Proof idea", [
    {"t": "U shifts a^k ↦ a^(k+1) inside the sum; re-indexing k ↦ k − 1 pulls out exactly the factor e^{2πi s/r}.", "bullet": True},
    {"t": "Summing |u_s⟩ over s, the phases Σ_s e^{−2πi sk/r} cancel for k ≢ 0 and reinforce for k = 0, leaving |a⁰⟩ = |1⟩.", "bullet": True},
], size=14, color=GREY)
card(s, 0.7, 5.5, 11.95, 1.45, "Two facts that make this usable", [
    {"t": [("The eigenphase φ_s = s/r ", {"bold": True}), ("contains the order", {"bold": True, "color": RED}), (". We cannot prepare one |u_s⟩ (we don’t know r) — but |1⟩ = r^(−1/2) Σ_s |u_s⟩ is trivial to prepare.", {})], "bullet": True},
    {"t": [("QPE on U with input |1⟩ therefore measures a phase φ ≈ s/r for a ", {}), ("uniformly random s ∈ {0, …, r − 1}", {"bold": True}), (".", {})], "bullet": True},
], size=15)

# 18 --------------------------------------------------------------- QPE circuit
s = new_slide("Step 2 — the quantum phase estimation circuit", notes="t counting qubits in |+>, work register in |1>, controlled U^(2^j), inverse QFT, measure. The read-out y/2^t approximates s/r. With t ~ 2 log2 N + 1 the estimate is sharp enough for continued fractions. The circuit shown is the notebook's for N = 15, a = 7 with t = 4.")
picture(s, "assets/qpe_circuit_t4.png", 0.7, 1.5, w=7.4, name="QPEcircuit")
textbox(s, 0.7, 5.35, 7.4, 0.5, [{"t": "22_Shor_Period_Finding_to_RSA.ipynb: build_order_finding_circuit(a=7, n_count=4) for N = 15 — counting register on top, 4-qubit work register below", "align": "c"}], size=12, color=GREY)
card(s, 8.35, 1.5, 4.3, 4.35, "Reading the circuit", [
    {"t": "t counting qubits → |+⟩^⊗t (Hadamards); work register → |1⟩ (one X)", "bullet": True},
    {"t": "controlled U^(2⁰), U^(2¹), …, U^(2^(t−1)): qubit j picks up the phase e^{2πi s·2^j/r}", "bullet": True},
    {"t": "inverse QFT turns the phases into a binary number", "bullet": True},
    {"t": "measure y ∈ {0, …, 2^t − 1}:", "bullet": True},
    {"math": r"\phi \approx \frac{y}{2^{t}} \approx \frac{s}{r}", "size": 20, "color": RED, "align": "c"},
    {"t": "t ≈ 2 log₂N + 1 counting qubits make φ sharp enough for the next step.", "after": 0},
], size=14, fill=LIGHTBLUE)
textbox(s, 0.7, 5.95, 11.95, 1.05, [
    {"t": [("Qubit budget: ", {"bold": True}), ("t + ⌈log₂N⌉ qubits here (8 + 4 = 12 for N = 15 in the notebook). Beauregard’s construction needs 2n + 3 qubits for an n-bit N.", {})], "bullet": True},
    {"t": [("Where the gates go: ", {"bold": True}), ("the controlled modular multiplications dominate — see ‘the bottleneck’ later.", {})], "bullet": True},
], size=15)

# 19 --------------------------------------------------------------- continued fractions
s = new_slide("Step 3 — recover r by continued fractions", notes="QPE returns a binary fraction close to s/r. The continued-fraction theorem says s/r is a convergent of phi provided the error is below 1/(2 r^2). In Python it is one call: Fraction(phi).limit_denominator(N). Three failure modes, all cheaply detected.")
card(s, 0.7, 1.55, 7.2, 2.55, "Theorem (continued-fraction recovery)", [
    {"t": "If a rational s/r with 0 ≤ s < r ≤ N is approximated by φ to within", "after": 2},
    {"math": r"\left| \phi - \frac{s}{r} \right| \le \frac{1}{2 r^{2}}", "size": 22, "color": NAVY, "align": "c"},
    {"t": "then s/r is one of the convergents of the continued-fraction expansion of φ, found in O(log N) steps.", "after": 0},
], size=15, fill=LIGHTBLUE)
card(s, 8.1, 1.55, 4.55, 2.55, "In code: one line", [
    {"t": "Fraction(phi).limit_denominator(N)", "font": "Courier New", "size": 14, "color": NAVY, "bold": True, "after": 6},
    {"t": "returns the best rational approximation to φ with denominator ≤ N — exactly the convergent above. Its denominator is the candidate r.", "after": 4},
    {"t": "Example: Fraction(0.75).limit_denominator(15) = 3/4  →  r = 4", "size": 13, "color": GREY, "after": 0},
], size=14)
card(s, 0.7, 4.3, 11.95, 2.65, "Why the algorithm is probabilistic — and why that is fine", [
    {"t": [("s = 0: ", {"bold": True}), ("φ = 0 carries no information.", {})], "bullet": True},
    {"t": [("gcd(s, r) > 1: ", {"bold": True}), ("we recover a divisor of r, not r itself (e.g. s/r = 2/4 → r′ = 2).", {})], "bullet": True},
    {"t": [("r odd, or a^(r/2) ≡ −1: ", {"bold": True}), ("the theorem of Step 1 does not apply.", {})], "bullet": True},
    {"t": [("Each failure is detected cheaply ", {"bold": True, "color": RED}), ("(test a^r ≡ 1? and the gcds) and we simply repeat with a new run or a new a. A constant number of repetitions gives any desired success probability.", {})], "bullet": True},
], size=15, fill=LIGHT)

# 20 --------------------------------------------------------------- recipe
s = new_slide("The complete recipe (S1)", notes="This is shor_factor(N) in the notebook, line by line. Steps 1, 2, 4, 5 are classical; only step 3 is quantum.")
steps = [
    ("1", "Classical shortcuts", "If N is even output 2. If N = cᵇ is a perfect power (checkable classically) output c.", NAVY),
    ("2", "Pick a random a ∈ {2, …, N − 1}", "Compute g = gcd(a, N). If g > 1 output g — a lucky factor, no quantum computer needed.", NAVY),
    ("3", "Quantum order finding", "QPE on U|y⟩ = |ay mod N⟩ with input |1⟩; measure φ ≈ s/r.", RED),
    ("4", "Continued fractions", "r = denominator of limit_denominator(φ, N). Verify aʳ ≡ 1 (mod N); if not, go to 2.", NAVY),
    ("5", "Extract the factors", "If r is even and a^(r/2) ≢ −1 (mod N), output gcd(a^(r/2) ± 1, N). Otherwise go to 2.", NAVY),
]
for i, (n, head, sub, colr) in enumerate(steps):
    y = 1.55 + i * 1.08
    rect(s, 0.8, y + 0.1, 0.65, 0.65, fill=colr, line=None, shape=MSO_SHAPE.OVAL)
    textbox(s, 0.8, y + 0.1, 0.65, 0.65, [{"t": n, "align": "c", "bold": True}], size=20, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, margin=0)
    textbox(s, 1.65, y - 0.02, 8.2, 1.05, [{"t": head, "bold": True, "size": 19, "after": 0, "color": colr}, {"t": sub, "size": 15, "color": GREY}], size=18)
card(s, 10.05, 1.55, 2.6, 5.3, "Legend", [
    {"t": [("■ classical", {"bold": True, "color": NAVY})], "after": 2},
    {"t": [("■ quantum", {"bold": True, "color": RED})], "after": 10},
    {"t": "Only step 3 runs on the QPU. Everything else is a few lines of Python.", "after": 8},
    {"t": "Notebook: shor_factor(N)", "font": "Courier New", "size": 12, "color": NAVY, "after": 0},
], size=14, fill=LIGHT)

# 21 --------------------------------------------------------------- example 15 ideal
s = new_slide("Example: factoring N = 15 with a = 7 on a simulator", notes="Ideal Aer simulation of the notebook circuit with 8 counting qubits: four equally likely outcomes 0, 64, 128, 192 i.e. phases 0, 1/4, 1/2, 3/4. Two of the four outcomes succeed. The histogram is exactly what the notebook shows.")
picture(s, "assets/hist_ideal.png", 0.7, 1.5, w=6.6, name="HistIdeal")
textbox(s, 0.7, 4.65, 6.6, 0.5, [{"t": "IBM/22_Shor_Period_Finding_to_RSA.ipynb on the Aer simulator — 8 counting qubits, 2048 shots", "align": "c"}], size=12, color=GREY)
card(s, 7.55, 1.5, 5.1, 3.6, "Reading the histogram", [
    {"t": "r = 4 (7¹=7, 7²≡4, 7³≡13, 7⁴≡1), so QPE returns φ ∈ {0, ¼, ½, ¾} with equal probability: register values {0, 64, 128, 192} out of 256.", "after": 6},
    {"t": [("φ = ¾: ", {"bold": True}), ("limit_denominator(15) → 3/4, r = 4 ✓", {})], "bullet": True},
    {"t": [("φ = ¼: ", {"bold": True}), ("→ 1/4, r = 4 ✓", {})], "bullet": True},
    {"t": [("φ = ½: ", {"bold": True}), ("→ 1/2, r = 2: but 7² ≢ 1 — rejected, retry", {})], "bullet": True},
    {"t": [("φ = 0: ", {"bold": True}), ("no information — retry", {})], "bullet": True},
], size=14, fill=LIGHTBLUE)
card(s, 0.7, 5.3, 11.95, 1.65, "Then the classical finish", [
    {"math": r"a^{r/2} = 7^{2} = 49 \equiv 4 \pmod{15}, \qquad \mathrm{gcd}(4-1, 15) = 3, \qquad \mathrm{gcd}(4+1, 15) = 5 \qquad\Longrightarrow\qquad 15 = 3 \times 5", "size": 17, "color": RED, "align": "c"},
], size=15)

# 22 --------------------------------------------------------------- noisy hardware
s = new_slide("The same circuit on a noisy 20-qubit device model", notes="Transpiled to IQM's native PRX + CZ gate set with Garnet's square-lattice connectivity: 12 qubits, about 600 native instructions, depth about 350. The four peaks survive but most shots land elsewhere. shor_factor still succeeds after a few retries. The user can run this on IQM Emerald via the TARGET line.")
picture(s, "assets/hist_noisy.png", 0.7, 1.5, w=6.6, name="HistNoisy")
textbox(s, 0.7, 4.65, 6.6, 0.5, [{"t": "IQM/22_Shor_Period_Finding_to_RSA.ipynb on fake_apollo — IQM’s noisy model of a 20-qubit Garnet-class chip", "align": "c"}], size=12, color=GREY)
card(s, 7.55, 1.5, 5.1, 3.6, "What the hardware sees", [
    {"t": "Transpiled to the native gate set (PRX + CZ) on a square lattice:", "after": 2},
    {"t": [("12 qubits · ≈ 600 native instructions · depth ≈ 350", {"bold": True, "color": RED})], "after": 6},
    {"t": "The four ideal peaks are still the four tallest bars, but most of the 2048 shots are scattered by gate errors and decoherence (T₁, T₂).", "after": 6},
    {"t": "shor_factor(15) still succeeds — after a few more retries (continued fractions + the aʳ ≡ 1 check reject the bad samples).", "after": 0},
], size=14, fill=LIGHTBLUE)
card(s, 0.7, 5.3, 11.95, 1.65, "Run it yourself", [
    {"t": [("One line selects the backend in IQM/22_Shor_Period_Finding_to_RSA.ipynb:  ", {}), ('TARGET = "fake_apollo"', {"font": "Courier New", "color": NAVY, "bold": True}), ("  (local noisy simulator)  →  ", {}),
           ('"garnet"', {"font": "Courier New", "color": NAVY, "bold": True}), (" / ", {}), ('"emerald"', {"font": "Courier New", "color": NAVY, "bold": True}), ("  (real 20- / 54-qubit QPUs on IQM Resonance).", {})], "after": 4},
    {"t": "The ‘:mock’ targets only test the cloud pipeline (they return random bitstrings); verify logic on fake_apollo, then spend QPU credits.", "size": 13, "color": GREY, "after": 0},
], size=15)

# 23 --------------------------------------------------------------- breaking RSA
s = new_slide("Breaking a toy RSA key — and N = 21", notes="End to end: from public data only, Shor recovers p and q, then phi, then d, then the message. This is the last section of 22_Shor_Period_Finding_to_RSA.ipynb. N = 21 with a = 2 is the second worked example of the lesson.")
card(s, 0.7, 1.55, 7.2, 5.4, "The attack (22_Shor_Period_Finding_to_RSA.ipynb, last section)", [
    {"t": [("The attacker sees only the public key ", {}), ("(N, e) = (55, 3)", {"bold": True, "color": GREEN}), (" and the cipher-text ", {}), ("c = 13", {"bold": True}), (".", {})], "after": 6},
    {"t": [("1. ", {"bold": True}), ("Run Recipe S1 on N = 55  →  p = 5, q = 11", {})], "after": 3},
    {"t": [("2. ", {"bold": True}), ("φ(N) = 4 · 10 = 40", {})], "after": 3},
    {"t": [("3. ", {"bold": True}), ("d ≡ 3⁻¹ ≡ 27 (mod 40)   — the private key", {})], "after": 3},
    {"t": [("4. ", {"bold": True}), ("m = c^d mod N = 13²⁷ mod 55 = 7   — the message", {})], "after": 8},
    {"t": "public data  →  factor N  →  φ(N)  →  d  →  m", "align": "c", "bold": True, "color": RED, "size": 20, "after": 8},
    {"t": "The private key and the message are recovered purely from public data: the trapdoor is gone.", "bold": True, "after": 0},
], size=15, fill=LIGHTRED)
card(s, 8.1, 1.55, 4.55, 5.4, "Second example: N = 21, a = 2", [
    {"t": "Powers of 2 mod 21: 2, 4, 8, 16, 11, 1  →  r = 6 (even)", "after": 4},
    {"math": r"a^{r/2} = 2^{3} = 8", "size": 18, "color": NAVY, "align": "c"},
    {"math": r"\mathrm{gcd}(8-1, 21) = 7", "size": 18, "color": NAVY, "align": "c"},
    {"math": r"\mathrm{gcd}(8+1, 21) = 3", "size": 18, "color": NAVY, "align": "c"},
    {"math": r"21 = 3 \times 7", "size": 20, "color": RED, "align": "c"},
    {"t": "Exercise: which measured phases y/2⁸ fail for N = 21, and why?", "size": 13, "color": GREY, "after": 0},
], size=15)

# 24 --------------------------------------------------------------- bottleneck
s = new_slide("The bottleneck: modular exponentiation", notes="Never build U^(2^j) by repeating U: a^(2^j) mod N is computed classically by repeated squaring and the circuit does one multiplication. Our own notebook measured the difference: 69 914 vs 650 native instructions on the IQM transpiler. Beauregard: 2n+3 qubits, O(n^3) gates.")
textbox(s, 0.7, 1.5, 11.95, 1.1, [
    {"t": [("The controlled-U^(2^j) gates dominate the cost. We never build U^(2^j) by repeating U 2^j times (that is exponential): ", {}),
           ("a^(2^j) mod N is precomputed classically by repeated squaring", {"bold": True, "color": RED}), (" in O(j) multiplications, and the circuit performs one controlled modular multiplication by that number.", {})]},
], size=16)
card(s, 0.7, 2.75, 5.85, 2.3, "Measured in the course notebook (N = 15, t = 8)", [
    {"t": [("Naive: repeat U 2^j times → ", {}), ("69 914", {"bold": True, "color": RED, "size": 22}), (" native instructions", {})], "after": 4},
    {"t": [("Classical pre-computation → ", {}), ("650", {"bold": True, "color": GREEN, "size": 22}), (" native instructions, depth 372", {})], "after": 4},
    {"t": "(IQM transpiler, PRX + CZ gate set; IQM Resonance refuses jobs above 10 000 instructions — the naive circuit cannot even be submitted.)", "size": 13, "color": GREY, "after": 0},
], size=15, fill=LIGHTBLUE)
card(s, 6.8, 2.75, 5.85, 2.3, "Theorem (complexity of Shor’s algorithm)", [
    {"t": "Order finding, hence factoring N, succeeds with constant probability using", "after": 2},
    {"math": r"O(\log N)\ \text{qubits}", "size": 17, "color": NAVY, "align": "c", "after": 0},
    {"math": r"\tilde{O}\!\left((\log N)^{2}\right)\ \text{quantum gates per run}", "size": 17, "color": NAVY, "align": "c"},
    {"t": "plus O((log N)³) classical post-processing — polynomial in the input size log N.", "after": 0},
], size=15, fill=LIGHTBLUE)
card(s, 0.7, 5.2, 11.95, 1.75, "How the multiplier is built", [
    {"t": "Reversible modular multiplication = QFT-based adders (Draper) + controlled modular additions: Beauregard (2003) factors an n-bit N with 2n + 3 qubits and O(n³) gates.", "bullet": True},
    {"t": "For N = 15 the notebook cheats pedagogically: multiplication by 2, 4, 7, 8, 11, 13 is a permutation of 4 wires (swaps + X gates) — that is c_amod15.", "bullet": True},
], size=14, fill=LIGHT)

# 25 --------------------------------------------------------------- reality check
s = new_slide("Reality check: how far are we from RSA-2048?", notes="Gidney & Ekera 2019: 20 million noisy physical qubits, 8 hours. Gidney 2025 lowered the estimate to under a million noisy qubits running for less than a week. Today's chips: IQM Garnet 20, Emerald 54, the largest superconducting processors around a thousand physical qubits, with error rates that still need heavy error correction. Hence the notebooks factor 15 and 21.")
stats = [("20 000 000", "noisy physical qubits · 8 hours", "Gidney & Ekerå (2019), RSA-2048", RED),
         ("< 1 000 000", "noisy physical qubits · < 1 week", "Gidney (2025), RSA-2048, improved codes", RED),
         ("20 / 54", "qubits on IQM Garnet / Emerald", "the machines behind IQM/22_Shor_Period_Finding_to_RSA.ipynb", NAVY),
         ("≈ 10³", "physical qubits on the largest chips", "no fault-tolerant logical qubits at scale yet", NAVY)]
for i, (big, lab, src, colr) in enumerate(stats):
    x = 0.7 + i * 3.02
    rect(s, x, 1.55, 2.85, 2.5, fill=LIGHT, line=LINEGREY, line_w=0.75, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
    textbox(s, x, 1.6, 2.85, 2.45, [
        {"t": big, "align": "c", "bold": True, "size": 30, "color": colr, "after": 2},
        {"t": lab, "align": "c", "size": 14, "color": GREY, "after": 6},
        {"t": src, "align": "c", "size": 12, "color": BLUE, "after": 0},
    ], anchor=MSO_ANCHOR.MIDDLE)
textbox(s, 0.7, 4.3, 11.95, 2.7, [
    {"t": [("Polynomial, but the constants are enormous: ", {"bold": True}), ("every logical qubit of the factoring circuit needs hundreds to thousands of physical qubits of error correction, and the modular-exponentiation circuit has ~10⁹ Toffoli gates.", {})], "bullet": True},
    {"t": [("Hence the gap: ", {"bold": True}), ("our notebooks factor 15 and 21 with 12 qubits — several orders of magnitude from 2048-bit keys. No RSA key has ever been broken by a quantum computer.", {})], "bullet": True},
    {"t": [("Why worry now? ", {"bold": True}), ("‘Harvest now, decrypt later’: encrypted traffic recorded today can be decrypted once a large machine exists. Long-lived secrets need protection today.", {"color": RED})], "bullet": True},
], size=16)

# 26 --------------------------------------------------------------- PQC
s = new_slide("Post-quantum cryptography", notes="NIST finalised FIPS 203/204/205 in August 2024. ML-KEM and ML-DSA are lattice-based: their security does not reduce to factoring or discrete logs, i.e. to period finding, which is what Shor exploits. Migration is under way in TLS and SSH.")
textbox(s, 0.7, 1.5, 11.95, 0.9, [
    {"t": [("Shor breaks everything whose security reduces to ", {}), ("factoring or discrete logarithms", {"bold": True, "color": RED}), (" — RSA, Diffie–Hellman, DSA, elliptic curves. The answer is not ‘more bits’: it is a different hard problem.", {})]},
], size=17)
cols = [("FIPS 203 — ML-KEM (Kyber)", "key encapsulation", "Module lattices: Learning With Errors. Replaces RSA / ECDH key exchange in TLS 1.3 (hybrid X25519 + ML-KEM is already deployed by major browsers and CDNs)."),
        ("FIPS 204 — ML-DSA (Dilithium)", "digital signatures", "Also lattice-based (Fiat–Shamir with aborts). Replaces RSA-PSS / ECDSA signatures in certificates and code signing."),
        ("FIPS 205 — SLH-DSA (SPHINCS+)", "hash-based signatures", "Security rests only on hash functions; larger signatures, but a conservative backup if lattices fall.")]
for i, (head, sub, body) in enumerate(cols):
    x = 0.7 + i * 4.05
    card(s, x, 2.55, 3.85, 2.9, head, [{"t": sub, "italic": True, "color": BLUE, "after": 6}, {"t": body, "after": 0}], size=14, fill=LIGHTBLUE, header_size=15)
card(s, 0.7, 5.6, 11.95, 1.35, "What survives, what doesn’t", [
    {"t": [("Symmetric crypto and hashes: ", {"bold": True}), ("Grover gives only a quadratic speed-up → double the key length (AES-256, SHA-384) and you are fine.", {})], "bullet": True},
    {"t": [("Public-key crypto based on periodicity (RSA, DH, ECC): ", {"bold": True}), ("broken in polynomial time → must be replaced, standards finalised by NIST in 2024.", {})], "bullet": True},
], size=14, fill=LIGHT)

# 27 --------------------------------------------------------------- notebook mapping + demo
s = new_slide("From the lesson to the notebook", notes="Demo time. Each piece of the lecture is a named function in 22_Shor_Period_Finding_to_RSA.ipynb. Run on the Aer simulator first; the IQM copy switches to Garnet/Emerald with the TARGET line.")
rows = [("Order → factors (Step 1)", "factors_from_order(a, r, N)"),
        ("Operator U and QPE circuit (Step 2)", "c_amod15, qft_dagger, build_order_finding_circuit"),
        ("Continued fractions (Step 3)", "best_rational / Fraction.limit_denominator"),
        ("Recipe S1 — the full loop", "shor_factor(N)"),
        ("RSA key, encryption, attack", "rsa_keygen, rsa_encrypt, ‘breaking RSA’ cell")]
tb = s.shapes.add_table(len(rows) + 1, 2, Inches(0.7), Inches(1.55), Inches(7.3), Inches(3.3)).table
tb.columns[0].width = Inches(3.3); tb.columns[1].width = Inches(4.0)
hdr = ("Lecture", "22_Shor_Period_Finding_to_RSA.ipynb")
for c, val in enumerate(hdr):
    cell = tb.cell(0, c); cell.text = ""; _run(cell.text_frame.paragraphs[0], val, size=15, color=WHITE, bold=True)
    cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
for r, (a_, b_) in enumerate(rows, 1):
    for c, val in enumerate((a_, b_)):
        cell = tb.cell(r, c); cell.text = ""
        _run(cell.text_frame.paragraphs[0], val, size=13, color=GREY if c == 0 else NAVY, font=None if c == 0 else "Courier New", bold=(c == 1))
        cell.fill.solid(); cell.fill.fore_color.rgb = LIGHT if r % 2 else WHITE
demo_box(s, 8.4, 1.75, 4.25, 1.3, "Demo Shor (IBM Aer)", NOTEBOOK_URL)
demo_box(s, 8.4, 3.35, 4.25, 1.3, "Demo Shor (IQM)", NOTEBOOK_IQM_URL)
card(s, 0.7, 5.1, 11.95, 1.85, "How to run", [
    {"t": [("IBM/22_Shor_Period_Finding_to_RSA.ipynb: ", {"bold": True}), ("pip install qiskit qiskit-aer matplotlib pandas — runs entirely on the Aer simulator.", {})], "bullet": True},
    {"t": [("IQM/22_Shor_Period_Finding_to_RSA.ipynb: ", {"bold": True}), ("same notebook; the helper iqm_backend.py transpiles to PRX + CZ and runs on fake_apollo (offline) or, with an IQM Resonance token, on Garnet / Emerald. One TARGET line.", {})], "bullet": True},
], size=14, fill=LIGHTBLUE)

# 28 --------------------------------------------------------------- exercises
s = new_slide("Exercises", notes="Exercises from the lesson; 4 and 5 are meant to be done with the notebook.")
ex = [
    "Compute φ(561) and verify that 561 = 3·11·17 is a Carmichael number: a⁵⁶⁰ ≡ 1 (mod 561) for all a coprime to 561, yet 561 is composite. (Why does this not contradict Euler?)",
    "For p = 7, q = 13 build an RSA key with e = 5; find d and encrypt/decrypt m = 9 by hand, using CRT for the decryption.",
    "Prove that if gcd(e, φ(N)) ≠ 1 then d need not exist, and explain why Recipe R1 step 3 forbids it. What happens if you try e = 65537 with p = 65537·2 + 1?",
    "In the N = 15, a = 7 example, which measured phases φ fail to produce a factor, and why? Relate your answer to the three failure modes of Step 3. Check with the notebook histogram.",
    "Factor N = 35 by hand using a = 3 (r = 12): show gcd(3⁶ ± 1, 35) = {5, 7}. Then modify shor_factor to handle N = 35 (hint: you need a different modular multiplier).",
]
for i, e_ in enumerate(ex):
    y = 1.55 + i * 1.08
    rect(s, 0.8, y + 0.08, 0.6, 0.6, fill=NAVY, line=None, shape=MSO_SHAPE.OVAL)
    textbox(s, 0.8, y + 0.08, 0.6, 0.6, [{"t": str(i + 1), "align": "c", "bold": True}], size=18, color=WHITE, anchor=MSO_ANCHOR.MIDDLE, margin=0)
    textbox(s, 1.6, y, 11.0, 1.05, [{"t": e_}], size=15, color=GREY)

# 29 --------------------------------------------------------------- references
s = new_slide("References", notes=None)
refs = [
    ("R. Rivest, A. Shamir, L. Adleman", "A Method for Obtaining Digital Signatures and Public-Key Cryptosystems", "Comm. ACM 21 (1978) 120–126", None),
    ("P. W. Shor", "Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer", "SIAM J. Comput. 26 (1997) 1484 — arXiv:quant-ph/9508027", "https://arxiv.org/abs/quant-ph/9508027"),
    ("M. A. Nielsen, I. L. Chuang", "Quantum Computation and Quantum Information", "Cambridge University Press (2000), Chapter 5", None),
    ("S. Beauregard", "Circuit for Shor’s algorithm using 2n+3 qubits", "arXiv:quant-ph/0205095", "https://arxiv.org/abs/quant-ph/0205095"),
    ("C. Gidney, M. Ekerå", "How to factor 2048 bit RSA integers in 8 hours using 20 million noisy qubits", "Quantum 5 (2021) 433 — arXiv:1905.09749", "https://arxiv.org/abs/1905.09749"),
    ("C. Gidney", "How to factor 2048 bit RSA integers with less than a million noisy qubits", "arXiv:2505.15917 (2025)", "https://arxiv.org/abs/2505.15917"),
    ("NIST", "FIPS 203 (ML-KEM), FIPS 204 (ML-DSA), FIPS 205 (SLH-DSA)", "Post-Quantum Cryptography Standards, August 2024", "https://csrc.nist.gov/projects/post-quantum-cryptography"),
]
items = []
for who, title, where, url in refs:
    items.append({"t": [(who + " — ", {"bold": True}), (title, {"italic": True, "link": url} if url else {"italic": True}), (". " + where, {"color": GREY})], "bullet": True, "after": 8})
textbox(s, 0.7, 1.55, 11.95, 5.4, items, size=15, color=BLUE)

# 30 --------------------------------------------------------------- end
s = new_slide("Questions & Answers", notes=None)
if END_PIC:
    picture(s, END_PIC, 0.92, 1.41, w=11.5, name="EndPicture")
    pic = s.shapes[-1]
    if pic.height > Inches(5.55):
        pic.height = Inches(5.55); pic.width = int(pic.width * 5.55 / (pic.height / E) / E * E) if False else pic.width
textbox(s, 0.92, 6.98, 11.5, 0.45, [{"t": "Thanks for your attention!   ·   rsa_shor_lesson.pdf · IBM/22_Shor_Period_Finding_to_RSA.ipynb · IQM/22_Shor_Period_Finding_to_RSA.ipynb", "align": "c"}], size=14, color=BLUE)

prs.save(OUT)
print("saved", OUT, "slides:", len(prs.slides))
