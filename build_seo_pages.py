"""
AlyaGames - Static SEO Page & Sitemap Generator
Fetches catalog games from GameDistribution and generates:
1. Static SEO Landing Pages for each game (/oyun/<slug>/index.html)
2. Static SEO Category Landing Pages (/kategori/<category>/index.html)
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
    text = text.lower().strip()
    text = text.replace('&', '-and-')
    text = text.replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ş', 's').replace('ö', 'o').replace('ç', 'c')
    text = re.sub(r'[\s\W-]+', '-', text)
    text = text.strip('-')
    return text or 'oyun'

def fetch_games(max_pages=5):
    all_games = []
    seen_titles = set()
    print(f"[*] Fetching games from GameDistribution API (pages 1 to {max_pages})...")
    
    for page in range(1, max_pages + 1):
        url = f"https://catalog.api.gamedistribution.com/api/v2.0/rss/All/?collection=All&amount=100&page={page}&format=json"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                items = data if isinstance(data, list) else data.get('items', [])
                for g in items:
                    title = g.get('Title', '').strip()
                    if title and title not in seen_titles and g.get('Url'):
                        seen_titles.add(title)
                        all_games.append(g)
            print(f"  -> Page {page}: fetched {len(items)} games (Total unique: {len(all_games)})")
        except Exception as e:
            print(f"  [!] Error fetching page {page}: {e}")
            
    return all_games

CATEGORY_MAP = {
    'action': {'name': 'Aksiyon Oyunları', 'slug': 'aksiyon', 'icon': '⚔️', 'desc': 'En heyecanlı aksiyon, dövüş ve süper kahraman oyunlarını ücretsiz, indirmeden tarayıcınızda online oynayın.'},
    'war': {'name': 'Savaş ve Silah Oyunları', 'slug': 'savas', 'icon': '🔫', 'desc': 'Ücretsiz FPS nişancı, ordu, sniper ve taktiksel savaş oyunları ile düşmanları alt edin.'},
    'racing': {'name': 'Araba ve Yarış Oyunları', 'slug': 'yaris', 'icon': '🏎️', 'desc': 'Hızlı spor arabalar, drift yarışları, motosiklet ve zorlu pistlerde direksiyon başına geçin.'},
    'skill': {'name': 'Zeka ve Beceri Oyunları', 'slug': 'beceri', 'icon': '🧩', 'desc': 'Mantık bulmacaları, tetris benzeri blok oyunları ve zihninizi geliştirecek zeka oyunları.'},
    'adventure': {'name': 'Macera Oyunları', 'slug': 'macera', 'icon': '🗺️', 'desc': 'Gizemli dünyaları keşfedin, platform engellerini aşın ve unutulmaz maceralara atılın.'},
    'girls': {'name': 'Kız Oyunları', 'slug': 'kiz', 'icon': '🎀', 'desc': 'Moda tasarım, makyaj, prenses giydirmece ve sevimli yemek pişirme simülasyonları.'},
    'multiplayer': {'name': 'İki Kişilik Oyunlar', 'slug': 'iki-kisilik', 'icon': '👥', 'desc': 'Aynı klavyede veya online arkadaşınızla birlikte oynayabileceğiniz en iyi 2 kişilik oyunlar.'},
    'unblocked': {'name': 'Okul Oyunları (Engelsiz)', 'slug': 'okul-oyunlari', 'icon': '🎯', 'desc': 'Okulda ve her ağda kısıtlama olmadan açılan en popüler Unblocked HTML5 oyunları.'}
}

def categorize_game(game):
    cats = [c.lower() for c in game.get('Category', [])]
    tags = [t.lower() for t in game.get('Tag', [])]
    combined = " ".join(cats + tags + [game.get('Title', '').lower()])
    
    if any(k in combined for k in ['2-player', 'multiplayer', '2player', 'pvp', 'co-op', 'coop', 'two player']):
        return 'multiplayer'
    if any(k in combined for k in ['girl', 'dress', 'makeup', 'fashion', 'cooking', 'doll', 'princess', 'makeover', 'beauty']):
        return 'girls'
    if any(k in combined for k in ['racing', 'driving', 'car', 'moto', 'bike', 'drift', 'truck', 'parking', 'speed']):
        return 'racing'
    if any(k in combined for k in ['shooter', 'shooting', 'sniper', 'gun', 'war', 'battle', 'fps', 'tank', 'army']):
        return 'war'
    if any(k in combined for k in ['action', 'fight', 'stickman', 'superhero', 'zombie', 'ninja', 'combat']):
        return 'action'
    if any(k in combined for k in ['puzzle', 'skill', 'match-3', 'math', 'logic', 'block', 'tetris', 'educational', 'quiz', 'brain']):
        return 'skill'
    if any(k in combined for k in ['adventure', 'escape', 'runner', 'platformer', 'quest', 'rpg', 'jump']):
        return 'adventure'
    
    # Default fallback
    return 'action'

def get_best_image(game):
    assets = game.get('Asset', [])
    if not assets:
        return "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=600"
    for url in assets:
        if '512x384' in url or '512x512' in url:
            return url
    return assets[0]

def generate_game_page(game, cat_key, related_games):
    title = game.get('Title', '').replace('"', '&quot;')
    slug = slugify(game.get('Title', ''))
    raw_desc = (game.get('Description') or f"{title} oyununu AlyaGames ile hemen ücretsiz ve indirmeden tarayıcında oyna. En popüler HTML5 oyunları burada!").strip()
    clean_desc = re.sub(r'\s+', ' ', raw_desc).replace('"', '&quot;')
    instructions = (game.get('Instructions') or "Oyunu fare, dokunmatik ekran veya klavye yön tuşları (WASD / Ok Tuşları) ile kolayca yönlendirebilirsiniz.").strip()
    image = get_best_image(game)
    url = game.get('Url', '')
    
    cat_info = CATEGORY_MAP.get(cat_key, CATEGORY_MAP['action'])
    cat_name = cat_info['name']
    cat_slug = cat_info['slug']
    canonical_url = f"{SITE_URL}/oyun/{slug}/"

    # Schema JSON-LD Data
    schema_video_game = {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": title,
        "url": canonical_url,
        "image": image,
        "description": clean_desc[:250],
        "inLanguage": "tr",
        "genre": [cat_name, "HTML5 Game", "Online Game"],
        "playMode": "SinglePlayer" if cat_key != 'multiplayer' else "MultiPlayer",
        "applicationCategory": "Game",
        "operatingSystem": "Web Browser, Windows, MacOS, Android, iOS",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.8",
            "bestRating": "5",
            "worstRating": "1",
            "ratingCount": "142"
        },
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD",
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
                "name": title,
                "item": canonical_url
            }
        ]
    }

    schema_faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"{title} oyunu ücretsiz mi?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Evet, {title} AlyaGames platformunda tamamen ücretsizdir. Herhangi bir indirme, kayıt veya abonelik gerekmeden doğrudan web tarayıcınızdan oynayabilirsiniz."
                }
            },
            {
                "@type": "Question",
                "name": f"{title} nasıl oynanır ve kontrolleri nelerdir?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"{instructions}"
                }
            },
            {
                "@type": "Question",
                "name": f"{title} telefonda ve tablette çalışır mı?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Evet! {title} HTML5 ve WebGL teknolojisi sayesinde Android telefonlar, iPhone ve iPad gibi tüm dokunmatik cihazlarda kesintisiz çalışır."
                }
            }
        ]
    }

    # Related games HTML
    related_html = ""
    for rg in related_games[:6]:
        r_title = rg.get('Title', '').replace('"', '&quot;')
        r_slug = slugify(rg.get('Title', ''))
        r_img = get_best_image(rg)
        r_cat = rg.get('Category', ['Oyun'])[0] if rg.get('Category') else 'Oyun'
        related_html += f"""
        <a href="/oyun/{r_slug}/" class="game-card" title="{r_title} Oyna">
            <div class="game-card-img-wrapper">
                <img src="{r_img}" alt="{r_title}" class="game-card-img" loading="lazy">
            </div>
            <div class="game-card-content">
                <span class="game-card-category">{r_cat}</span>
                <h3 class="game-card-title">{r_title}</h3>
                <span class="play-btn-pill">Oyna</span>
            </div>
        </a>"""

    html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} Oyunu Oyna - Ücretsiz Online | AlyaGames</title>
    <meta name="description" content="{clean_desc[:160]}">
    <meta name="keywords" content="{title}, {title} oyna, {title} oyunu, {cat_name}, ücretsiz online oyunlar, html5 oyunlar">
    <link rel="canonical" href="{canonical_url}">

    <!-- Open Graph SEO Metadata -->
    <meta property="og:title" content="{title} Oyunu Oyna - AlyaGames">
    <meta property="og:description" content="{clean_desc[:160]}">
    <meta property="og:type" content="game">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="{image}">
    <meta property="og:site_name" content="AlyaGames">

    <!-- Twitter Cards -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title} Oyunu Oyna - AlyaGames">
    <meta name="twitter:description" content="{clean_desc[:160]}">
    <meta name="twitter:image" content="{image}">

    <!-- PWA & Mobile Web App -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#6366f1">
    <link rel="apple-touch-icon" href="{image}">

    <!-- Structured Data JSON-LD -->
    <script type="application/ld+json">{json.dumps(schema_video_game)}</script>
    <script type="application/ld+json">{json.dumps(schema_breadcrumbs)}</script>
    <script type="application/ld+json">{json.dumps(schema_faq)}</script>

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
                    <iframe id="game-frame" src="{url}" frameborder="0" allowfullscreen allow="autoplay; gamepad; fullscreen"></iframe>
                </div>

                <div class="game-info-card">
                    <!-- Rating Widget -->
                    <div class="rating-box">
                        <div>
                            <strong>Oyuncu Puanı:</strong>
                            <div class="star-rating" id="star-rating" title="Puan Ver">★★★★★</div>
                        </div>
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">
                            <span id="rating-val">4.8</span> / 5 (142+ değerlendirme)
                        </div>
                    </div>

                    <h2>📖 {title} Hakkında</h2>
                    <p>{raw_desc}</p>

                    <h2>🕹️ Nasıl Oynanır ve Kontroller</h2>
                    <p>{instructions}</p>

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
                {related_html}
            </div>
        </aside>
    </main>

    <!-- Footer -->
    <footer class="main-footer">
        <div class="footer-container">
            <div class="footer-brand">
                <span class="logo-icon">🎮</span>
                <span class="logo-accent">Alya</span>Games
            </div>
            <div class="footer-links">
                <a href="/">Anasayfa</a>
                <a href="/blog.html">Blog & Makaleler</a>
                <a href="/about.html">Hakkımızda</a>
                <a href="/privacy.html">Gizlilik Politikası</a>
                <a href="/terms.html">Kullanım Koşulları</a>
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
        title = g.get('Title', '').replace('"', '&quot;')
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
    <link rel="canonical" href="{canonical_url}">

    <!-- Open Graph -->
    <meta property="og:title" content="{cat_name} - AlyaGames">
    <meta property="og:description" content="{cat_desc}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="{canonical_url}">
    <meta property="og:image" content="https://img.gamedistribution.com/24c4d87d116e4521aaeecd12b413c56f-512x384.jpg">

    <!-- PWA -->
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#6366f1">

    <script type="application/ld+json">{json.dumps(schema_cat)}</script>

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
            <p class="section-subtitle">{cat_desc}</p>
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
                <a href="/blog.html">Blog & Makaleler</a>
                <a href="/about.html">Hakkımızda</a>
                <a href="/privacy.html">Gizlilik Politikası</a>
                <a href="/terms.html">Kullanım Koşulları</a>
                <a href="/contact.html">İletişim</a>
            </div>
            <p class="footer-copy">&copy; 2026 AlyaGames. Tüm Hakları Saklıdır.</p>
        </div>
    </footer>

    <script src="/script.js"></script>
</body>
</html>"""
    return html

def generate_sitemap(games, categories):
    today = datetime.now().strftime("%Y-%m-%d")
    urls = []

    # Main core pages
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

    # Category pages
    for cat_slug in categories:
        urls.append(f"""    <url>
        <loc>{SITE_URL}/kategori/{cat_slug}/</loc>
        <lastmod>{today}</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.9</priority>
    </url>""")

    # Game pages
    for g in games:
        slug = slugify(g.get('Title', ''))
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
    games = fetch_games(max_pages=5)
    if not games:
        print("[!] No games fetched. Aborting.")
        return

    print(f"[*] Processing {len(games)} games...")
    
    # Categorize games
    games_by_cat = {k: [] for k in CATEGORY_MAP}
    game_categories = {}
    
    for g in games:
        cat_key = categorize_game(g)
        games_by_cat[cat_key].append(g)
        game_categories[g.get('Title')] = cat_key
        # Also add fun games to unblocked / okul
        if len(games_by_cat['unblocked']) < 40 and cat_key in ['racing', 'skill', 'action', 'adventure']:
            games_by_cat['unblocked'].append(g)

    # 1. Generate Static Game Pages
    print("[*] Generating static game landing pages...")
    oyun_dir = os.path.join(OUTPUT_ROOT, "oyun")
    os.makedirs(oyun_dir, exist_ok=True)
    
    for i, g in enumerate(games):
        slug = slugify(g.get('Title', ''))
        cat_key = game_categories.get(g.get('Title'), 'action')
        
        # Pick related games from same category
        related = [rg for rg in games_by_cat[cat_key] if rg.get('Title') != g.get('Title')]
        if len(related) < 6:
            related += [rg for rg in games if rg.get('Title') != g.get('Title')]
        
        page_html = generate_game_page(g, cat_key, related)
        
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
