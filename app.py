# -*- coding: utf-8 -*-

# Phone Number Lookup - TrueCaller + GetContact

# Streamlit app - all characters are ASCII-safe

import streamlit as st
import asyncio
import hashlib
import hmac
import time
import json
import re
import requests

# ———————————————————————–

# Optional: truecallerpy

# ———————————————————————–

try:
from truecallerpy import search_phonenumber
TRUECALLER_LIB = True
except ImportError:
TRUECALLER_LIB = False

# ———————————————————————–

# Optional: phonenumbers

# ———————————————————————–

try:
import phonenumbers
PHONENUMBERS_LIB = True
except ImportError:
PHONENUMBERS_LIB = False

# ———————————————————————–

# Page config

# ———————————————————————–

st.set_page_config(
page_title=“Phone Lookup”,
page_icon=”:mag:”,
layout=“centered”,
initial_sidebar_state=“expanded”,
)

st.markdown(”””

<style>
.card {
    background: #16213e;
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.5rem 0 1rem 0;
    border-left: 4px solid #667eea;
}
.card.gc { border-left-color: #00b4d8; }
.badge {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 8px;
}
.badge-tc { background:#667eea22; color:#667eea; border:1px solid #667eea55; }
.badge-gc { background:#00b4d822; color:#00b4d8; border:1px solid #00b4d855; }
.name { font-size:1.4rem; font-weight:700; color:#fff; margin-bottom:6px; }
.info { color:#aaa; font-size:0.85rem; margin:3px 0; }
.chip {
    display:inline-block;
    border-radius:20px;
    padding:2px 10px;
    font-size:0.75rem;
    margin:2px;
    background:#ff6b6b22;
    color:#ff6b6b;
    border:1px solid #ff6b6b44;
}
.chip.ok { background:#51cf6622; color:#51cf66; border-color:#51cf6644; }
.section { font-weight:600; color:#aaa; font-size:0.78rem;
           text-transform:uppercase; letter-spacing:1px;
           margin:10px 0 4px 0; }
.warn { background:#ff980018; border:1px solid #ff980055;
        border-radius:8px; padding:0.8rem 1rem;
        font-size:0.82rem; color:#ffb347; }
</style>

“””, unsafe_allow_html=True)

# ———————————————————————–

# Phone number normalizer

# ———————————————————————–

def normalize(raw, default_cc=“ID”):
raw = re.sub(r”[\s-().+]”, “”, raw)

```
if PHONENUMBERS_LIB:
    try:
        parsed = phonenumbers.parse("+" + raw if not raw.startswith("0") else raw, default_cc)
        e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
        region = phonenumbers.region_code_for_number(parsed) or default_cc
        try:
            from phonenumbers import carrier as _c
            op = _c.name_for_number(parsed, "id") or _c.name_for_number(parsed, "en") or "-"
        except Exception:
            op = "-"
        return {"e164": e164, "national": national, "cc": region,
                "operator": op, "valid": phonenumbers.is_valid_number(parsed)}
    except Exception:
        pass

# Fallback manual for Indonesia
if raw.startswith("0"):
    e164 = "+62" + raw[1:]
elif raw.startswith("62"):
    e164 = "+" + raw
else:
    e164 = "+" + raw
return {"e164": e164, "national": raw, "cc": default_cc, "operator": "-", "valid": True}
```

# ———————————————————————–

# TrueCaller lookup

# ———————————————————————–

async def tc_lookup(phone_e164, token):
if not TRUECALLER_LIB:
return {“error”: “truecallerpy belum terinstall. Jalankan: pip install truecallerpy”,
“source”: “TrueCaller”}
try:
clean = phone_e164.lstrip(”+”)
result = await search_phonenumber(clean, “ID”, token)
if not result or “data” not in result:
return {“error”: “Tidak ada hasil dari TrueCaller”, “source”: “TrueCaller”}

```
    data = result["data"]
    if not data:
        return {"error": "Nomor tidak ditemukan di TrueCaller", "source": "TrueCaller"}

    item = data[0] if isinstance(data, list) else data
    phones = item.get("phones", [{}])
    pd = phones[0] if phones else {}

    tags = []
    spam_type = item.get("spamType", "") or item.get("spam", {}).get("spamType", "")
    spam_score = item.get("spamScore", 0) or item.get("spam", {}).get("score", 0)
    if spam_type:
        tags.append({"label": spam_type, "spam": True})

    inet = [ia.get("id", "") for ia in item.get("internetAddresses", []) if ia.get("id")]

    return {
        "source": "TrueCaller",
        "name": item.get("name", ""),
        "carrier": pd.get("carrier", ""),
        "country": pd.get("countryCode", ""),
        "spam_score": spam_score,
        "spam_type": spam_type,
        "tags": tags,
        "internet": inet,
    }
except Exception as e:
    return {"error": "TrueCaller: " + str(e), "source": "TrueCaller"}
```

# ———————————————————————–

# GetContact lookup via raw HTTP (no pip package needed)

# Reverse-engineered from Android APK v6.x

# ———————————————————————–

GC_API_URL = “https://pbssrv-centralevents.com/v2.4/details”
GC_HMAC_SECRET = “getcontact2018”

def gc_sign(payload_str):
ts = str(int(time.time()))
msg = ts + payload_str
sig = hmac.new(GC_HMAC_SECRET.encode(), msg.encode(), hashlib.sha256).hexdigest()
return ts, sig

def gc_lookup(phone_e164, token):
phone_clean = phone_e164.lstrip(”+”)
body = json.dumps({“phoneNumber”: phone_clean}, separators=(”,”, “:”))
ts, sig = gc_sign(body)

```
tok = token.strip()
if not tok.startswith("Bearer "):
    tok = "Bearer " + tok

headers = {
    "Content-Type": "application/json; charset=UTF-8",
    "Authorization": tok,
    "X-Req-Timestamp": ts,
    "X-Req-Signature": sig,
    "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; Pixel 5 Build/RQ3A.211001.001)",
    "Accept-Language": "id",
}

try:
    resp = requests.post(GC_API_URL, data=body, headers=headers, timeout=15)

    if resp.status_code == 401:
        return {"error": "GetContact: Token tidak valid atau kadaluarsa (401 Unauthorized)",
                "source": "GetContact"}
    if resp.status_code == 429:
        return {"error": "GetContact: Terlalu banyak request - coba lagi nanti (429)",
                "source": "GetContact"}
    if not resp.ok:
        return {"error": "GetContact: HTTP " + str(resp.status_code) + " - " + resp.text[:200],
                "source": "GetContact"}

    data = resp.json()
    result = data.get("result", data)

    # Extract names
    names_raw = result.get("names", [])
    sorted_names = sorted(names_raw, key=lambda x: x.get("count", 0), reverse=True)
    main_name = sorted_names[0].get("name", "") if sorted_names else ""

    # Extract tags
    spam_keywords = [
        "spam", "scam", "penipuan", "penipu", "fraud",
        "iklan", "sales", "marketing", "promo", "bot",
        "phishing", "telemarketing",
    ]
    tags = []
    for t in result.get("tags", []):
        label = t.get("tag", t.get("name", ""))
        count = t.get("count", 0)
        is_spam = any(k in label.lower() for k in spam_keywords)
        display = label + (" (" + str(count) + "x)" if count else "")
        tags.append({"label": display, "spam": is_spam})

    return {
        "source": "GetContact",
        "name": main_name,
        "all_names": [n.get("name", "") for n in sorted_names[:6]],
        "tags": tags,
    }

except requests.exceptions.Timeout:
    return {"error": "GetContact: Request timeout (15s)", "source": "GetContact"}
except Exception as e:
    return {"error": "GetContact: " + str(e), "source": "GetContact"}
```

# ———————————————————————–

# Render result card

# ———————————————————————–

def render_card(res):
if “error” in res:
src = res.get(“source”, “Error”)
st.error(”[” + src + “] “ + res[“error”])
return

```
src = res.get("source", "")
is_gc = (src == "GetContact")
card_cls = "card gc" if is_gc else "card"
badge_cls = "badge badge-gc" if is_gc else "badge badge-tc"
label = "[GC]" if is_gc else "[TC]"

name = res.get("name") or "Nama tidak diketahui"
tags = res.get("tags", [])
carrier = res.get("carrier", "")
spam_score = res.get("spam_score", 0)
all_names = res.get("all_names", [])
inet = res.get("internet", [])

tags_html = ""
for t in tags:
    cls = "chip" if t.get("spam") else "chip ok"
    tags_html += "<span class='" + cls + "'>" + t["label"] + "</span>"

extra = ""
if carrier:
    extra += "<div class='info'>Operator: " + carrier + "</div>"
if spam_score:
    color = "#ff6b6b" if float(spam_score) > 3 else "#ffd43b"
    extra += ("<div class='info'>Spam Score: <span style='color:" + color
              + ";font-weight:700'>" + str(spam_score) + "</span></div>")
if inet:
    extra += "<div class='info'>Web: " + ", ".join(inet[:3]) + "</div>"

alt_html = ""
others = [n for n in all_names if n and n != name]
if others:
    alt_html = "<div class='section'>Nama lain</div>"
    for n in others:
        alt_html += "<div class='info'>- " + n + "</div>"

tags_sec = (("<div class='section'>Tags</div>" + tags_html)
            if tags_html else "<div class='info'>Tidak ada tag</div>")

st.markdown(
    "<div class='" + card_cls + "'>"
    + "<span class='" + badge_cls + "'>" + label + " " + src + "</span>"
    + "<div class='name'>" + name + "</div>"
    + extra + tags_sec + alt_html
    + "</div>",
    unsafe_allow_html=True,
)
```

# ———————————————————————–

# Sidebar

# ———————————————————————–

with st.sidebar:
st.markdown(”### Konfigurasi Token”)
st.markdown(”—”)

```
st.markdown("**TrueCaller Token**")
tc_token = st.text_input(
    "tc_token",
    type="password",
    placeholder="installationId dari truecaller.json",
    label_visibility="collapsed",
)

st.markdown("**GetContact Token**")
gc_token = st.text_input(
    "gc_token",
    type="password",
    placeholder="eyJ... (tanpa kata Bearer)",
    label_visibility="collapsed",
)

st.markdown("---")
cc_default = st.selectbox("Default Country", ["ID", "MY", "SG", "US", "AU"], index=0)

st.markdown("---")
with st.expander("Cara dapat token TrueCaller"):
    st.code(
        "pip install truecallerpy\n"
        "python -m truecallerpy\n"
        "# Ikuti prompt: masukkan no HP, OTP\n"
        "# Token tersimpan di:\n"
        "# ~/.truecallerpy/truecaller.json\n"
        "# Salin nilai 'installationId'",
        language="bash",
    )

with st.expander("Cara dapat token GetContact"):
    st.markdown(
        "1. Install **HTTP Toolkit** (gratis) di PC\n"
        "2. Intercept HTTPS dari HP Android\n"
        "3. Buka app GetContact, cari nomor apapun\n"
        "4. Cari request ke `pbssrv-centralevents.com`\n"
        "5. Salin nilai header `Authorization` (tanpa kata Bearer)\n\n"
        "Token biasanya valid 30-90 hari."
    )

with st.expander("Disclaimer"):
    st.markdown(
        "- Menggunakan unofficial/reverse-engineered API\n"
        "- Bisa melanggar ToS GetContact & TrueCaller\n"
        "- Gunakan hanya untuk keperluan pribadi\n"
        "- Jangan gunakan untuk scraping massal"
    )

st.markdown("---")
st.markdown("**Status Library**")
st.write("truecallerpy:", "OK" if TRUECALLER_LIB else "Belum install")
st.write("phonenumbers:", "OK" if PHONENUMBERS_LIB else "Belum install")
st.write("GetContact:", "Built-in via HTTP")

if not TRUECALLER_LIB or not PHONENUMBERS_LIB:
    st.code("pip install truecallerpy phonenumbers", language="bash")
```

# ———————————————————————–

# Main UI

# ———————————————————————–

st.title(“Phone Lookup”)
st.caption(“TrueCaller + GetContact - gabungan dalam satu pencarian”)

col1, col2 = st.columns([3, 1])
with col1:
phone_input = st.text_input(
“Nomor Telepon”,
placeholder=“08123456789 atau +6281234567890”,
label_visibility=“collapsed”,
)
with col2:
search_btn = st.button(“Cari”, use_container_width=True, type=“primary”)

with st.expander(“Cari banyak nomor sekaligus (batch)”):
batch_input = st.text_area(
“batch”,
placeholder=“08111111111\n08222222222\n+6281333333333”,
height=120,
label_visibility=“collapsed”,
)
batch_btn = st.button(“Cari Semua”, key=“batch_btn”)

# ———————————————————————–

# Search logic

# ———————————————————————–

def do_search(raw):
info = normalize(raw, cc_default)
e164 = info[“e164”]

```
c1, c2, c3 = st.columns(3)
c1.metric("E.164", e164)
c2.metric("Negara", info["cc"])
c3.metric("Operator", info["operator"])
st.markdown("---")

if not tc_token and not gc_token:
    st.markdown(
        "<div class='warn'>Belum ada token. Isi TrueCaller Token dan/atau "
        "GetContact Token di sidebar kiri.</div>",
        unsafe_allow_html=True,
    )
    return

results = {}

with st.spinner("Mencari..."):
    if tc_token:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results["tc"] = loop.run_until_complete(tc_lookup(e164, tc_token))
        loop.close()

    if gc_token:
        results["gc"] = gc_lookup(e164, gc_token)

if "tc" in results:
    render_card(results["tc"])
if "gc" in results:
    render_card(results["gc"])

# Summary nama
all_names = set()
for k in ("tc", "gc"):
    if k in results and "error" not in results[k]:
        n = results[k].get("name", "")
        if n:
            all_names.add(n)
        for an in results[k].get("all_names", []):
            if an:
                all_names.add(an)

if all_names:
    st.success("Ditemukan: " + " / ".join(sorted(all_names)))

with st.expander("Raw JSON"):
    st.json(results)
```

if search_btn:
if phone_input:
do_search(phone_input)
else:
st.warning(“Masukkan nomor telepon terlebih dahulu.”)

if batch_btn:
lines = [ln.strip() for ln in (batch_input or “”).split(”\n”) if ln.strip()]
if not lines:
st.warning(“Masukkan nomor di kotak batch.”)
else:
prog = st.progress(0)
for i, line in enumerate(lines):
st.markdown(”#### “ + str(i + 1) + “. `" + line + "`”)
do_search(line)
st.markdown(”—”)
prog.progress((i + 1) / len(lines))
prog.empty()
st.success(“Selesai: “ + str(len(lines)) + “ nomor.”)