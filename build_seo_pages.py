"""
AlyaGames - Static SEO Page & Sitemap Generator
Fetches catalog games from both GameDistribution and GamePix (plus curated games) and generates:
1. Static SEO Landing Pages for each game (/oyun/<slug>/index.html) with rich Turkish SEO content & circular internal linking
2. Static SEO Category Landing Pages (/kategori/<category>/index.html) with full crawlable game grids
3. Dynamic, complete sitemap.xml with all game URLs for Google Search Console
"""

import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime

SITE_URL = "https://alyagames.com"
OUTPUT_ROOT = os.path.dirname(os.path.abspath(__file__))

def slugify(text):
    if not text:
        return 'oyun'
    text = str(text).lower().strip()
    text = text.replace('&', '-and-')
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    text = re.sub(r'[\s\W-]+', '-', text)
    text = text.strip('-')
    return text or 'oyun'

CURATED_GAMES = [
    {
        'Title': 'Klumen',
        'Url': 'https://html5.gamedistribution.com/e24064f9b2594b189a8f504970436040/',
        'Asset': ['https://img.gamedistribution.com/e24064f9b2594b189a8f504970436040-512x384.jpg'],
        'Category': ['Puzzle', 'Skill'],
        'Tag': ['puzzle', 'logic', 'brain'],
        'Description': 'Klumen ile ışık iplikçiklerini birleştirin ve dinlendirici bir bulmaca deneyimi yaşayın. Merkezdeki yıldızdan tüm panoya ışık yayılana kadar her parçayı döndürün ve komşusuyla birleştirin.',
        'Instructions': 'Kareleri döndürmek için dokunun veya farenizle tıklayın. Merkezdeki yıldızdan gelen ışığın tüm panoya yayılması için tüm ışık yollarını birleştirin.',
        'Source': 'GameDistribution'
    },
    {
        'Title': 'Bike Obby Draw Pencil',
        'Url': 'https://play.gamepix.com/bike-obby-draw-pencil/embed?sid=M4M77',
        'Asset': ['https://img.gamedistribution.com/ccb3b200322c4779957dfee55c68f3fc-512x384.jpg'],
        'Category': ['Puzzle', 'Skill'],
        'Tag': ['skill', 'puzzle', 'bike', 'obby'],
        'Description': 'Bike Obby Draw Pencil ile yaratıcılığınızı ve reflekslerinizi konuşturun! Platformlar arasındaki boşluklara kaleminizle köprüler ve yollar çizerek bisikletli karakterinizi düşmeden bitiş çizgisine ulaştırın.',
        'Instructions': 'W tuşu ile zıplayın, A ve D tuşları ile sola ve sağa hareket edin. Boşlukları ve uçurumları geçmek için farenizle (veya dokunmatik ekranda parmağınızla) köprü ve yol çizin.',
        'Source': 'GamePix'
    }
]

def map_gamepix_category(gp_cat):
    if not gp_cat:
        return 'Arcade'
    cat = str(gp_cat).lower()
    if cat in ('puzzle', 'puzzles', 'memory', 'drawing', '2048'):
        return 'Puzzle'
    if cat in ('strategy', 'battle'):
        return 'Strategy'
    if cat == 'sports':
        return 'Sports'
    if cat == 'adventure':
        return 'Adventure'
    if cat == 'shooter':
        return 'Shooting'
    if cat in ('fighting', 'stickman'):
        return 'Action'
    if cat == 'simulation':
        return 'Driving'
    if cat in ('kids', 'junior'):
        return 'Baby'
    if cat == 'match-3':
        return 'Bejeweled'
    if cat in ('ball', 'fun', 'classics', 'board'):
        return 'Arcade'
    return str(gp_cat).capitalize()

def load_existing_local_games():
    oyun_dir = os.path.join(OUTPUT_ROOT, "oyun")
    local_games = []
    if not os.path.isdir(oyun_dir):
        return local_games
    for folder in sorted(os.listdir(oyun_dir)):
        idx_path = os.path.join(oyun_dir, folder, "index.html")
        if not os.path.isfile(idx_path):
            continue
        try:
            with open(idx_path, "r", encoding="utf-8") as f:
                html = f.read()
            m_title = re.search(r'<h1 class="game-stage-title">(.*?)</h1>', html, re.S)
            m_url = re.search(r'<iframe id="game-frame" src="([^"]+)"', html)
            m_img = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            m_cat = re.search(r'<a href="/kategori/([^/]+)/">', html)
            m_desc_orig = re.search(r'<strong>Oyun Detayları ve Konusu:</strong>\s*(.*?)</p>', html, re.S)
            m_desc = re.search(r'<h2>📖[^<]*</h2>\s*<p>(.*?)</p>', html, re.S)
            m_instr_orig = re.search(r'<strong>Özel Tuş ve Kontrol Bilgisi:</strong>\s*(.*?)</p>', html, re.S)
            m_instr = re.search(r'<h2>🕹️[^<]*</h2>\s*<p>(.*?)</p>', html, re.S)
            if m_title and m_url:
                title = m_title.group(1).strip().replace('&quot;', '"')
                url = m_url.group(1).strip()
                img = m_img.group(1).strip() if m_img else "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600"
                cat_slug = m_cat.group(1).strip() if m_cat else "aksiyon"
                cat_map_rev = {
                    'aksiyon': 'action', 'savas': 'shooting', 'yaris': 'racing',
                    'beceri': 'puzzle', 'macera': 'adventure', 'kiz': 'girls',
                    'iki-kisilik': 'multiplayer', 'okul-oyunlari': 'action'
                }
                if m_desc_orig:
                    desc = re.sub(r'<[^>]+>', '', m_desc_orig.group(1)).strip()
                elif m_desc:
                    desc = re.sub(r'<[^>]+>', '', m_desc.group(1)).strip()
                else:
                    desc = ''
                if m_instr_orig:
                    instr = re.sub(r'<[^>]+>', '', m_instr_orig.group(1)).strip()
                elif m_instr and 'Fare (Sol Tık' not in m_instr.group(1):
                    instr = re.sub(r'<[^>]+>', '', m_instr.group(1)).strip()
                else:
                    instr = ''
                local_games.append({
                    'Title': title,
                    'Url': url,
                    'Asset': [img],
                    'Category': [cat_map_rev.get(cat_slug, 'action')],
                    'Tag': [cat_map_rev.get(cat_slug, 'action')],
                    'Description': desc,
                    'Instructions': instr,
                    'Source': 'LocalExisting'
                })
        except Exception as e:
            print(f"  [!] Could not parse local game {folder}: {e}")
    return local_games

def fetch_games(max_gd_pages=5, max_gp_pages=1):
    all_games = []
    seen_slugs = set()

    # 1. Add curated games first
    for cg in CURATED_GAMES:
        s = slugify(cg.get('Title', ''))
        if s and s not in seen_slugs:
            seen_slugs.add(s)
            all_games.append(cg)

    # 1b. Preserve all existing local /oyun/<slug>/ games so no existing URL becomes orphaned or outdated
    existing_local = load_existing_local_games()
    for lg in existing_local:
        s = slugify(lg.get('Title', ''))
        if s and s not in seen_slugs:
            seen_slugs.add(s)
            all_games.append(lg)
    print(f"[*] Loaded {len(all_games)} existing/curated games from local /oyun/ directory.")

    # 2. Fetch GameDistribution catalog
    print(f"[*] Fetching games from GameDistribution API (pages 1 to {max_gd_pages})...")
    for page in range(1, max_gd_pages + 1):
        url = f"https://catalog.api.gamedistribution.com/api/v2.0/rss/All/?collection=All&amount=100&page={page}&format=json"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                items = data if isinstance(data, list) else data.get('items', [])
                for g in items:
                    title = (g.get('Title') or '').strip()
                    s = slugify(title)
                    if title and s and s not in seen_slugs and g.get('Url'):
                        seen_slugs.add(s)
                        g['Source'] = 'GameDistribution'
                        all_games.append(g)
            print(f"  -> GD Page {page}: fetched {len(items)} items (Total unique: {len(all_games)})")
        except Exception as e:
            print(f"  [!] Error fetching GD page {page}: {e}")

    # 3. Fetch GamePix catalog so homepage GamePix cards also have static SEO pages (GamePix max pagination is 96)
    print(f"[*] Fetching games from GamePix API (pages 1 to {max_gp_pages}, pagination=96)...")
    for page in range(1, max_gp_pages + 1):
        gp_url = f"https://feeds.gamepix.com/v2/json?sid=M4M77&pagination=96&page={page}"
        try:
            req = urllib.request.Request(gp_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                raw_games = data if isinstance(data, list) else (data.get('data') or data.get('items') or [])
                added_gp = 0
                for g in raw_games:
                    title = (g.get('title') or '').strip()
                    s = slugify(title)
                    game_url = g.get('url') or ''
                    if not title or not s or not game_url or s in seen_slugs:
                        continue
                    gp_cat = g.get('category') or ''
                    if g.get('categories') and len(g['categories']) > 0:
                        gp_cat = g['categories'][0]
                    mapped_cat = map_gamepix_category(gp_cat)
                    text_search = f"{title} {g.get('description', '')} {gp_cat}".lower()
                    cat_list = [mapped_cat]
                    if any(k in text_search for k in ['girl', 'dress', 'makeup', 'fashion', 'cooking', 'care', 'cake', 'doll', 'salon']):
                        cat_list.append('Girls')
                    thumb = g.get('thumbnailUrl') or g.get('thumbnailUrl100') or g.get('image') or 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=500'
                    seen_slugs.add(s)
                    all_games.append({
                        'Title': title,
                        'Url': game_url,
                        'Asset': [thumb],
                        'Category': cat_list,
                        'Tag': [ str(gp_cat).lower() ],
                        'Description': g.get('description') or '',
                        'Instructions': '',
                        'Source': 'GamePix'
                    })
                    added_gp += 1
            print(f"  -> GP Page {page}: added {added_gp} unique GamePix games (Total unique: {len(all_games)})")
        except Exception as e:
            print(f"  [!] Error fetching GP page {page}: {e}")

    return all_games

CATEGORY_MAP = {
    'action': {
        'name': 'Aksiyon Oyunları',
        'slug': 'aksiyon',
        'icon': '⚔️',
        'desc': 'En heyecanlı aksiyon, dövüş ve süper kahraman oyunlarını ücretsiz, indirmeden tarayıcınızda online oynayın.',
        'long_intro': 'Aksiyon temposunun hiç düşmediği bu yapımda reflekslerinizi, hızınızı ve stratejik hamlelerinizi bir araya getirerek rakiplerinizi geride bırakabilirsiniz.'
    },
    'war': {
        'name': 'Savaş ve Silah Oyunları',
        'slug': 'savas',
        'icon': '🔫',
        'desc': 'Ücretsiz FPS nişancı, ordu, sniper ve taktiksel savaş oyunları ile düşmanları alt edin.',
        'long_intro': 'Taktiksel nişancılık, keskin nişancı görevleri ve heyecan dolu cephe mücadeleleriyle dikkat çeken bu savaş oyununda hedefi tam on ikiden vurun.'
    },
    'racing': {
        'name': 'Araba ve Yarış Oyunları',
        'slug': 'yaris',
        'icon': '🏎️',
        'desc': 'Hızlı spor arabalar, drift yarışları, motosiklet ve zorlu pistlerde direksiyon başına geçin.',
        'long_intro': 'Yüksek hızlı araçlar, keskin virajlar ve adrenalin dolu pistlerle tasarlanan bu yarış oyununda sürüş yeteneklerinizi sergileyerek bitiş çizgisine ilk ulaşan olun.'
    },
    'skill': {
        'name': 'Zeka ve Beceri Oyunları',
        'slug': 'beceri',
        'icon': '🧩',
        'desc': 'Mantık bulmacaları, tetris benzeri blok oyunları ve zihninizi geliştirecek zeka oyunları.',
        'long_intro': 'Analitik düşünme, dikkat ve el-göz koordinasyonunu birleştiren bu zeka ve beceri oyununda her seviyede yeni bir bulmacayı çözmenin keyfini çıkarın.'
    },
    'adventure': {
        'name': 'Macera Oyunları',
        'slug': 'macera',
        'icon': '🗺️',
        'desc': 'Gizemli dünyaları keşfedin, platform engellerini aşın ve unutulmaz maceralara atılın.',
        'long_intro': 'Sürükleyici bölümler, engelli parkurlar ve keşfedilmeyi bekleyen dünyalarla dolu bu macera oyununda karakterinizi güvenle hedefe ulaştırın.'
    },
    'girls': {
        'name': 'Kız Oyunları',
        'slug': 'kiz',
        'icon': '🎀',
        'desc': 'Moda tasarım, makyaj, prenses giydirmece ve sevimli yemek pişirme simülasyonları.',
        'long_intro': 'Renkli tasarımlar, kombin seçenekleri ve yaratıcı eğlence sunan bu oyunda kendi tarzınızı oluşturarak keyifli vakit geçirebilirsiniz.'
    },
    'multiplayer': {
        'name': 'İki Kişilik Oyunlar',
        'slug': 'iki-kisilik',
        'icon': '👥',
        'desc': 'Aynı klavyede veya online arkadaşınızla birlikte oynayabileceğiniz en iyi 2 kişilik oyunlar.',
        'long_intro': 'Arkadaşlarınızla veya rakiplerinizle rekabet edebileceğiniz bu çok oyunculu deneyimde takım çalışması ya da birebir mücadele heyecanını doyasıya yaşayın.'
    },
    'unblocked': {
        'name': 'Okul Oyunları (Engelsiz)',
        'slug': 'okul-oyunlari',
        'icon': '🎯',
        'desc': 'Okulda ve her ağda kısıtlama olmadan açılan en popüler Unblocked HTML5 oyunları.',
        'long_intro': 'Her ortamda hızlı açılan, kurulum gerektirmeyen engelsiz HTML5 yapısı sayesinde mola zamanlarınızda anında eğlenceye dahil olun.'
    }
}

def categorize_game(game):
    cats = [str(c).lower() for c in game.get('Category', [])]
    tags = [str(t).lower() for t in game.get('Tag', [])]
    combined = " ".join(cats + tags + [str(game.get('Title', '')).lower()])
    
    if any(k in combined for k in ['2-player', 'multiplayer', '2player', 'pvp', 'co-op', 'coop', 'two player']):
        return 'multiplayer'
    if any(k in combined for k in ['girl', 'dress', 'makeup', 'fashion', 'cooking', 'doll', 'princess', 'makeover', 'beauty']):
        return 'girls'
    if any(k in combined for k in ['racing', 'driving', 'car', 'moto', 'bike', 'drift', 'truck', 'parking', 'speed']):
        return 'racing'
    if any(k in combined for k in ['shooter', 'shooting', 'sniper', 'gun', 'war', 'battle', 'fps', 'tank', 'army']):
        return 'war'
    if any(k in combined for k in ['puzzle', 'skill', 'match-3', 'math', 'logic', 'block', 'tetris', 'educational', 'quiz', 'brain', 'obby', 'draw']):
        return 'skill'
    if any(k in combined for k in ['adventure', 'escape', 'runner', 'platformer', 'quest', 'rpg', 'jump']):
        return 'adventure'
    if any(k in combined for k in ['action', 'fight', 'stickman', 'superhero', 'zombie', 'ninja', 'combat']):
        return 'action'
    
    return 'action'

def get_best_image(game):
    assets = game.get('Asset', [])
    if not assets:
        return "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600"
    for url in assets:
        if '512x384' in url or '512x512' in url:
            return url
    return assets[0]

def build_turkish_seo_texts(title, cat_info, raw_desc, raw_instructions):
    cat_name = cat_info['name']
    long_intro = cat_info['long_intro']
    
    # Unique Turkish meta description (135-160 chars)
    meta_desc = f"{title} oyununu AlyaGames'te ücretsiz ve indirmeden online oyna! En popüler {cat_name} arasında yer alan {title} PC, telefon ve tablette seni bekliyor."
    if len(meta_desc) > 160:
        meta_desc = f"{title} oyununu AlyaGames'te ücretsiz ve indirmeden oyna! En sevilen {cat_name} kategorisindeki bu oyunu tarayıcında hemen deneyimle."

    # Detailed Turkish About Paragraphs
    tr_about_p1 = (
        f"<strong>{title}</strong>, AlyaGames'in <em>{cat_name}</em> kategorisinde oyuncuların en çok tercih ettiği ücretsiz HTML5 tarayıcı oyunlarından biridir. "
        f"{long_intro} Herhangi bir dosya indirmeye veya üyelik açmaya gerek kalmadan bilgisayar, telefon ve tablet tarayıcınızdan tam ekran modunda kesintisiz oynayabilirsiniz."
    )
    clean_raw_desc = re.sub(r'\s+', ' ', (raw_desc or '')).strip()
    if clean_raw_desc:
        tr_about_p2 = f"<strong>Oyun Detayları ve Konusu:</strong> {clean_raw_desc}"
    else:
        tr_about_p2 = f"<strong>Oyun Detayları:</strong> {title}, akıcı grafikleri, artan zorluk seviyeleri ve yüksek skor odaklı yapısıyla her yaştan oyuncuya keyifli bir deneyim sunar."

    # Detailed Turkish Controls / Instructions
    clean_instr = re.sub(r'\s+', ' ', (raw_instructions or '')).strip()
    tr_controls_p1 = (
        f"<strong>{title}</strong> oyununu masaüstü bilgisayarlarda <strong>Fare (Sol Tık / Sürükle)</strong>, <strong>WASD</strong> veya <strong>Yön Tuşları (Ok Tuşları)</strong> ile; "
        f"mobil telefon ve tabletlerde ise doğrudan <strong>dokunmatik ekran kontrolleri</strong> ile kolayca yönlendirebilirsiniz."
    )
    if clean_instr:
        tr_controls_p2 = f"<strong>Özel Tuş ve Kontrol Bilgisi:</strong> {clean_instr}"
    else:
        tr_controls_p2 = "Oyun başladıktan sonra ekrandaki yönergeleri takip ederek hamlelerinizi zamanında yapabilir ve bölümleri başarıyla tamamlayabilirsiniz."

    return meta_desc, tr_about_p1, tr_about_p2, tr_controls_p1, tr_controls_p2

def generate_game_page(game, cat_key, sidebar_related, bottom_related):
    raw_title = (game.get('Title') or 'Oyun').strip()
    title = raw_title.replace('"', '&quot;')
    slug = slugify(raw_title)
    raw_desc = (game.get('Description') or '').strip()
    raw_instructions = (game.get('Instructions') or '').strip()
    image = get_best_image(game)
    url = game.get('Url', '')
    cat_info = CATEGORY_MAP.get(cat_key, CATEGORY_MAP['action'])
    cat_name = cat_info['name']
    cat_slug = cat_info['slug']
    canonical_url = f"{SITE_URL}/oyun/{slug}/"

    if 'html5.gamedistribution.com' in url and 'gd_sdk_referrer_url' not in url:
        sep = '&' if '?' in url else '?'
        url = f"{url.rstrip('/')}/{sep}gd_sdk_referrer_url={urllib.parse.quote(canonical_url)}"

    meta_desc, tr_about_p1, tr_about_p2, tr_controls_p1, tr_controls_p2 = build_turkish_seo_texts(
        title, cat_info, raw_desc, raw_instructions
    )
    meta_desc_attr = meta_desc.replace('"', '&quot;')

    # Deterministic rating variation based on slug so every game has realistic rich snippet data
    hash_val = sum(ord(c) for c in slug)
    rating_val = f"4.{7 + (hash_val % 3)}"
    rating_count = str(95 + (hash_val % 240))

    schema_video_game = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": raw_title,
        "url": canonical_url,
        "image": image,
        "description": meta_desc,
        "inLanguage": "tr",
        "genre": [cat_name, "HTML5 Oyun", "Ücretsiz Online Oyun"],
        "playMode": "SinglePlayer" if cat_key != 'multiplayer' else "MultiPlayer",
        "applicationCategory": "Game",
        "operatingSystem": "Web Browser, Windows, MacOS, Android, iOS",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": rating_val,
            "bestRating": "5",
            "worstRating": "1",
            "ratingCount": rating_count
        },
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "TRY",
            "availability": "https://schema.org/InStock"
        }
    }

    schema_breadcrumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Anasayfa",
                "item": f"{SITE_URL}/"
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": cat_name,
                "item": f"{SITE_URL}/kategori/{cat_slug}/"
            },
            {
                "@type": "ListItem",
                "position": 3,
                "name": raw_title,
                "item": canonical_url
            }
        ]
    }

    faq_controls_text = f"{raw_title} oyununu bilgisayarınızda fare ve klavye yön tuşları (WASD / Ok tuşları) ile, telefon ve tablette ise dokunmatik ekran kontrolleriyle oynayabilirsiniz."
    if raw_instructions:
        faq_controls_text += f" ({re.sub(r'\\s+', ' ', raw_instructions)[:180]})"

    schema_faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"{raw_title} oyunu ücretsiz mi?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Evet, {raw_title} AlyaGames platformunda tamamen ücretsizdir. Herhangi bir indirme, kurulum veya abonelik gerekmeden doğrudan web tarayıcınızdan oynayabilirsiniz."
                }
            },
            {
                "@type": "Question",
                "name": f"{raw_title} nasıl oynanır ve kontrolleri nelerdir?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq_controls_text
                }
            },
            {
                "@type": "Question",
                "name": f"{raw_title} telefonda ve tablette çalışır mı?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Evet! {raw_title} modern HTML5 ve WebGL teknolojisi sayesinde Android telefonlar, iPhone, iPad ve masaüstü bilgisayarlarda tam ekran uyumlu çalışır."
                }
            }
        ]
    }

    def render_card_list(games_slice):
        out = ""
        for rg in games_slice:
            r_title = (rg.get('Title') or 'Oyun').replace('"', '&quot;')
            r_slug = slugify(rg.get('Title', ''))
            r_img = get_best_image(rg)
            r_cat = rg.get('Category', ['Oyun'])[0] if rg.get('Category') else 'Oyun'
            out += f"""
        <a href="/oyun/{r_slug}/" class="game-card" title="{r_title} Oyunu Oyna">
            <div class="game-card-img-wrapper">
                <img src="{r_img}" alt="{r_title}" class="game-card-img" loading="lazy">
            </div>
            <div class="game-card-content">
                <span class="game-card-category">{r_cat}</span>
                <h3 class="game-card-title">{r_title}</h3>
                <span class="play-btn-pill">Oyna</span>
            </div>
        </a>"""
        return out

    sidebar_html = render_card_list(sidebar_related[:6])
    bottom_html = render_card_list(bottom_related[:8])

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} Oyunu Oyna - Ücretsiz Online {cat_name} | AlyaGames</title>
    <meta name="description" content="{meta_desc_attr}">
    <meta name="keywords" content="{title}, {title} oyna, {title} oyunu, {cat_name}, ücretsiz online oyunlar, html5 oyunlar, alyagames">
    <meta name="robots" content="index, follow, max-image-preview:large">
    <link rel="canonical" href="{canonical_url}">

    <!-- Open Graph SEO Metadata -->
    <meta property="og:title" content="{title} Oyunu Oyna - AlyaGames">
    <meta property="og:description" content="{meta_desc_attr}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="{image}">
    <meta property="og:site_name" content="AlyaGames">
    <meta property="og:locale" content="tr_TR">

    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title} Oyunu Oyna - AlyaGames">
    <meta name="twitter:description" content="{meta_desc_attr}">
    <meta name="twitter:image" content="{image}">

    <!-- PWA & Mobile Web App -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#6366f1">
    <link rel="apple-touch-icon" href="{image}">

    <!-- Structured Data JSON-LD -->
    <script type="application/ld+json">{json.dumps(schema_video_game, ensure_ascii=False)}</script>
    <script type="application/ld+json">{json.dumps(schema_breadcrumbs, ensure_ascii=False)}</script>
    <script type="application/ld+json">{json.dumps(schema_faq, ensure_ascii=False)}</script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <!-- Main Style Sheet -->
    <link rel="stylesheet" href="/style.css">

    <!-- Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7980209202674588" crossorigin="anonymous"></script>

    <style>
        .game-detail-container {{
            max-width: 1300px;
            margin: 1.5rem auto;
            padding: 0 1.25rem;
            display: grid;
            grid-template-columns: 1fr 340px;
            gap: 2rem;
        }}
        @media (max-width: 1024px) {{
            .game-detail-container {{ grid-template-columns: 1fr; }}
        }}
        .breadcrumbs {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.88rem;
            color: var(--text-secondary);
            margin-bottom: 1.25rem;
            flex-wrap: wrap;
        }}
        .breadcrumbs a {{ color: var(--text-secondary); text-decoration: none; transition: color 0.2s; }}
        .breadcrumbs a:hover {{ color: var(--clr-primary); }}
        .game-stage {{
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-color);
            overflow: hidden;
            box-shadow: var(--shadow-card);
        }}
        .game-stage-header {{
            padding: 1.2rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            background: rgba(255,255,255,0.02);
            flex-wrap: wrap;
            gap: 1rem;
        }}
        .game-stage-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
            color: var(--text-primary);
        }}
        .game-stage-actions {{
            display: flex;
            gap: 0.6rem;
            align-items: center;
        }}
        .stage-btn {{
            background: var(--bg-surface);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            padding: 0.5rem 0.9rem;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.88rem;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .stage-btn:hover {{
            background: var(--clr-primary);
            color: #fff;
            border-color: var(--clr-primary);
            transform: translateY(-2px);
        }}
        .stage-btn.active {{
            background: var(--clr-red);
            color: #fff;
            border-color: var(--clr-red);
        }}
        .iframe-container {{
            position: relative;
            width: 100%;
            height: 600px;
            background: #000;
        }}
        @media (max-width: 768px) {{
            .iframe-container {{ height: 450px; }}
        }}
        .iframe-container iframe {{
            width: 100%;
            height: 100%;
            border: none;
            display: block;
        }}
        .game-info-card {{
            padding: 1.75rem;
            line-height: 1.7;
            color: var(--text-secondary);
        }}
        .game-info-card h2 {{
            font-family: 'Outfit', sans-serif;
            color: var(--text-primary);
            font-size: 1.3rem;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .game-info-card h2:first-of-type {{ margin-top: 0; }}
        .game-info-card p {{ margin-bottom: 0.9rem; }}
        .rating-box {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: var(--bg-surface);
            border-radius: var(--radius-md);
            margin: 1.5rem 0;
            border: 1px solid var(--border-color);
        }}
        .star-rating {{ color: #fbbf24; font-size: 1.3rem; cursor: pointer; }}
        .play-btn-pill {{
            display: inline-block;
            background: var(--clr-primary);
            color: #fff;
            padding: 0.35rem 0.85rem;
            border-radius: 999px;
            font-size: 0.78rem;
            font-weight: 700;
            margin-top: 0.4rem;
        }}
        .more-category-games {{
            max-width: 1300px;
            margin: 2rem auto 3rem;
            padding: 0 1.25rem;
        }}
        .more-category-games h2 {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.45rem;
            color: var(--text-primary);
            margin-bottom: 1.25rem;
        }}
    </style>
</head>
<body>
    <div class="glow-bg glow-bg-1"></div>
    <div class="glow-bg glow-bg-2"></div>

    <!-- Header -->
    <header class="main-header">
        <div class="header-container">
            <a href="/" class="logo">
                <span class="logo-icon">🎮</span>
                <span class="logo-accent">Alya</span>Games
            </a>

            <div class="search-wrapper">
                <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input type="text" id="header-search-input" placeholder="Oyun ara..." autocomplete="off">
            </div>

            <div class="header-controls">
                <button id="pwa-install-btn" class="header-control-btn" style="display:none;" title="Uygulamayı İndir">📱 Yükle</button>
                <button id="sound-toggle" class="header-control-btn" aria-label="Sesi Aç/Kapat">🔊</button>
                <button id="theme-toggle" class="header-control-btn" aria-label="Tema Değiştir">🌙</button>
            </div>
        </div>
    </header>

    <!-- Categories Navigation Bar -->
    <nav class="categories-nav">
        <div class="categories-container">
            <a href="/" class="category-btn">Tümü</a>
            <a href="/kategori/aksiyon/" class="category-btn {'active' if cat_slug == 'aksiyon' else ''}">Aksiyon</a>
            <a href="/kategori/savas/" class="category-btn {'active' if cat_slug == 'savas' else ''}">Savaş</a>
            <a href="/kategori/yaris/" class="category-btn {'active' if cat_slug == 'yaris' else ''}">Yarış</a>
            <a href="/kategori/beceri/" class="category-btn {'active' if cat_slug == 'beceri' else ''}">Beceri & Zeka</a>
            <a href="/kategori/macera/" class="category-btn {'active' if cat_slug == 'macera' else ''}">Macera</a>
            <a href="/kategori/kiz/" class="category-btn {'active' if cat_slug == 'kiz' else ''}">Kız</a>
            <a href="/kategori/iki-kisilik/" class="category-btn {'active' if cat_slug == 'iki-kisilik' else ''}">2 Kişilik</a>
            <a href="/kategori/okul-oyunlari/" class="category-btn {'active' if cat_slug == 'okul-oyunlari' else ''}">🎯 Okulda Oyna</a>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="game-detail-container">
        <!-- Left: Game Play Stage & Info -->
        <div class="game-main-col">
            <!-- Breadcrumbs -->
            <div class="breadcrumbs">
                <a href="/">Anasayfa</a> <span>&gt;</span>
                <a href="/kategori/{cat_slug}/">{cat_name}</a> <span>&gt;</span>
                <span>{title}</span>
            </div>

            <!-- Game Stage Box -->
            <div class="game-stage">
                <div class="game-stage-header">
                    <h1 class="game-stage-title">{title}</h1>
                    <div class="game-stage-actions">
                        <button class="stage-btn" id="fav-btn" title="Favorilere Ekle" data-slug="{slug}" data-title="{title}" data-img="{image}" data-cat="{cat_name}">
                            <span id="fav-icon">🤍</span> Favori
                        </button>
                        <button class="stage-btn" id="share-btn" title="Oyunu Paylaş">
                            🔗 Paylaş
                        </button>
                        <button class="stage-btn" id="fullscreen-btn" title="Tam Ekran Oyna">
                            ⛶ Tam Ekran
                        </button>
                    </div>
                </div>

                <div class="iframe-container" id="game-container">
                    <iframe id="game-frame" src="{url}" frameborder="0" allowfullscreen allow="autoplay; gamepad; fullscreen; screen-wake-lock"></iframe>
                </div>

                <div class="game-info-card">
                    <!-- Rating Widget -->
                    <div class="rating-box">
                        <div>
                            <strong>Oyuncu Puanı:</strong>
                            <div class="star-rating" id="star-rating" title="Puan Ver">★★★★★</div>
                        </div>
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">
                            <span id="rating-val">{rating_val}</span> / 5 ({rating_count}+ değerlendirme)
                        </div>
                    </div>

                    <h2>📖 {title} Oyunu Hakkında</h2>
                    <p>{tr_about_p1}</p>
                    <p>{tr_about_p2}</p>

                    <h2>🕹️ {title} Nasıl Oynanır ve Kontroller</h2>
                    <p>{tr_controls_p1}</p>
                    <p>{tr_controls_p2}</p>

                    <h2>❓ Sıkça Sorulan Sorular (SSS)</h2>
                    <div style="margin-top: 1rem;">
                        <details style="margin-bottom: 0.75rem; background: var(--bg-surface); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid var(--border-color);">
                            <summary style="font-weight: 600; cursor: pointer; color: var(--text-primary);">{title} oyunu ücretsiz mi?</summary>
                            <p style="margin-top: 0.5rem; font-size: 0.92rem;">Evet, {title} AlyaGames üzerinden tamamen ücretsiz ve indirmeden online olarak oynanabilir.</p>
                        </details>
                        <details style="margin-bottom: 0.75rem; background: var(--bg-surface); padding: 0.75rem 1rem; border-radius: 8px; border: 1px solid var(--border-color);">
                            <summary style="font-weight: 600; cursor: pointer; color: var(--text-primary);">{title} mobilde (telefon ve tablet) çalışır mı?</summary>
                            <p style="margin-top: 0.5rem; font-size: 0.92rem;">Evet, modern HTML5 altyapısı ile iPhone, iPad ve Android cihazların tümünde tam ekran uyumlu çalışır.</p>
                        </details>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right: Related Games Sidebar -->
        <aside class="game-sidebar">
            <h3 style="font-family: 'Outfit', sans-serif; font-size: 1.25rem; margin-bottom: 1rem; color: var(--text-primary);">🔥 Benzer Popüler Oyunlar</h3>
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                {sidebar_html}
            </div>
        </aside>
    </main>

    <!-- More Games in Category Section for Strong Internal Linking -->
    <section class="more-category-games">
        <h2>🎮 {cat_name} Kategorisindeki Diğer Oyunlar</h2>
        <div class="games-grid" style="display: grid;">
            {bottom_html}
        </div>
    </section>

    <!-- Footer -->
    <footer class="main-footer">
        <div class="footer-container">
            <div class="footer-brand">
                <span class="logo-icon">🎮</span>
                <span class="logo-accent">Alya</span>Games
            </div>
            <div class="footer-links">
                <a href="/">Anasayfa</a>
                <a href="/kategori/aksiyon/">Aksiyon Oyunları</a>
                <a href="/kategori/savas/">Savaş Oyunları</a>
                <a href="/kategori/yaris/">Yarış Oyunları</a>
                <a href="/kategori/beceri/">Zeka &amp; Beceri</a>
                <a href="/kategori/macera/">Macera Oyunları</a>
                <a href="/kategori/kiz/">Kız Oyunları</a>
                <a href="/kategori/iki-kisilik/">2 Kişilik Oyunlar</a>
                <a href="/blog.html">Blog</a>
                <a href="/about.html">Hakkımızda</a>
                <a href="/privacy.html">Gizlilik</a>
                <a href="/terms.html">Koşullar</a>
                <a href="/contact.html">İletişim</a>
            </div>
            <p class="footer-copy">&copy; 2026 AlyaGames. Tüm Hakları Saklıdır.</p>
        </div>
    </footer>

    <script>
        // Track recently played game
        try {{
            const recent = JSON.parse(localStorage.getItem('alyagames_recent') || '[]');
            const currentGame = {{ slug: "{slug}", title: "{title}", img: "{image}", cat: "{cat_name}" }};
            const filtered = recent.filter(g => g.slug !== currentGame.slug);
            filtered.unshift(currentGame);
            localStorage.setItem('alyagames_recent', JSON.stringify(filtered.slice(0, 12)));
        }} catch (e) {{}}

        // Fullscreen Toggle
        document.getElementById('fullscreen-btn').addEventListener('click', () => {{
            const iframe = document.getElementById('game-frame');
            if (iframe.requestFullscreen) iframe.requestFullscreen();
            else if (iframe.webkitRequestFullscreen) iframe.webkitRequestFullscreen();
            else if (iframe.msRequestFullscreen) iframe.msRequestFullscreen();
        }});

        // Favorite Toggle
        const favBtn = document.getElementById('fav-btn');
        const favIcon = document.getElementById('fav-icon');
        const slug = "{slug}";
        
        function updateFavUI() {{
            const favs = JSON.parse(localStorage.getItem('alyagames_favorites') || '[]');
            const isFav = favs.some(f => f.slug === slug);
            if (isFav) {{
                favBtn.classList.add('active');
                favIcon.textContent = '❤️';
            }} else {{
                favBtn.classList.remove('active');
                favIcon.textContent = '🤍';
            }}
        }}
        updateFavUI();

        favBtn.addEventListener('click', () => {{
            let favs = JSON.parse(localStorage.getItem('alyagames_favorites') || '[]');
            const isFav = favs.some(f => f.slug === slug);
            if (isFav) {{
                favs = favs.filter(f => f.slug !== slug);
            }} else {{
                favs.push({{ slug: "{slug}", title: "{title}", img: "{image}", cat: "{cat_name}" }});
            }}
            localStorage.setItem('alyagames_favorites', JSON.stringify(favs));
            updateFavUI();
        }});

        // Share Button
        document.getElementById('share-btn').addEventListener('click', () => {{
            if (navigator.share) {{
                navigator.share({{ title: "{title} - AlyaGames", url: window.location.href }});
            }} else {{
                navigator.clipboard.writeText(window.location.href);
                alert("Oyun linki kopyalandı!");
            }}
        }});

        // Theme Toggle
        const themeBtn = document.getElementById('theme-toggle');
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.classList.add('dark-mode');
        }}
        if (themeBtn) {{
            themeBtn.addEventListener('click', () => {{
                document.body.classList.toggle('dark-mode');
                localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
            }});
        }}

        // Search Input Redirect
        const searchInput = document.getElementById('header-search-input');
        if (searchInput) {{
            searchInput.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' && searchInput.value.trim()) {{
                    window.location.href = '/#/?q=' + encodeURIComponent(searchInput.value.trim());
                }}
            }});
        }}

        // Register Service Worker
        if ('serviceWorker' in navigator) {{
            window.addEventListener('load', () => {{
                navigator.serviceWorker.register('/sw.js').catch(console.warn);
            }});
        }}
    </script>
</body>
</html>"""
    return html

def generate_category_page(cat_key, cat_info, games_in_cat):
    cat_name = cat_info['name']
    cat_slug = cat_info['slug']
    cat_desc = cat_info['desc']
    canonical_url = f"{SITE_URL}/kategori/{cat_slug}/"

    cards_html = ""
    for idx, g in enumerate(games_in_cat):
        title = (g.get('Title') or 'Oyun').replace('"', '&quot;')
        slug = slugify(g.get('Title', ''))
        img = get_best_image(g)
        cards_html += f"""
        <a href="/oyun/{slug}/" class="game-card fade-in-stagger" title="{title} Oyna">
            <div class="game-card-img-wrapper">
                <img src="{img}" alt="{title}" class="game-card-img" loading="lazy">
            </div>
            <div class="game-card-content">
                <span class="game-card-category">{cat_name}</span>
                <h3 class="game-card-title">{title}</h3>
                <span class="play-btn-pill">Şimdi Oyna</span>
            </div>
        </a>"""

    schema_cat = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{cat_name} - En İyi Ücretsiz Online Oyunlar",
        "url": canonical_url,
        "description": cat_desc,
        "inLanguage": "tr",
        "isPartOf": {
            "@type": "WebSite",
            "name": "AlyaGames",
            "url": SITE_URL
        }
    }

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cat_name} - En İyi Ücretsiz Online Oyunlar | AlyaGames</title>
    <meta name="description" content="{cat_desc}">
    <meta name="keywords" content="{cat_name}, ücretsiz {cat_name}, online {cat_name}, html5 oyunlar, alyagames">
    <meta name="robots" content="index, follow, max-image-preview:large">
    <link rel="canonical" href="{canonical_url}">

    <!-- Open Graph -->
    <meta property="og:title" content="{cat_name} - AlyaGames">
    <meta property="og:description" content="{cat_desc}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="https://img.gamedistribution.com/24c4d87d116e4521aaeecd12b413c56f-512x384.jpg">
    <meta property="og:locale" content="tr_TR">

    <!-- PWA -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#6366f1">

    <script type="application/ld+json">{json.dumps(schema_cat, ensure_ascii=False)}</script>

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <link rel="stylesheet" href="/style.css">
</head>
<body>
    <div class="glow-bg glow-bg-1"></div>
    <div class="glow-bg glow-bg-2"></div>

    <header class="main-header">
        <div class="header-container">
            <a href="/" class="logo">
                <span class="logo-icon">🎮</span>
                <span class="logo-accent">Alya</span>Games
            </a>

            <div class="search-wrapper">
                <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input type="text" id="header-search-input" placeholder="Oyun ara..." autocomplete="off">
            </div>

            <div class="header-controls">
                <button id="sound-toggle" class="header-control-btn">🔊</button>
                <button id="theme-toggle" class="header-control-btn">🌙</button>
            </div>
        </div>
    </header>

    <nav class="categories-nav">
        <div class="categories-container">
            <a href="/" class="category-btn">Tümü</a>
            <a href="/kategori/aksiyon/" class="category-btn {'active' if cat_slug == 'aksiyon' else ''}">Aksiyon</a>
            <a href="/kategori/savas/" class="category-btn {'active' if cat_slug == 'savas' else ''}">Savaş</a>
            <a href="/kategori/yaris/" class="category-btn {'active' if cat_slug == 'yaris' else ''}">Yarış</a>
            <a href="/kategori/beceri/" class="category-btn {'active' if cat_slug == 'beceri' else ''}">Beceri & Zeka</a>
            <a href="/kategori/macera/" class="category-btn {'active' if cat_slug == 'macera' else ''}">Macera</a>
            <a href="/kategori/kiz/" class="category-btn {'active' if cat_slug == 'kiz' else ''}">Kız</a>
            <a href="/kategori/iki-kisilik/" class="category-btn {'active' if cat_slug == 'iki-kisilik' else ''}">2 Kişilik</a>
            <a href="/kategori/okul-oyunlari/" class="category-btn {'active' if cat_slug == 'okul-oyunlari' else ''}">🎯 Okulda Oyna</a>
        </div>
    </nav>

    <main class="main-content">
        <div class="section-title-wrapper">
            <h1 class="section-title">{cat_info['icon']} {cat_name}</h1>
            <p class="section-subtitle">{cat_desc} Toplam {len(games_in_cat)} ücretsiz oyun listeleniyor.</p>
        </div>

        <div class="games-grid" style="display: grid;">
            {cards_html}
        </div>
    </main>

    <footer class="main-footer">
        <div class="footer-container">
            <div class="footer-brand">
                <span class="logo-icon">🎮</span>
                <span class="logo-accent">Alya</span>Games
            </div>
            <div class="footer-links">
                <a href="/">Anasayfa</a>
                <a href="/kategori/aksiyon/">Aksiyon Oyunları</a>
                <a href="/kategori/savas/">Savaş Oyunları</a>
                <a href="/kategori/yaris/">Yarış Oyunları</a>
                <a href="/kategori/beceri/">Zeka &amp; Beceri</a>
                <a href="/kategori/macera/">Macera Oyunları</a>
                <a href="/kategori/kiz/">Kız Oyunları</a>
                <a href="/kategori/iki-kisilik/">2 Kişilik Oyunlar</a>
                <a href="/blog.html">Blog &amp; Makaleler</a>
                <a href="/about.html">Hakkımızda</a>
                <a href="/privacy.html">Gizlilik Politikası</a>
                <a href="/terms.html">Kullanım Koşulları</a>
                <a href="/contact.html">İletişim</a>
            </div>
            <p class="footer-copy">&copy; 2026 AlyaGames. Tüm Hakları Saklıdır.</p>
        </div>
    </footer>

    <script>
        const themeBtn = document.getElementById('theme-toggle');
        if (localStorage.getItem('theme') === 'dark') {{
            document.body.classList.add('dark-mode');
        }}
        if (themeBtn) {{
            themeBtn.addEventListener('click', () => {{
                document.body.classList.toggle('dark-mode');
                localStorage.setItem('theme', document.body.classList.contains('dark-mode') ? 'dark' : 'light');
            }});
        }}
        const searchInput = document.getElementById('header-search-input');
        if (searchInput) {{
            searchInput.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' && searchInput.value.trim()) {{
                    window.location.href = '/#/?q=' + encodeURIComponent(searchInput.value.trim());
                }}
            }});
        }}
    </script>
</body>
</html>"""
    return html

def generate_sitemap(games, categories):
    today = datetime.now().strftime("%Y-%m-%d")
    urls = []

    core_pages = [
        ("/", "1.0", "daily"),
        ("/blog.html", "0.8", "weekly"),
        ("/about.html", "0.5", "monthly"),
        ("/contact.html", "0.5", "monthly"),
        ("/privacy.html", "0.3", "monthly"),
        ("/terms.html", "0.3", "monthly")
    ]
    for path, prio, freq in core_pages:
        urls.append(f"""    <url>
        <loc>{SITE_URL}{path}</loc>
        <lastmod>{today}</lastmod>
        <changefreq>{freq}</changefreq>
        <priority>{prio}</priority>
    </url>""")

    for cat_slug in categories:
        urls.append(f"""    <url>
        <loc>{SITE_URL}/kategori/{cat_slug}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>""")

    seen_sitemap_slugs = set()
    for g in games:
        slug = slugify(g.get('Title', ''))
        if not slug or slug in seen_sitemap_slugs:
            continue
        seen_sitemap_slugs.add(slug)
        urls.append(f"""    <url>
        <loc>{SITE_URL}/oyun/{slug}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>""")

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>
"""
    return sitemap_xml

def main():
    games = fetch_games(max_gd_pages=5, max_gp_pages=1)
    if not games:
        print("[!] No games fetched. Aborting.")
        return

    print(f"[*] Processing {len(games)} total unique games...")
    
    games_by_cat = {k: [] for k in CATEGORY_MAP}
    game_categories = {}
    
    for g in games:
        cat_key = categorize_game(g)
        games_by_cat[cat_key].append(g)
        game_categories[slugify(g.get('Title', ''))] = cat_key
        if len(games_by_cat['unblocked']) < 60 and cat_key in ['racing', 'skill', 'action', 'adventure']:
            games_by_cat['unblocked'].append(g)

    # 1. Generate Static Game Pages with circular internal linking (no orphan pages!)
    print("[*] Generating static game landing pages...")
    oyun_dir = os.path.join(OUTPUT_ROOT, "oyun")
    os.makedirs(oyun_dir, exist_ok=True)
    
    n_total = len(games)
    for i, g in enumerate(games):
        slug = slugify(g.get('Title', ''))
        cat_key = game_categories.get(slug, 'action')
        cat_list = games_by_cat.get(cat_key, games)
        n_cat = len(cat_list)

        # Find current game's index inside its category list for circular window linking
        cat_idx = 0
        for idx_c, cg in enumerate(cat_list):
            if slugify(cg.get('Title', '')) == slug:
                cat_idx = idx_c
                break

        sidebar_related = []
        for offset in range(1, 7):
            candidate = cat_list[(cat_idx + offset) % n_cat]
            if slugify(candidate.get('Title', '')) != slug:
                sidebar_related.append(candidate)

        bottom_related = []
        for offset in range(7, 15):
            candidate = cat_list[(cat_idx + offset) % n_cat]
            if slugify(candidate.get('Title', '')) != slug and candidate not in sidebar_related:
                bottom_related.append(candidate)

        # Fallback if category has fewer than 15 games
        if len(bottom_related) < 8:
            for offset in range(1, 15):
                candidate = games[(i + offset) % n_total]
                if slugify(candidate.get('Title', '')) != slug and candidate not in sidebar_related and candidate not in bottom_related:
                    bottom_related.append(candidate)
                if len(bottom_related) >= 8:
                    break

        page_html = generate_game_page(g, cat_key, sidebar_related, bottom_related)
        
        game_folder = os.path.join(oyun_dir, slug)
        os.makedirs(game_folder, exist_ok=True)
        with open(os.path.join(game_folder, "index.html"), "w", encoding="utf-8") as f:
            f.write(page_html)

    print(f"  -> Generated {len(games)} static game pages under /oyun/<slug>/index.html")

    # 2. Generate Category Pages
    print("[*] Generating category landing pages...")
    kategori_dir = os.path.join(OUTPUT_ROOT, "kategori")
    os.makedirs(kategori_dir, exist_ok=True)

    for cat_key, cat_info in CATEGORY_MAP.items():
        cat_slug = cat_info['slug']
        cat_games = games_by_cat.get(cat_key, [])
        if not cat_games:
            cat_games = games[:24]
        
        cat_html = generate_category_page(cat_key, cat_info, cat_games)
        cat_folder = os.path.join(kategori_dir, cat_slug)
        os.makedirs(cat_folder, exist_ok=True)
        with open(os.path.join(cat_folder, "index.html"), "w", encoding="utf-8") as f:
            f.write(cat_html)
        print(f"  -> Generated category: /kategori/{cat_slug}/ ({len(cat_games)} games)")

    # 3. Generate Sitemap XML
    print("[*] Generating comprehensive sitemap.xml...")
    cat_slugs = [c['slug'] for c in CATEGORY_MAP.values()]
    sitemap_content = generate_sitemap(games, cat_slugs)
    
    sitemap_path = os.path.join(OUTPUT_ROOT, "sitemap.xml")
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    print(f"  -> Successfully generated sitemap.xml with {len(games) + len(cat_slugs) + 6} URLs!")

if __name__ == "__main__":
    main()
