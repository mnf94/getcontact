# -*- coding: utf-8 -*-

# “””
Phone Number Lookup - TrueCaller + GetContact

Gabungan pencarian nama & tag dari TrueCaller dan GetContact
menggunakan library unofficial (reverse-engineered mobile API).

Setup sekali:
pip install streamlit truecallerpy getcontact phonenumbers

Jalankan:
streamlit run app.py
“””

import streamlit as st
import asyncio
import re
import json
from datetime import datetime

# ─── Dependency check ──────────────────────────────────────────────────────────

try:
import phonenumbers
PHONENUMBERS_OK = True
except ImportError:
PHONENUMBERS_OK = False

try:
from truecallerpy import search_phonenumber
TRUECALLER_OK = True
except ImportError:
TRUECALLER_OK = False

try:
import getcontact
GETCONTACT_OK = True
except ImportError:
GETCONTACT_OK = False

# ─── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
page_title=“Phone Lookup — TC + GC”,
page_icon=“🔍”,
layout=“centered”,
initial_sidebar_state=“expanded”,
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown(”””

<style>
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #888;
        font-size: 0.9rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .result-card {
        background: #1a1a2e;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .result-card.getcontact {
        border-left-color: #00b4d8;
    }
    .source-badge {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 8px;
    }
    .badge-tc {
        background: #667eea22;
        color: #667eea;
        border: 1px solid #667eea44;
    }
    .badge-gc {
        background: #00b4d822;
        color: #00b4d8;
        border: 1px solid #00b4d844;
    }
    .name-main {
        font-size: 1.4rem;
        font-weight: 700;
        color: #fff;
    }
    .tag-chip {
        display: inline-block;
        background: #ff6b6b22;
        color: #ff6b6b;
        border: 1px solid #ff6b6b44;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        margin: 2px;
    }
    .tag-chip.positive {
        background: #51cf6622;
        color: #51cf66;
        border-color: #51cf6644;
    }
    .info-row {
        color: #aaa;
        font-size: 0.85rem;
        margin: 4px 0;
    }
    .warn-box {
        background: #ff980022;
        border: 1px solid #ff980044;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.82rem;
        color: #ffb347;
    }
    .section-header {
        font-weight: 600;
        color: #ccc;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    hr.divider {
        border: none;
        border-top: 1px solid #333;
        margin: 1rem 0;
    }
</style>

“””, unsafe_allow_html=True)

# ─── Helpers ───────────────────────────────────────────────────────────────────

def normalize_phone(raw: str, default_country: str = “ID”) -> dict:
“””
Terima format apapun: 08xx, +62xx, 628xx, dll.
Return dict dengan: e164, national, country_code, is_valid
“””
raw = raw.strip().replace(” “, “”).replace(”-”, “”).replace(”(”, “”).replace(”)”, “”)

```
if not PHONENUMBERS_OK:
    # Fallback manual untuk Indonesia
    if raw.startswith("0"):
        e164 = "+62" + raw[1:]
    elif raw.startswith("62"):
        e164 = "+" + raw
    elif not raw.startswith("+"):
        e164 = "+62" + raw
    else:
        e164 = raw
    return {
        "e164": e164,
        "national": raw,
        "country_code": "ID",
        "is_valid": True,
        "operator": "Unknown"
    }

try:
    parsed = phonenumbers.parse(raw, default_country)
    is_valid = phonenumbers.is_valid_number(parsed)
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
    region = phonenumbers.region_code_for_number(parsed)

    # Coba ambil operator
    try:
        from phonenumbers import carrier
        op = carrier.name_for_number(parsed, "id") or carrier.name_for_number(parsed, "en") or "Unknown"
    except Exception:
        op = "Unknown"

    return {
        "e164": e164,
        "national": national,
        "country_code": region or default_country,
        "is_valid": is_valid,
        "operator": op,
    }
except Exception as e:
    return {
        "e164": raw,
        "national": raw,
        "country_code": default_country,
        "is_valid": False,
        "operator": "Unknown",
        "error": str(e)
    }
```

async def lookup_truecaller(phone_e164: str, auth_token: str) -> dict:
“””
Cari nomor via TrueCaller menggunakan truecallerpy.
Docs: https://github.com/sumithemmadi/truecallerpy
“””
if not TRUECALLER_OK:
return {“error”: “Library truecallerpy belum terinstall. Jalankan: pip install truecallerpy”}

```
try:
    # Hapus tanda + dari e164 untuk truecallerpy
    phone_clean = phone_e164.lstrip("+")
    result = await search_phonenumber(phone_clean, "ID", auth_token)

    if not result or "data" not in result:
        return {"error": "Tidak ada hasil dari TrueCaller", "raw": result}

    data = result["data"]
    if not data:
        return {"error": "Nomor tidak ditemukan di TrueCaller"}

    item = data[0] if isinstance(data, list) else data
    name = item.get("name", "")
    phones = item.get("phones", [{}])
    phone_data = phones[0] if phones else {}

    # Ekstrak tags / spam info
    tags = []
    score = item.get("score", 0)
    spam_score = item.get("spamScore", 0) or item.get("spam", {}).get("score", 0)
    spam_type = item.get("spamType", "") or item.get("spam", {}).get("spamType", "")

    if spam_type:
        tags.append({"label": spam_type, "type": "spam"})
    if score:
        tags.append({"label": f"Score: {score:.1f}", "type": "info"})

    # Internet name / alias
    internet_addrs = item.get("internetAddresses", [])

    return {
        "source": "TrueCaller",
        "name": name,
        "number": phone_data.get("e164Format", phone_e164),
        "carrier": phone_data.get("carrier", ""),
        "country": phone_data.get("countryCode", ""),
        "spam_score": spam_score,
        "spam_type": spam_type,
        "tags": tags,
        "internet_addresses": [ia.get("id", "") for ia in internet_addrs],
        "raw": item,
    }

except Exception as e:
    return {"error": f"TrueCaller error: {str(e)}"}
```

async def lookup_getcontact(phone_e164: str, auth_token: str) -> dict:
“””
Cari nomor via GetContact menggunakan library getcontact.
Docs: https://github.com/HerculesNode/getcontact
“””
if not GETCONTACT_OK:
return {“error”: “Library getcontact belum terinstall. Jalankan: pip install getcontact”}

```
try:
    # GetContact biasanya pakai format tanpa tanda +
    phone_clean = phone_e164.lstrip("+")
    
    # Inisialisasi client dengan token
    client = getcontact.GetContact(token=auth_token)
    result = await asyncio.to_thread(client.search, phone_clean)

    if not result:
        return {"error": "Tidak ada hasil dari GetContact"}

    # Parse tags — format: list of {"tag": "nama tag", "count": N}
    tags_raw = result.get("tags", []) or result.get("result", {}).get("tags", [])
    names_raw = result.get("names", []) or result.get("result", {}).get("names", [])

    # Ambil nama terbanyak
    name = ""
    if names_raw:
        sorted_names = sorted(names_raw, key=lambda x: x.get("count", 0), reverse=True)
        name = sorted_names[0].get("name", "") if sorted_names else ""

    tags = []
    spam_keywords = ["spam", "scam", "penipuan", "penipu", "fraud", "iklan", "sales",
                     "marketing", "promo", "ojol", "driver", "kurir", "bot"]
    for t in tags_raw:
        label = t.get("tag", t.get("name", ""))
        count = t.get("count", 0)
        is_spam = any(k in label.lower() for k in spam_keywords)
        tags.append({
            "label": f"{label} ({count}x)" if count else label,
            "type": "spam" if is_spam else "positive",
        })

    return {
        "source": "GetContact",
        "name": name,
        "all_names": [n.get("name", "") for n in names_raw[:5]],
        "tags": tags,
        "raw": result,
    }

except Exception as e:
    return {"error": f"GetContact error: {str(e)}"}
```

def render_result_card(result: dict):
“”“Render kartu hasil pencarian.”””
if “error” in result:
st.error(f”⚠️ {result[‘source’] if ‘source’ in result else ‘Error’}: {result[‘error’]}”)
return

```
source = result.get("source", "")
badge_class = "badge-tc" if source == "TrueCaller" else "badge-gc"
card_class = "" if source == "TrueCaller" else "getcontact"
icon = "🔵" if source == "TrueCaller" else "🟦"

name = result.get("name", "") or "Nama tidak diketahui"
tags = result.get("tags", [])
carrier = result.get("carrier", "")
country = result.get("country", "")
spam_score = result.get("spam_score", 0)
all_names = result.get("all_names", [])
internet_addresses = result.get("internet_addresses", [])

# Render HTML card
tags_html = ""
for tag in tags:
    css_class = "tag-chip" if tag["type"] == "spam" else "tag-chip positive"
    tags_html += f'<span class="{css_class}">{tag["label"]}</span>'

names_html = ""
if all_names and len(all_names) > 1:
    names_html = "<div class='section-header'>Nama lain yang tersimpan</div>"
    for n in all_names:
        if n and n != name:
            names_html += f"<div class='info-row'>• {n}</div>"

extra_html = ""
if carrier:
    extra_html += f"<div class='info-row'>📡 Operator: {carrier}</div>"
if spam_score:
    color = "#ff6b6b" if spam_score > 3 else "#ffd43b"
    extra_html += f"<div class='info-row'>⚠️ Spam Score: <span style='color:{color};font-weight:600'>{spam_score}</span></div>"
if internet_addresses:
    extra_html += f"<div class='info-row'>🌐 {', '.join(internet_addresses[:3])}</div>"

st.markdown(f"""
<div class="result-card {card_class}">
    <span class="source-badge {badge_class}">{icon} {source}</span>
    <div class="name-main">{name}</div>
    {extra_html}
    {"<div class='section-header'>Tags</div>" + tags_html if tags_html else "<div class='info-row'>Tidak ada tag</div>"}
    {names_html}
</div>
""", unsafe_allow_html=True)
```

# ─── Sidebar: Auth tokens ───────────────────────────────────────────────────────

with st.sidebar:
st.markdown(”### ⚙️ Konfigurasi Auth”)
st.markdown(”—”)

```
st.markdown("**TrueCaller Token**")
st.markdown(
    "<small>Dapat dari login via: <code>python -m truecallerpy</code> atau lihat README di bawah</small>",
    unsafe_allow_html=True
)
tc_token = st.text_input(
    "TrueCaller Auth Token",
    type="password",
    placeholder="eyJhbGciOiJSUzI1NiJ9...",
    key="tc_token",
    label_visibility="collapsed"
)

st.markdown("**GetContact Token**")
st.markdown(
    "<small>Dapat dari intercept request app GetContact (lihat README)</small>",
    unsafe_allow_html=True
)
gc_token = st.text_input(
    "GetContact Auth Token",
    type="password",
    placeholder="Bearer eyJ...",
    key="gc_token",
    label_visibility="collapsed"
)

st.markdown("---")
st.markdown("**Default Country**")
country_default = st.selectbox(
    "Default Country",
    options=["ID", "US", "MY", "SG", "AU"],
    index=0,
    label_visibility="collapsed"
)

st.markdown("---")
with st.expander("📖 Cara dapat token"):
    st.markdown("""
```

**TrueCaller:**

```bash
pip install truecallerpy
python -m truecallerpy
```

Ikuti prompt → masukkan no HP → OTP → token tersimpan di `~/.truecallerpy/truecaller.json`
Salin nilai `installationId` atau `token` dari file tersebut.

-----

**GetContact:**

1. Install mitmproxy / HTTP Toolkit
1. Buka app GetContact di HP
1. Intercept request ke `api.getcontact.com`
1. Salin header `Authorization: Bearer ...`

Token biasanya valid 30–90 hari.
“””)

```
with st.expander("⚠️ Disclaimer"):
    st.markdown("""
```

- Tools ini menggunakan **unofficial API** (reverse-engineered)
- Penggunaan dapat **melanggar ToS** GetContact & TrueCaller
- Akun dapat **di-suspend** sewaktu-waktu
- Gunakan hanya untuk keperluan **pribadi/internal**
- Jangan gunakan untuk scraping massal
  “””)
  
  # Library status
  
  st.markdown(”—”)
  st.markdown(”**Status Library**”)
  col1, col2 = st.columns(2)
  with col1:
  st.markdown(“TrueCaller”)
  st.markdown(“GetContact”)
  with col2:
  st.markdown(“✅” if TRUECALLER_OK else “❌ Not installed”)
  st.markdown(“✅” if GETCONTACT_OK else “❌ Not installed”)
  
  if not TRUECALLER_OK or not GETCONTACT_OK:
  st.markdown(”””

```bash
pip install truecallerpy getcontact phonenumbers
```

```
    """)
```

# ─── Main UI ───────────────────────────────────────────────────────────────────

st.markdown(’<p class="main-title">🔍 Phone Lookup</p>’, unsafe_allow_html=True)
st.markdown(’<p class="subtitle">TrueCaller + GetContact — gabungan dalam satu pencarian</p>’, unsafe_allow_html=True)

# Input nomor

col_input, col_btn = st.columns([3, 1])
with col_input:
phone_input = st.text_input(
“Nomor Telepon”,
placeholder=“08123456789 atau +6281234567890”,
key=“phone_input”,
label_visibility=“collapsed”
)
with col_btn:
search_btn = st.button(“🔍 Cari”, use_container_width=True, type=“primary”)

# Batch search

with st.expander(“📋 Cari banyak nomor sekaligus (batch)”):
batch_input = st.text_area(
“Nomor (satu per baris)”,
placeholder=“08111111111\n08222222222\n+6281333333333”,
height=120,
label_visibility=“collapsed”
)
batch_btn = st.button(“🔍 Cari Semua”, key=“batch_btn”)

# ─── Search logic ──────────────────────────────────────────────────────────────

def do_search(phone_raw: str):
“”“Eksekusi pencarian untuk satu nomor.”””
phone_info = normalize_phone(phone_raw, country_default)

```
if not phone_info.get("is_valid", False) and "error" in phone_info:
    st.warning(f"⚠️ Format nomor mungkin tidak valid: {phone_info.get('error', '')}")

e164 = phone_info["e164"]
national = phone_info["national"]
operator = phone_info.get("operator", "")
country_code = phone_info.get("country_code", "")

# Info nomor
cols = st.columns(3)
cols[0].metric("Format E.164", e164)
cols[1].metric("Negara", country_code)
cols[2].metric("Operator", operator or "—")

st.markdown("<hr class='divider'>", unsafe_allow_html=True)

# Cek token
sources_to_search = []
if tc_token:
    sources_to_search.append("truecaller")
if gc_token:
    sources_to_search.append("getcontact")

if not sources_to_search:
    st.markdown("""
    <div class="warn-box">
    ⚠️ <b>Belum ada token yang diisi.</b><br>
    Isi TrueCaller Token dan/atau GetContact Token di sidebar kiri untuk mulai pencarian.
    </div>
    """, unsafe_allow_html=True)
    return

# Jalankan pencarian paralel
with st.spinner("🔄 Mencari..."):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = {}
    if "truecaller" in sources_to_search:
        tasks["truecaller"] = loop.run_until_complete(lookup_truecaller(e164, tc_token))
    if "getcontact" in sources_to_search:
        tasks["getcontact"] = loop.run_until_complete(lookup_getcontact(e164, gc_token))

    loop.close()

# Render hasil
if "truecaller" in tasks:
    render_result_card(tasks["truecaller"])

if "getcontact" in tasks:
    render_result_card(tasks["getcontact"])

# Summary
names_found = set()
if "truecaller" in tasks and "name" in tasks["truecaller"]:
    n = tasks["truecaller"].get("name", "")
    if n:
        names_found.add(n)
if "getcontact" in tasks and "name" in tasks["getcontact"]:
    n = tasks["getcontact"].get("name", "")
    if n:
        names_found.add(n)
if "getcontact" in tasks and "all_names" in tasks["getcontact"]:
    for n in tasks["getcontact"]["all_names"]:
        if n:
            names_found.add(n)

if names_found:
    st.success(f"✅ Ditemukan: **{' / '.join(names_found)}**")

# Export JSON
with st.expander("📄 Raw JSON"):
    st.json(tasks)
```

# ─── Trigger search ────────────────────────────────────────────────────────────

if search_btn and phone_input:
do_search(phone_input)
elif search_btn and not phone_input:
st.warning(“Masukkan nomor telepon terlebih dahulu.”)

if batch_btn and batch_input:
lines = [l.strip() for l in batch_input.strip().split(”\n”) if l.strip()]
if not lines:
st.warning(“Tidak ada nomor yang dimasukkan.”)
else:
st.markdown(f”### Hasil Batch ({len(lines)} nomor)”)
progress = st.progress(0)
for i, line in enumerate(lines):
st.markdown(f”#### {i+1}. `{line}`”)
do_search(line)
st.markdown(”<hr class='divider'>”, unsafe_allow_html=True)
progress.progress((i + 1) / len(lines))
progress.empty()
st.success(f”✅ Selesai mencari {len(lines)} nomor.”)

elif batch_btn and not batch_input:
st.warning(“Masukkan nomor di kotak batch terlebih dahulu.”)

# ─── Footer ────────────────────────────────────────────────────────────────────

st.markdown(”—”)
st.markdown(
“<center><small>⚠️ Hanya untuk penggunaan pribadi/internal. “
“Hormati privasi orang lain.</small></center>”,
unsafe_allow_html=True
)