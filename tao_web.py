# -*- coding: utf-8 -*-
"""
tao_web.py — Tạo trang tìm kiếm thư viện (index.html) cho GitHub Pages từ danh mục Google Sheet.

Cách 1 (TỰ ĐỘNG): điền DATA_URL = link ứng dụng web Apps Script, đưa file này lên repo GitHub
        cùng .github/workflows/cap-nhat-web.yml -> GitHub tự tạo lại index.html mỗi ngày.
Cách 2 (tay):     python tao_web.py "Thu vien tai lieu - DanhMuc.csv"   (CSV tải từ tab DanhMuc)

Trang chỉ chứa "Link xem" (bản xem có watermark). KHÔNG đưa Link Drive / File ID bản gốc ra ngoài.
Danh sách toàn bộ tài liệu được ghi sẵn trong HTML để Google tìm thấy (SEO), JavaScript chỉ lọc.
"""
import csv
import html
import json
import os
import re
import sys
import unicodedata
from datetime import date

# ======================= CẤU HÌNH — SỬA Ở ĐÂY =======================
TEN_WEB = "Thư viện tài liệu sửa chữa máy công trình"
MO_TA = ("Tra cứu miễn phí tài liệu sửa chữa xe nâng, cẩu, máy xúc, động cơ, hộp số, xe tải, máy phát điện: "
         "mã lỗi, sơ đồ điện, sơ đồ thủy lực, service manual. Nhận dịch tài liệu kỹ thuật sang tiếng Việt.")
ZALO = "https://zalo.me/0384560508"            # <- link Zalo của anh
FORM_YEU_CAU = ""                               # (tuỳ chọn) link Google Form "Yêu cầu tài liệu"
URL_WEB = "https://vinh-hung.github.io/ThuVienTaiLieufree/"   # <- địa chỉ trang GitHub Pages
GOOGLE_VERIFY = "jnCm0WrTvWY0uuFa-5qZdpvNlcECUzXsN5oYfW4FJMw"   # <- mã xác minh Google Search Console (phần content="..." của thẻ meta), để trống nếu chưa có
DATA_URL = "https://script.google.com/macros/s/AKfycbw22TQMEXXbpHpy1BkC_uxJ-hNotLB0C2kdzh2sEdwJA6G3kZcJHUBgUXXgAKQCO6ssIg/exec"   # <- link ứng dụng web Apps Script
# ===================================================================

MAY = {"XeNang": "Xe nâng", "Cau": "Cẩu", "MayXuc": "Máy xúc", "MayXucLat": "Máy xúc lật", "MayUi": "Máy ủi",
       "DongCo": "Động cơ", "HopSo": "Hộp số", "XeTai": "Xe tải", "XeCon": "Ô tô", "XeMay": "Xe máy",
       "MayPhat": "Máy phát điện", "LinhKien": "Linh kiện"}
TL = {"MaLoi": "Mã lỗi", "SoDoDien": "Sơ đồ điện", "ThuyLuc": "Thủy lực", "Service": "Sửa chữa",
      "Parts": "Phụ tùng", "VanHanh": "Vận hành", "DaoTao": "Đào tạo", "ThongSo": "Thông số", "Khac": "Khác"}
HT = {"Controller": "Bộ điều khiển", "ECU": "ECU", "NhienLieu": "Nhiên liệu", "ChongQuaTai": "Chống quá tải",
      "ManHinh": "Màn hình", "DongCo": "Động cơ", "HopSo": "Hộp số", "Phanh": "Phanh", "Lai": "Lái",
      "DieuHoa": "Điều hòa", "Khung": "Khung nâng", "Can": "Cần", "Toi": "Tời", "Pin": "Pin/sạc",
      "ThuyLuc": "Thủy lực", "Dien": "Điện", "TongThe": ""}
NN = {"EN": "Tiếng Anh", "VI": "Tiếng Việt", "ES": "Tây Ban Nha", "DE": "Đức", "FR": "Pháp", "IT": "Ý",
      "PT": "Bồ Đào Nha", "RU": "Nga", "KO": "Hàn", "ZH": "Trung", "TR": "Thổ Nhĩ Kỳ"}


def bo_dau(s):
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def file_id(link):
    m = re.search(r"/d/([\w-]+)", link or "")
    return m.group(1) if m else ""


def doc_nguon(src):
    """src = đường dẫn CSV hoặc URL Apps Script trả JSON {items:[...]}"""
    if src.startswith("http"):
        import urllib.request
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [{k: ("" if v is None else str(v)) for k, v in it.items()} for it in data.get("items", [])]
    with open(src, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def doc_csv(src):
    rows = doc_nguon(src)
    items = []
    for r in rows:
        fid = r.get("File ID xem") or file_id(r.get("Link xem"))
        if not fid:
            continue
        model = (r.get("Model") or "").strip()
        model = "" if model == "Chung" else model
        may, tl, ht = MAY.get(r.get("Loại máy", ""), r.get("Loại máy", "")), TL.get(r.get("Loại TL", ""), r.get("Loại TL", "")), HT.get(r.get("Hệ thống", ""), "")
        tieu_de = " ".join(x for x in (r.get("Hãng", ""), model) if x) + f" – {tl}" + (f" {ht}" if ht else "")
        try:
            trang = int(float(r.get("Số trang") or 0))
        except ValueError:
            trang = 0
        it = {"id": r.get("ID", ""), "t": tieu_de, "h": r.get("Hãng", ""), "m": model, "may": may, "tl": tl,
              "ht": ht, "nn": r.get("Ngôn ngữ") or "EN", "p": trang, "scan": r.get("Dạng PDF") == "Scan",
              "kw": r.get("Từ khóa VN", ""), "c": r.get("Mã áp dụng", ""), "f": fid,
              "d": (r.get("Ngày thêm") or "")[:10]}
        it["s"] = bo_dau(" ".join([it["t"], it["h"], it["m"], may, tl, ht, it["kw"], it["c"], r.get("Tên file", ""),
                                   r.get("Thư mục Drive", "")]))
        items.append(it)
    items.sort(key=lambda x: (x["may"], x["h"], x["m"], x["tl"]))
    return items


def li(it):
    e = html.escape
    meta = " · ".join(x for x in (it["id"], it["may"], it["tl"], f'{it["p"]} trang' if it["p"] else "", NN.get(it["nn"], it["nn"])) if x)
    return (f'<li class="item" data-id="{e(it["id"])}"><a href="d/{e(it["id"])}.html" class="open">'
            f'<span class="tt">{e(it["t"])}</span><span class="meta">{e(meta)}</span>'
            + (f'<span class="codes">Áp dụng: {e(it["c"])}</span>' if it["c"] else "")
            + f'<span class="kw">{e(it["kw"])}</span></a></li>')


TEMPLATE = r"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TEN__</title>
<meta name="description" content="__MOTA__">
<link rel="canonical" href="__URL__">__VERIFY__
<meta property="og:title" content="__TEN__"><meta property="og:description" content="__MOTA__">
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--mute:#667085;--line:#e4e7ec;--acc:#c2410c;--acc2:#fff3ec;--chip:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--card:#1b2029;--ink:#e8ebf0;--mute:#98a2b3;--line:#2b3240;--acc:#fb923c;--acc2:#2a1d14;--chip:#252b36}}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
header{padding:28px 16px 12px;max-width:1200px;margin:auto}
h1{font-size:22px;margin:0 0 4px}header p{margin:0;color:var(--mute);font-size:14px}
.bar{position:sticky;top:0;z-index:5;background:var(--bg);padding:10px 16px 8px;max-width:1200px;margin:auto}
#q{width:100%;font-size:18px;padding:14px 18px;border:1px solid var(--line);border-radius:28px;background:var(--card);color:var(--ink);outline:none;box-shadow:0 1px 3px #0000000d}
#q:focus{border-color:var(--acc)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.chip{border:1px solid var(--line);background:var(--chip);color:var(--ink);border-radius:16px;padding:4px 12px;font-size:13px;cursor:pointer}
.chip.on{background:var(--acc);border-color:var(--acc);color:#fff}
.count{color:var(--mute);font-size:13px;margin-top:8px}
main{max-width:1200px;margin:auto;padding:0 16px 40px;display:grid;grid-template-columns:minmax(0,1fr);gap:16px}
main.split{grid-template-columns:minmax(0,420px) minmax(0,1fr)}
ul{list-style:none;margin:0;padding:0}
.item{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-bottom:8px}
.item.sel{border-color:var(--acc);background:var(--acc2)}
.open{display:block;padding:10px 14px;color:inherit;text-decoration:none}
.tt{display:block;font-weight:600}.meta{display:block;color:var(--mute);font-size:13px}
.codes{display:block;font-size:12px;color:var(--acc);font-family:ui-monospace,Consolas,monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.kw{display:block;color:var(--mute);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#viewer{display:none;position:sticky;top:120px;height:calc(100vh - 140px);background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;flex-direction:column}
main.split #viewer{display:flex}
.vh{display:flex;gap:8px;align-items:center;padding:8px 12px;border-bottom:1px solid var(--line)}
.vh b{flex:1;font-size:14px}
.btn{border:0;border-radius:8px;padding:7px 12px;font-size:13px;cursor:pointer;text-decoration:none;display:inline-block}
.btn.p{background:var(--acc);color:#fff}.btn.g{background:var(--chip);color:var(--ink)}
iframe{flex:1;border:0;width:100%;background:#fff}
.top{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.top h1{flex:1;min-width:220px}.top h1 a{color:inherit;text-decoration:none}
.code{font:600 13px/1 ui-monospace,Consolas,monospace;background:var(--chip);border:1px solid var(--line);border-radius:6px;padding:5px 8px}
#toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);max-width:92vw;background:#1d2330;color:#fff;padding:12px 16px;border-radius:10px;font-size:14px;box-shadow:0 6px 24px #0004;z-index:50;display:none}
#toast b{color:#fdba74}
.empty{padding:24px;text-align:center;color:var(--mute)}
footer{max-width:1200px;margin:auto;padding:16px;color:var(--mute);font-size:12px}
@media (max-width:820px){main.split{grid-template-columns:1fr}
 #viewer{position:fixed;inset:0;top:0;height:100%;border-radius:0;z-index:20}
 .vh{flex-wrap:wrap}.vh #vt{order:9;flex-basis:100%;font-size:13px}.vh #dl{flex:1}}
</style>
</head>
<body>
<header>
  <div class="top"><h1><a href="./" class="home">__TEN__</a></h1>
    <a href="./" class="btn g home">⌂ Trang chủ</a>
    <a href="__ZALO__" class="btn p" target="_blank" rel="noopener">Zalo</a></div>
  <p>__SO__ tài liệu tiếng Anh, xem miễn phí, chỉ xem trực tuyến. Cần bản đầy đủ hoặc bản dịch tiếng Việt: <a href="__ZALO__" target="_blank" rel="noopener">nhắn Zalo</a>.</p>
</header>
<div class="bar">
  <input id="q" type="search" placeholder="Gõ hãng, model, mã lỗi… vd: allison mã lỗi, pc200 thủy lực, cẩu không ra cần" autocomplete="off" autofocus>
  <div class="chips" id="chips"></div>
  <div class="count" id="count"></div>
</div>
<main id="main">
  <section><ul id="list">__LIST__</ul><div class="empty" id="empty" hidden>Chưa có tài liệu phù hợp. <a href="__ZALO__" target="_blank" rel="noopener">Nhắn Zalo yêu cầu tài liệu</a>__FORM__</div></section>
  <aside id="viewer">
    <div class="vh"><button class="btn g home" title="Trang chủ">⌂</button><span class="code" id="vcode"></span><b id="vt"></b>
      <button class="btn p" id="dl">Liên hệ Zalo để download</button>
      <button class="btn g" id="close">Đóng</button></div>
    <iframe id="frame" title="Xem tài liệu" loading="lazy" allow="autoplay"></iframe>
  </aside>
</main>
<div id="toast" role="status"></div>
<footer>Tài liệu thuộc bản quyền của nhà sản xuất, chỉ dùng để tham khảo. Thông số an toàn, áp suất, lực siết luôn đối chiếu bản gốc. Cập nhật __NGAY__.</footer>
<script>
const DATA = __DATA__;
const $ = s => document.querySelector(s);
const norm = s => (s||'').normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/đ/g,'d').replace(/Đ/g,'d').toLowerCase();
const byId = Object.fromEntries(DATA.map(d => [d.id, d]));
const els = [...document.querySelectorAll('#list .item')];
const elById = Object.fromEntries(els.map(e => [e.dataset.id, e]));
let fMay = '', fTl = '';
const mays = [...new Set(DATA.map(d => d.may))].sort(), tls = [...new Set(DATA.map(d => d.tl))].sort();
function chip(label, group, val){ const b=document.createElement('button'); b.className='chip'; b.textContent=label;
  b.onclick=()=>{ if(group==='may') fMay = fMay===val?'':val; else fTl = fTl===val?'':val; render(); }; b.dataset.g=group; b.dataset.v=val; return b; }
mays.forEach(m => $('#chips').append(chip(m,'may',m))); tls.forEach(t => $('#chips').append(chip(t,'tl',t)));
let timer;
$('#q').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(render, 80); });
function render(){
  const toks = norm($('#q').value).split(/[\s,;]+/).filter(Boolean);
  const cmp = t => t.replace(/[-\/._]/g, '');   // d110s5 = D110S-5, pc2008 = PC200-8
  let n = 0;
  for (const d of DATA){
    const ok = (!fMay || d.may===fMay) && (!fTl || d.tl===fTl) && toks.every(t => d.s.includes(t) || (d.sc || (d.sc = cmp(d.s))).includes(cmp(t)));
    elById[d.id].hidden = !ok; if (ok) n++;
  }
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', (c.dataset.g==='may'?fMay:fTl)===c.dataset.v));
  $('#count').textContent = n + ' / ' + DATA.length + ' tài liệu';
  $('#empty').hidden = n > 0;
  if (toks.length && !n) logMiss(toks.join(' '));
}
function openDoc(id, push){
  const d = byId[id]; if (!d) return;
  els.forEach(e => e.classList.toggle('sel', e.dataset.id===id));
  $('#vt').textContent = d.t; $('#vcode').textContent = d.id; cur = d;
  $('#frame').src = 'https://drive.google.com/file/d/' + d.f + '/preview';
  $('#main').classList.add('split');
  if (push) history.pushState({id}, '', '?id=' + id);
  document.title = d.t + ' | __TEN_JS__';
}
function closeDoc(){ $('#main').classList.remove('split'); $('#frame').src='about:blank'; history.pushState({}, '', location.pathname); }
document.getElementById('list').addEventListener('click', e => { const a = e.target.closest('.open'); if(!a) return; e.preventDefault(); openDoc(a.parentElement.dataset.id, true); });
$('#close').onclick = closeDoc;
let cur = null;
const ZALO = '__ZALO__';
document.querySelectorAll('.home').forEach(a => a.addEventListener('click', e => { e.preventDefault();
  $('#q').value=''; fMay=''; fTl=''; closeDoc(); render(); window.scrollTo({top:0, behavior:'smooth'}); $('#q').focus(); }));
function copyText(t){
  if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(t).then(()=>true, ()=>fallback(t));
  return Promise.resolve(fallback(t));
  function fallback(t){ const a=document.createElement('textarea'); a.value=t; a.style.position='fixed'; a.style.opacity='0';
    document.body.appendChild(a); a.select(); let ok=false; try{ ok=document.execCommand('copy'); }catch(e){} a.remove(); return ok; }
}
function toast(html){ const t=$('#toast'); t.innerHTML=html; t.style.display='block'; clearTimeout(toast.t); toast.t=setTimeout(()=>t.style.display='none', 12000); }
$('#dl').onclick = () => {
  if (!cur) return;
  const link = location.origin + location.pathname + '?id=' + cur.id;
  const msg = 'Chào anh, tôi cần download tài liệu mã ' + cur.id + ': ' + cur.t + '\n' + link;
  window.open(ZALO, '_blank', 'noopener');
  copyText(msg).then(ok => toast(ok
    ? 'Đã sao chép yêu cầu tài liệu <b>' + cur.id + '</b>. Trong Zalo, <b>dán</b> (Ctrl+V hoặc nhấn giữ → Dán) rồi gửi.'
    : 'Khi nhắn Zalo, vui lòng ghi mã tài liệu <b>' + cur.id + '</b>.'));
};
window.onpopstate = () => { const id = new URLSearchParams(location.search).get('id'); id ? openDoc(id) : closeDoc(); };
// Giai đoạn 2: ghi lại từ khóa tìm không ra (gửi về Apps Script) — để trống thì bỏ qua
const LOG_URL = '';
let lastMiss = '';
function logMiss(q){ if(!LOG_URL || q===lastMiss || q.length<3) return; lastMiss=q; clearTimeout(logMiss.t);
  logMiss.t = setTimeout(()=>fetch(LOG_URL+'?miss='+encodeURIComponent(q),{mode:'no-cors'}), 1500); }
render();
const id0 = new URLSearchParams(location.search).get('id'); if (id0) openDoc(id0);
</script>
</body>
</html>
"""


def verify_tag():
    return f'\n<meta name="google-site-verification" content="{html.escape(GOOGLE_VERIFY)}">' if GOOGLE_VERIFY else ""


DOC_PAGE = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESC__">
<link rel="canonical" href="__CANON__">
<meta property="og:title" content="__TITLE__"><meta property="og:description" content="__DESC__"><meta property="og:type" content="article">
<script type="application/ld+json">__LD__</script>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1d2330;--mute:#667085;--line:#e4e7ec;--acc:#c2410c;--chip:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#12151b;--card:#1b2029;--ink:#e8ebf0;--mute:#98a2b3;--line:#2b3240;--acc:#fb923c;--chip:#252b36}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.w{max-width:1000px;margin:auto;padding:16px}nav{font-size:13px;color:var(--mute)}nav a{color:var(--mute)}
h1{font-size:22px;margin:8px 0}.code{font:600 13px ui-monospace,Consolas,monospace;background:var(--chip);border:1px solid var(--line);border-radius:6px;padding:3px 7px}
table{border-collapse:collapse;margin:10px 0;font-size:14px}td{padding:4px 12px 4px 0;vertical-align:top}td:first-child{color:var(--mute);white-space:nowrap}
.btn{display:inline-block;border:0;border-radius:8px;padding:9px 14px;font-size:14px;cursor:pointer;text-decoration:none;background:var(--acc);color:#fff;margin:6px 6px 6px 0}
.btn.g{background:var(--chip);color:var(--ink)}
iframe{width:100%;height:80vh;border:1px solid var(--line);border-radius:10px;background:#fff;margin-top:10px}
ul{padding-left:18px}li{margin:3px 0}a{color:var(--acc)}footer{color:var(--mute);font-size:12px;margin-top:24px}
#toast{position:fixed;left:50%;bottom:24px;transform:translateX(-50%);max-width:92vw;background:#1d2330;color:#fff;padding:12px 16px;border-radius:10px;display:none;z-index:9}
</style></head><body><div class="w">
<nav><a href="../">⌂ Trang chủ</a> › __MAY__ › __HANG__</nav>
<h1>__H1__</h1>
<p><span class="code">__ID__</span> __INTRO__</p>
<table>__ROWS__</table>
<a class="btn g" href="../">⌂ Trang chủ</a><button class="btn" id="dl">Liên hệ Zalo để download</button>
<iframe src="https://drive.google.com/file/d/__FID__/preview" loading="lazy" title="Xem tài liệu __ID__"></iframe>
__RELATED__
<footer>Tài liệu thuộc bản quyền của nhà sản xuất, chỉ dùng để tham khảo. Thông số an toàn, áp suất, lực siết luôn đối chiếu bản gốc.</footer>
</div><div id="toast"></div>
<script>
document.getElementById('dl').onclick=function(){
  var msg='Chào anh, tôi cần download tài liệu mã __ID__: __H1JS__\n'+location.href;
  window.open('__ZALO__','_blank','noopener');
  var t=document.getElementById('toast');
  function show(ok){t.innerHTML=ok?'Đã sao chép yêu cầu tài liệu <b>__ID__</b>. Trong Zalo, dán (Ctrl+V hoặc nhấn giữ → Dán) rồi gửi.':'Khi nhắn Zalo, vui lòng ghi mã tài liệu <b>__ID__</b>.';t.style.display='block';setTimeout(function(){t.style.display='none'},12000);}
  if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(msg).then(function(){show(true)},function(){show(false)});}else show(false);
};
</script></body></html>
"""


def write_doc_pages(items):
    """Mỗi tài liệu 1 trang riêng d/<ID>.html (Google tìm theo từng model/mã) + sitemap.xml + robots.txt."""
    e = html.escape
    os.makedirs("d", exist_ok=True)
    keep = set()
    base = URL_WEB.rstrip("/") + "/"
    for it in items:
        codes = [c.strip() for c in it["c"].split(",") if c.strip()]
        name = " ".join(x for x in (it["h"], it["m"]) if x)
        h1 = f'{name} – {it["tl"]}' + (f' {it["ht"]}' if it["ht"] else "") + f' ({it["may"]})'
        title = f'{h1}' + (f' – {", ".join(codes[:6])}' if codes else "") + " | Tài liệu sửa chữa"
        desc = (f'Tài liệu {it["tl"].lower()} {it["may"].lower()} {name}'
                + (f', áp dụng: {", ".join(codes[:12])}' if codes else "")
                + f'. {it["p"]} trang, {NN.get(it["nn"], it["nn"]).lower()}. Xem miễn phí, nhận dịch tiếng Việt.')
        rows = [("Hãng", it["h"]), ("Model", it["m"] or "—"), ("Loại máy", it["may"]), ("Loại tài liệu", it["tl"]),
                ("Hệ thống", it["ht"]), ("Áp dụng cho", ", ".join(codes)), ("Số trang", str(it["p"] or "")),
                ("Ngôn ngữ", NN.get(it["nn"], it["nn"])), ("Từ khóa", it["kw"])]
        rows_html = "".join(f"<tr><td>{e(k)}</td><td>{e(v)}</td></tr>" for k, v in rows if v)
        rel = [x for x in items if x["id"] != it["id"] and x["h"] == it["h"] and x["may"] == it["may"]][:12]
        if len(rel) < 6:
            rel += [x for x in items if x["id"] != it["id"] and x["may"] == it["may"] and x not in rel][:12 - len(rel)]
        rel_html = ("<h2 style='font-size:17px;margin-top:22px'>Tài liệu liên quan</h2><ul>"
                    + "".join(f'<li><a href="{e(x["id"])}.html">{e(x["t"])}</a></li>' for x in rel) + "</ul>") if rel else ""
        ld = json.dumps({"@context": "https://schema.org", "@type": "DigitalDocument", "name": h1, "description": desc,
                         "inLanguage": it["nn"].lower(), "url": base + f'd/{it["id"]}.html',
                         "keywords": ", ".join(codes + [it["kw"]])}, ensure_ascii=False)
        intro = (f'Tài liệu {e(it["tl"].lower())} cho {e(it["may"].lower())} {e(name)}'
                 + (f', áp dụng cho các model/động cơ: <b>{e(", ".join(codes))}</b>' if codes else "") + ".")
        page = (DOC_PAGE.replace("__TITLE__", e(title)).replace("__DESC__", e(desc))
                .replace("__CANON__", e(base + f'd/{it["id"]}.html')).replace("__LD__", ld.replace("</", "<\\/"))
                .replace("__MAY__", e(it["may"])).replace("__HANG__", e(it["h"])).replace("__H1__", e(h1))
                .replace("__H1JS__", e(h1).replace("'", " ")).replace("__INTRO__", intro).replace("__ROWS__", rows_html)
                .replace("__FID__", e(it["f"])).replace("__RELATED__", rel_html)
                .replace("__ZALO__", e(ZALO)).replace("__ID__", e(it["id"])))
        fn = f'{it["id"]}.html'
        keep.add(fn)
        with open(os.path.join("d", fn), "w", encoding="utf-8") as f:
            f.write(page)
    for fn in os.listdir("d"):   # xóa trang của tài liệu đã gỡ
        if fn.endswith(".html") and fn not in keep:
            os.remove(os.path.join("d", fn))
    today = date.today().isoformat()
    urls = [f"<url><loc>{e(base)}</loc><lastmod>{today}</lastmod><priority>1.0</priority></url>"]
    urls += [f'<url><loc>{e(base)}d/{e(it["id"])}.html</loc><lastmod>{it["d"] or today}</lastmod></url>' for it in items]
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "\n".join(urls) + "\n</urlset>\n")
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n")
    return len(items)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DATA_URL
    if not src:
        sys.exit('Cách dùng: python tao_web.py "Thu vien tai lieu - DanhMuc.csv"  (hoặc điền DATA_URL)')
    items = doc_csv(src)
    if len(items) < 10:   # an toàn: lỗi mạng / dữ liệu rỗng thì KHÔNG ghi đè trang đang chạy
        sys.exit(f"Chỉ đọc được {len(items)} tài liệu — dừng, không ghi đè index.html.")
    data = [{k: v for k, v in it.items()} for it in items]
    page = (TEMPLATE.replace("__TEN_JS__", TEN_WEB.replace("'", ""))
            .replace("__TEN__", html.escape(TEN_WEB)).replace("__MOTA__", html.escape(MO_TA))
            .replace("__URL__", html.escape(URL_WEB)).replace("__VERIFY__", verify_tag()).replace("__ZALO__", html.escape(ZALO))
            .replace("__FORM__", f' hoặc <a href="{html.escape(FORM_YEU_CAU)}" target="_blank" rel="noopener">gửi form</a>.' if FORM_YEU_CAU else ".")
            .replace("__SO__", str(len(items))).replace("__NGAY__", date.today().strftime("%d/%m/%Y"))
            .replace("__LIST__", "\n".join(li(it) for it in items))
            .replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(page)
    n = write_doc_pages(items)
    print(f"Đã tạo index.html với {len(items)} tài liệu ({len(page) / 1024:.0f} KB), {n} trang riêng, sitemap.xml, robots.txt.")


if __name__ == "__main__":
    main()
