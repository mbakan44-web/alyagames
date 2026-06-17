/**
 * FUNNIESPLAY - JAVASCRIPT CONTROLLER
 * Dynamic game portal populator, filter engine, and modal controller.
 * Powered by GameDistribution API.
 */

// API Feed URL for the top 20 games in JSON format
const GAME_API_URL = 'https://catalog.api.gamedistribution.com/api/v2.0/rss/All/?collection=All&amount=20&page=1&format=json';

// Global state variables
let gamesData = [];
let activeCategory = 'all';
let searchQuery = '';
let currentPage = 1;
let isLoadingMore = false;
let pendingGameToOpen = null;
let dynamicCategoryName = '';

// Helper to create clean URL slug from title strings
function slugify(text) {
    return text.toString().toLowerCase().trim()
        .replace(/&/g, '-and-')
        .replace(/[\s\W-]+/g, '-')
        .replace(/-$/, '')
        .replace(/^-/, '');
}

// High-quality local fallback data to ensure the portal is fully operational
// in case of CORS restrictions, offline use, or API downtime.
const FALLBACK_GAMES = [
    {
        Title: "Scrap Car Merge",
        Url: "https://html5.gamedistribution.com/6c04e97ae6eb4a098dc22c63471d1925/",
        Asset: ["https://img.gamedistribution.com/6c04e97ae6eb4a098dc22c63471d1925-512x384.jpg"],
        Category: ["Shooter", "Casual"],
        Description: "Scrap Car Merge is a fast arcade game about driving, shooting, and upgrading your own battle car. Drive forward through a dangerous road, shoot enemies, survive attacks, and reach the end of each level.",
        Instructions: "Use Arrow keys or Mouse drag to move and shoot enemies on the road. Upgrade your car with rewards after each run."
    },
    {
        Title: "Arrowtix - Train Your Brain",
        Url: "https://html5.gamedistribution.com/9afeb29876304d269c28d8ca7869b714/",
        Asset: ["https://img.gamedistribution.com/9afeb29876304d269c28d8ca7869b714-512x384.jpg"],
        Category: ["Puzzle"],
        Description: "Arrowtix is a satisfying, brain-teasing puzzle game where your goal is to clear the board by sliding tangled arrows out of the grid.",
        Instructions: "Study the arrows. Click only those with an unobstructed path in the direction they point."
    },
    {
        Title: "Math Stars Space Expedition",
        Url: "https://html5.gamedistribution.com/e7e5bb0e6caf47b5965d813736921e76/",
        Asset: ["https://img.gamedistribution.com/e7e5bb0e6caf47b5965d813736921e76-512x384.jpg"],
        Category: ["Educational", "Skill"],
        Description: "Travel through the galaxy, visit beautiful planets, and defeat space bosses by solving addition and subtraction problems!",
        Instructions: "Tap Play to start. Answer math questions by tapping the correct crystal before time runs out."
    },
    {
        Title: "Blocks and That's It",
        Url: "https://html5.gamedistribution.com/940b8ad7c3784a00be88bedaf0eae0af/",
        Asset: ["https://img.gamedistribution.com/940b8ad7c3784a00be88bedaf0eae0af-512x384.jpg"],
        Category: ["Puzzle"],
        Description: "Welcome to Blocks and That's It - an addictive Tetris-style puzzle! Drag and drop blocks onto an 8x8 grid, clear lines, and trigger combos.",
        Instructions: "Drag and drop the block pieces onto the grid. Fill horizontal or vertical rows to clear them and score."
    },
    {
        Title: "Worm Puzzle Snake Apple",
        Url: "https://html5.gamedistribution.com/7e5efdcdc8d84b2291c0febe8de5e638/",
        Asset: ["https://img.gamedistribution.com/7e5efdcdc8d84b2291c0febe8de5e638-512x384.jpg"],
        Category: ["Adventure", "Puzzle"],
        Description: "Worm Puzzle: Snake Apple combines classic snake gameplay with creative puzzle challenges. Solve spatial problems and guide snakes.",
        Instructions: "PC: Arrow keys to move snake. Mobile: Click the on-screen arrows to direct the snake."
    },
    {
        Title: "Sniper Mission",
        Url: "https://html5.gamedistribution.com/d8328c704f05470588667634f37803e4/",
        Asset: ["https://img.gamedistribution.com/d8328c704f05470588667634f37803e4-512x384.jpg"],
        Category: ["Shooter", "Action"],
        Description: "Eliminate targets from high structures, complete missions, and upgrade your sniper rifle to stay ahead of the enemy.",
        Instructions: "Drag to aim, release or tap button to shoot. Upgrade scope and stability."
    },
    {
        Title: "Hill Climb Racing Challenge",
        Url: "https://html5.gamedistribution.com/4a8697621ef04928b5774a3821034c44/",
        Asset: ["https://img.gamedistribution.com/4a8697621ef04928b5774a3821034c44-512x384.jpg"],
        Category: ["Racing", "Driving"],
        Description: "Drive up steep mountains, collect coins, and perform flips while managing your fuel levels carefully.",
        Instructions: "Use Right Arrow/D to accelerate and Left Arrow/A to brake/balance in air."
    },
    {
        Title: "Speedy Moto Rider",
        Url: "https://html5.gamedistribution.com/39328c704f05470588667634f37803f2/",
        Asset: ["https://img.gamedistribution.com/39328c704f05470588667634f37803f2-512x384.jpg"],
        Category: ["Racing"],
        Description: "Speed through heavy highway traffic on custom racing motorbikes. Get close to other cars for speed multipliers.",
        Instructions: "Use WASD or Arrow Keys to steer. Use Space for Nitrous booster."
    },
    {
        Title: "Temple Escape Run",
        Url: "https://html5.gamedistribution.com/f8328c704f05470588667634f37803a1/",
        Asset: ["https://img.gamedistribution.com/f8328c704f05470588667634f37803a1-512x384.jpg"],
        Category: ["Adventure"],
        Description: "Dash, slide, and jump over hazardous ruins while escaping from the giant guardian beast.",
        Instructions: "Swipe or use WASD/Arrows to jump, slide, and turn corners."
    },
    {
        Title: "Neon Ball Smash",
        Url: "https://html5.gamedistribution.com/97828c704f05470588667634f37803a8/",
        Asset: ["https://img.gamedistribution.com/97828c704f05470588667634f37803a8-512x384.jpg"],
        Category: ["Skill", "Arcade"],
        Description: "Bounce and smash tiles matching your ball color. Watch out for obstacles and trigger powerful streak multipliers.",
        Instructions: "Move mouse or drag finger to control platform position."
    }
];

// Document Elements
const gamesContainer = document.getElementById('games-container');
const mainLoader = document.getElementById('main-loader');
const noResultsMsg = document.getElementById('no-results-msg');
const searchInput = document.getElementById('search-input');
const clearSearchBtn = document.getElementById('clear-search');
const categoryButtons = document.querySelectorAll('.category-btn');
const displayTitle = document.getElementById('display-title');
const logoBtn = document.getElementById('logo-btn');
const loadMoreContainer = document.getElementById('load-more-container');
const loadMoreBtn = document.getElementById('load-more-btn');

// Homepage Sections Elements
const homepageSections = document.getElementById('homepage-sections');
const editorsChoiceGrid = document.getElementById('editors-choice-grid');
const popularGamesGrid = document.getElementById('popular-games-grid');
const newGamesGrid = document.getElementById('new-games-grid');
const warGamesGrid = document.getElementById('war-games-grid');
const racingGamesGrid = document.getElementById('racing-games-grid');
const girlsGamesGrid = document.getElementById('girls-games-grid');
const skillGamesGrid = document.getElementById('skill-games-grid');

// Modal Elements
const gameModal = document.getElementById('game-modal');
const gameIframe = document.getElementById('game-iframe');
const modalGameTitle = document.getElementById('modal-game-title');
const modalGameDescription = document.getElementById('modal-game-description');
const modalGameInstructions = document.getElementById('modal-game-instructions');
const closeModelBtn = document.getElementById('close-modal-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');
const iframeLoader = document.getElementById('iframe-loader');
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// SEO Configuration Map for Categories
const SEO_CONFIG = {
    all: {
        title: "AlyaGames | En İyi Ücretsiz Online HTML5 Oyunları Oyna",
        description: "En popüler ve yeni aksiyon, yarış, kız ve beceri oyunlarını ücretsiz, indirmeden tarayıcınızda oynayın. Oyunskor tarzı modern HTML5 oyun portalı.",
        keywords: "oyun oyna, ücretsiz oyunlar, online oyunlar, html5 oyunları, oyunskor"
    },
    action: {
        title: "Aksiyon Oyunları - En Heyecanlı Aksiyon Oyunları Oyna | AlyaGames",
        description: "En yeni aksiyon, dövüş ve macera oyunlarını ücretsiz oynayın. Tarayıcınızda hemen oyna butonuna basarak heyecana katılın.",
        keywords: "aksiyon oyunları, dövüş oyunları, macera oyunları, online aksiyon"
    },
    war: {
        title: "Savaş Oyunları - En Popüler Savaş ve Silah Oyunları | AlyaGames",
        description: "Ücretsiz silah, nişancı, strateji ve askeri savaş oyunlarını keşfedin. Ordunuzu kurun ve savaşa başlayın.",
        keywords: "savaş oyunları, silah oyunları, nişancı oyunları, sniper oyunları"
    },
    racing: {
        title: "Araba ve Yarış Oyunları - Hızlı Yarış Oyunları Oyna | AlyaGames",
        description: "En çılgın araba yarışları, motor oyunları ve simülasyonları ücretsiz oynayın. Direksiyon başına geçin ve hız yapın.",
        keywords: "araba yarışları, yarış oyunları, motor yarışları, drift oyunları"
    },
    skill: {
        title: "Beceri ve Zeka Oyunları - Zeka Geliştirici Oyunlar | AlyaGames",
        description: "Zihninizi zorlayacak en iyi bulmaca, beceri, klasik tetris ve zeka oyunlarını ücretsiz oynayın.",
        keywords: "beceri oyunları, zeka oyunları, bulmaca oyunları, yapboz oyunları"
    },
    adventure: {
        title: "Macera Oyunları - En İyi Keşif ve RPG Oyunları | AlyaGames",
        description: "Bilinmeyen dünyaları keşfedin, engelleri aşın. En eğlenceli platform ve macera oyunları sizi bekliyor.",
        keywords: "macera oyunları, rpg oyunları, platform oyunları, keşif oyunları"
    },
    girls: {
        title: "Kız Oyunları - Giydirme, Makyaj ve Yemek Oyunları | AlyaGames",
        description: "En güzel kız oyunları, bebek giydirmece, prenses makyajı ve mutfak yemek oyunları ücretsiz olarak burada.",
        keywords: "kız oyunları, giydirme oyunları, makyaj oyunları, yemek yapma"
    },
    multiplayer: {
        title: "İki Kişilik Oyunlar - Arkadaşınla Birlikte Oyna | AlyaGames",
        description: "Aynı ekranda veya online olarak arkadaşınızla oynayabileceğiniz en popüler 2 kişilik oyunları keşfedin.",
        keywords: "iki kişilik oyunlar, 2 kişilik oyunlar, multiplayer oyunlar, pvp oyunlar"
    }
};

// Initialize portal content
window.addEventListener('DOMContentLoaded', () => {
    fetchGamesList(1);
    setupEventListeners();
    handleRouteChange(); // Trigger initial routing on page load
});

// Watch route changes
window.addEventListener('hashchange', handleRouteChange);

// Route Handler
function handleRouteChange() {
    const hash = window.location.hash || '#/';
    
    // 1. Direct Game Route (e.g. #/oyun/scrap-car-merge)
    if (hash.startsWith('#/oyun/')) {
        const gameIdentifier = hash.substring(7); // Get md5 or title slug
        
        if (gamesData.length > 0) {
            // Find game matching title slug or MD5 hash
            const game = gamesData.find(g => slugify(g.Title) === gameIdentifier || g.Md5 === gameIdentifier);
            if (game) {
                openGame(game, false); // Open the game modal without resetting hash
                return;
            }
        }
        
        // If games are not loaded yet, save reference to open on finish loading
        pendingGameToOpen = gameIdentifier;
        return;
    }

    // Close modal if route is not an play route
    if (gameModal.classList.contains('active')) {
        closeModal(false); // Close modal without changing hash (since hash is already changed)
    }

    // 2. Dynamic Category Route (e.g. #/kategori/sports)
    if (hash.startsWith('#/kategori/')) {
        const categoryParam = hash.substring(11).toLowerCase();
        activeCategory = 'dynamic';
        dynamicCategoryName = categoryParam;
        
        // Remove active state from standard buttons
        categoryButtons.forEach(btn => btn.classList.remove('active'));
        
        // Capitalize category title
        const capitalized = categoryParam.charAt(0).toUpperCase() + categoryParam.slice(1);
        displayTitle.textContent = `${capitalized} Oyunları`;
        
        // SEO update
        updateSEOTags('dynamic', capitalized);
        applyFilters();
        return;
    }

    // 3. Standard Main Categories Route
    let routeCategory = 'all';
    if (hash.startsWith('#/')) {
        const path = hash.substring(2);
        const map = {
            'aksiyon': 'action',
            'savas': 'war',
            'yaris': 'racing',
            'beceri': 'skill',
            'macera': 'adventure',
            'kiz': 'girls',
            'iki-kisilik': 'multiplayer'
        };
        routeCategory = map[path] || 'all';
    }

    activeCategory = routeCategory;

    // Update active category menu badge
    categoryButtons.forEach(btn => {
        if (btn.getAttribute('data-category') === activeCategory) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update Display Title
    const activeBtn = document.querySelector(`.category-btn[data-category="${activeCategory}"]`);
    const catName = activeBtn ? activeBtn.textContent.trim() : 'Popüler';
    displayTitle.textContent = activeCategory === 'all' ? 'Popüler Oyunlar' : `${catName} Oyunları`;

    // Apply SEO dynamic tags update
    updateSEOTags(activeCategory);

    // Apply Filter & Render
    applyFilters();
}

// Dynamically Update Page SEO Meta Tags and JSON-LD Structured Data
function updateSEOTags(categoryKey, customName = '') {
    let config = SEO_CONFIG[categoryKey];
    
    if (categoryKey === 'dynamic') {
        config = {
            title: `${customName} Oyunları - En Popüler ${customName} Oyunları Oyna | AlyaGames`,
            description: `En çok oynanan ücretsiz ${customName} oyunlarını keşfedin. Tarayıcınızda ${customName} oyunlarını indirmeden hemen oynayın.`,
            keywords: `${customName} oyunları, ücretsiz ${customName}, online ${customName}`
        };
    } else if (categoryKey === 'game') {
        config = {
            title: `${customName} Oyunu - Şimdi Ücretsiz Oyna | AlyaGames`,
            description: `${customName} oyununu AlyaGames ile tarayıcınızda online ve ücretsiz oynayın. Oyun detayları ve tuş takımı açıklaması.`,
            keywords: `${customName} oyna, ücretsiz ${customName}, html5 ${customName}`
        };
    }
    
    if (!config) config = SEO_CONFIG.all;
    
    // Update Title & Meta Tags
    document.title = config.title;
    document.getElementById('meta-title').textContent = config.title;
    document.getElementById('meta-description').setAttribute('content', config.description);
    
    // Update Open Graph (Social) Tags
    const ogTitle = document.getElementById('og-title');
    const ogDesc = document.getElementById('og-description');
    const ogUrl = document.getElementById('og-url');
    
    if (ogTitle) ogTitle.setAttribute('content', config.title);
    if (ogDesc) ogDesc.setAttribute('content', config.description);
    if (ogUrl) ogUrl.setAttribute('content', window.location.href);

    // Update JSON-LD Schema structured data
    const schemaScript = document.getElementById('seo-schema');
    if (schemaScript) {
        const schema = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "AlyaGames",
            "url": window.location.href,
            "description": config.description,
            "genre": categoryKey !== 'all' ? (customName || categoryKey) : "Gaming Portal",
            "potentialAction": {
                "@type": "SearchAction",
                "target": `${window.location.origin}${window.location.pathname}?q={search_term_string}`,
                "query-input": "required name=search_term_string"
            }
        };
        schemaScript.textContent = JSON.stringify(schema, null, 2);
    }
}

// Setup application event handlers
function setupEventListeners() {
    // Search input handler
    searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase().trim();
        clearSearchBtn.style.display = searchQuery.length > 0 ? 'block' : 'none';
        applyFilters();
    });

    // Clear search button handler
    clearSearchBtn.addEventListener('click', () => {
        searchInput.value = '';
        searchQuery = '';
        clearSearchBtn.style.display = 'none';
        searchInput.focus();
        applyFilters();
    });

    // Category button filters (trigger Hash Change)
    categoryButtons.forEach(button => {
        button.addEventListener('click', () => {
            const cat = button.getAttribute('data-category');
            const map = {
                'all': '',
                'action': 'aksiyon',
                'war': 'savas',
                'racing': 'yaris',
                'skill': 'beceri',
                'adventure': 'macera',
                'girls': 'kiz',
                'multiplayer': 'iki-kisilik'
            };
            window.location.hash = map[cat] ? `#/${map[cat]}` : '#/';
        });
    });

    // Logo click returns to all category and resets search
    logoBtn.addEventListener('click', (e) => {
        e.preventDefault();
        searchInput.value = '';
        searchQuery = '';
        clearSearchBtn.style.display = 'none';
        window.location.hash = '#/';
    });

    // Load More click handler
    loadMoreBtn.addEventListener('click', () => {
        if (!isLoadingMore) {
            currentPage++;
            fetchGamesList(currentPage);
        }
    });

    // Modal Close
    closeModelBtn.addEventListener('click', closeModal);
    gameModal.addEventListener('click', (e) => {
        if (e.target === gameModal) closeModal();
    });

    // Modal Fullscreen
    fullscreenBtn.addEventListener('click', toggleFullscreen);

    // Modal tab navigation
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            button.classList.add('active');
            const targetTab = button.getAttribute('data-tab');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
        });
    });

    // Iframe load complete
    gameIframe.addEventListener('load', () => {
        iframeLoader.style.opacity = '0';
        setTimeout(() => {
            iframeLoader.style.display = 'none';
        }, 300);
    });

    // Surprise Game FAB Listener
    const surpriseFab = document.getElementById('surprise-fab');
    if (surpriseFab) {
        surpriseFab.addEventListener('click', () => {
            if (gamesData.length > 0) {
                const icon = surpriseFab.querySelector('.surprise-icon');
                if (icon) {
                    icon.style.animation = 'none';
                    void icon.offsetWidth; // Trigger reflow
                    icon.style.animation = 'rotateIcon 0.8s ease-out';
                }
                const randomIndex = Math.floor(Math.random() * gamesData.length);
                const game = gamesData[randomIndex];
                setTimeout(() => {
                    openGame(game);
                }, 400);
            }
        });
    }
}


// Fetch popular games list from GameDistribution JSON API
async function fetchGamesList(page) {
    isLoadingMore = true;
    loadMoreBtn.textContent = 'Yükleniyor...';
    
    if (page === 1) {
        mainLoader.style.display = 'flex';
        gamesContainer.style.display = 'none';
        homepageSections.style.display = 'none';
    }

    try {
        const amount = page === 1 ? 120 : 40;
        const url = `https://catalog.api.gamedistribution.com/api/v2.0/rss/All/?collection=All&amount=${amount}&page=${page}&format=json`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`API Network status is not OK: ${response.status}`);
        }
        
        const data = await response.json();
        let newGames = [];
        
        if (Array.isArray(data)) {
            newGames = data;
        } else if (data.items && Array.isArray(data.items)) {
            newGames = data.items;
        }
        
        if (newGames.length > 0) {
            // Filter duplicates out (in case API overlaps)
            const existingIds = new Set(gamesData.map(g => g.Url));
            const uniqueNewGames = newGames.filter(g => !existingIds.has(g.Url));
            gamesData = [...gamesData, ...uniqueNewGames];
        }
        
        console.log(`Successfully loaded page ${page}`, newGames);
        
        // If we have a pending game route loaded, open it now
        if (pendingGameToOpen) {
            const game = gamesData.find(g => slugify(g.Title) === pendingGameToOpen || g.Md5 === pendingGameToOpen);
            if (game) {
                openGame(game, false);
                pendingGameToOpen = null;
            }
        }
    } catch (error) {
        console.warn("CORS policy or network failure. Using fallback dataset.", error);
        // Only load fallback on page 1 if list is empty
        if (gamesData.length === 0) {
            gamesData = FALLBACK_GAMES;
            if (pendingGameToOpen) {
                const game = gamesData.find(g => slugify(g.Title) === pendingGameToOpen || g.Md5 === pendingGameToOpen);
                if (game) openGame(game, false);
                pendingGameToOpen = null;
            }
        }
    } finally {
        isLoadingMore = false;
        loadMoreBtn.innerHTML = `Daha Fazla Oyun Yükle <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 1.1rem; height: 1.1rem;"><polyline points="6 9 12 15 18 9"></polyline></svg>`;
        mainLoader.style.display = 'none';
        applyFilters();
    }
}

// Helper function to create game card DOM element
function createGameCardElement(game, index, isFeatured = false, badgeText = '') {
    let imageSrc = 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=500&auto=format&fit=crop&q=60';
    if (game.Asset && game.Asset.length > 0) {
        const preferred = game.Asset.find(url => url.includes('512x384') || url.includes('512x512'));
        imageSrc = preferred || game.Asset[0];
    }
    const primaryCat = game.Category && game.Category.length > 0 ? game.Category[0] : 'Oyun';

    const card = document.createElement('div');
    card.className = `game-card${isFeatured ? ' featured' : ''}`;
    card.style.animation = `fadeSlideIn 0.4s ease forwards ${index * 0.03}s`;
    card.style.opacity = '0';
    card.style.transform = 'translateY(15px)';
    card.style.cursor = 'pointer';

    let badgeHTML = '';
    if (badgeText) {
        const badgeClass = badgeText === 'YENİ' ? 'badge-new' : (badgeText === 'POPÜLER' ? 'badge-hot' : 'badge-best');
        badgeHTML = `<span class="card-badge ${badgeClass}">${badgeText}</span>`;
    }

    card.innerHTML = `
        ${badgeHTML}
        <div class="game-card-img-wrapper">
            <img src="${imageSrc}" alt="${game.Title}" class="game-card-img" loading="lazy">
        </div>
        <div class="game-card-content">
            <span class="game-card-category">${primaryCat}</span>
            <h3 class="game-card-title">${game.Title}</h3>
            <button class="play-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 1.1rem; height: 1.1rem;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                Şimdi Oyna
            </button>
        </div>
    `;

    // Clicking anywhere on the card plays the game
    card.addEventListener('click', () => openGame(game));

    return card;
}

// Generate the Hero Banner Showcase element
function renderHeroShowcase(games) {
    const heroCardContainer = document.getElementById('hero-card-container');
    if (!heroCardContainer || games.length === 0) return;
    
    // Select the first editors choice game
    const featuredGame = games[0];
    let imageSrc = 'https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1000&auto=format&fit=crop&q=80';
    if (featuredGame.Asset && featuredGame.Asset.length > 0) {
        const preferred = featuredGame.Asset.find(url => url.includes('512x384') || url.includes('512x512'));
        imageSrc = preferred || featuredGame.Asset[0];
    }
    
    heroCardContainer.innerHTML = `
        <div class="hero-info">
            <span class="hero-badge">Günün Oyunu 🌟</span>
            <h2 class="hero-title">${featuredGame.Title}</h2>
            <p class="hero-description">${featuredGame.Description || 'Muhteşem grafikleri ve sürükleyici oynanışı ile portalımızın en çok ilgi gören oyunu! Hemen ücretsiz, indirmeden tarayıcında oyna.'}</p>
            <button class="hero-cta" id="hero-play-btn">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="width: 1.3rem; height: 1.3rem;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                Hemen Oyna
            </button>
        </div>
        <div class="hero-media-wrapper">
            <img src="${imageSrc}" alt="${featuredGame.Title}" class="hero-image">
        </div>
    `;
    
    const playBtn = document.getElementById('hero-play-btn');
    if (playBtn) {
        playBtn.addEventListener('click', () => openGame(featuredGame));
    }
}

// Distribute loaded games to specific sections
function distributeGamesToSections(games) {
    // Populate the top hero showcase
    renderHeroShowcase(games);

    // 1. Editors' Choice: first 6 games
    const editorsChoice = games.slice(0, 6);
    renderSectionGrid(editorsChoice, editorsChoiceGrid, 'editorsChoice');

    // 2. Popular Games: next 18 games
    const popular = games.slice(6, 24);
    renderSectionGrid(popular, popularGamesGrid, 'popular');

    // 3. New Games: next 18 games
    const newGames = games.slice(24, 42);
    renderSectionGrid(newGames, newGamesGrid, 'new');

    // Categorized lists
    const warGames = [];
    const racingGames = [];
    const girlsGames = [];
    const skillGames = [];

    // Filter by type into separate category arrays
    games.forEach(game => {
        const categories = game.Category ? game.Category.map(c => c.toLowerCase()) : [];
        const tags = game.Tag ? game.Tag.map(t => t.toLowerCase()) : [];

        // War/Action
        if (warGames.length < 12) {
            if (categories.includes('shooter') || categories.includes('fighting') || tags.includes('war') || tags.includes('gun') || tags.includes('sniper') || tags.includes('battle') || categories.includes('action')) {
                if (!editorsChoice.includes(game) && !popular.includes(game) && !newGames.includes(game)) {
                    warGames.push(game);
                }
            }
        }

        // Racing
        if (racingGames.length < 12) {
            if (categories.includes('racing') || categories.includes('driving') || tags.includes('car') || tags.includes('moto')) {
                if (!editorsChoice.includes(game) && !popular.includes(game) && !newGames.includes(game) && !warGames.includes(game)) {
                    racingGames.push(game);
                }
            }
        }

        // Girls
        if (girlsGames.length < 12) {
            if (categories.includes('girls') || categories.includes('cooking') || tags.includes('girl') || tags.includes('fashion') || tags.includes('dress') || tags.includes('makeup')) {
                if (!editorsChoice.includes(game) && !popular.includes(game) && !newGames.includes(game) && !warGames.includes(game) && !racingGames.includes(game)) {
                    girlsGames.push(game);
                }
            }
        }

        // Skill
        if (skillGames.length < 12) {
            if (categories.includes('skill') || categories.includes('puzzle') || categories.includes('educational') || categories.includes('arcade') || tags.includes('logic')) {
                if (!editorsChoice.includes(game) && !popular.includes(game) && !newGames.includes(game) && !warGames.includes(game) && !racingGames.includes(game) && !girlsGames.includes(game)) {
                    skillGames.push(game);
                }
            }
        }
    });

    // Fill grids up to 12 using remaining items if API didn't return enough specific matches
    let index = 42;
    while (warGames.length < 12 && index < games.length) {
        const g = games[index++];
        if (!editorsChoice.includes(g) && !popular.includes(g) && !newGames.includes(g) && !racingGames.includes(g) && !girlsGames.includes(g) && !skillGames.includes(g)) {
            warGames.push(g);
        }
    }
    while (racingGames.length < 12 && index < games.length) {
        const g = games[index++];
        if (!editorsChoice.includes(g) && !popular.includes(g) && !newGames.includes(g) && !warGames.includes(g) && !girlsGames.includes(g) && !skillGames.includes(g)) {
            racingGames.push(g);
        }
    }
    while (girlsGames.length < 12 && index < games.length) {
        const g = games[index++];
        if (!editorsChoice.includes(g) && !popular.includes(g) && !newGames.includes(g) && !warGames.includes(g) && !racingGames.includes(g) && !skillGames.includes(g)) {
            girlsGames.push(g);
        }
    }
    while (skillGames.length < 12 && index < games.length) {
        const g = games[index++];
        if (!editorsChoice.includes(g) && !popular.includes(g) && !newGames.includes(g) && !warGames.includes(g) && !racingGames.includes(g) && !girlsGames.includes(g)) {
            skillGames.push(g);
        }
    }

    renderSectionGrid(warGames, warGamesGrid, 'war');
    renderSectionGrid(racingGames, racingGamesGrid, 'racing');
    renderSectionGrid(girlsGames, girlsGamesGrid, 'girls');
    renderSectionGrid(skillGames, skillGamesGrid, 'skill');
}

function renderSectionGrid(games, gridElement, sectionName = '') {
    gridElement.innerHTML = '';
    games.forEach((game, index) => {
        let isFeatured = false;
        let badgeText = '';
        
        if (sectionName === 'editorsChoice') {
            if (index < 2) isFeatured = true;
            badgeText = 'EDİTÖR';
        } else if (sectionName === 'popular') {
            if (index % 5 === 0) badgeText = 'POPÜLER';
        } else if (sectionName === 'new') {
            if (index % 4 === 0) badgeText = 'YENİ';
        } else if (sectionName === 'war') {
            if (index % 6 === 0) badgeText = 'AKSİYON';
        } else if (sectionName === 'racing') {
            if (index % 6 === 0) badgeText = 'YARIŞ';
        } else if (sectionName === 'girls') {
            if (index % 6 === 0) badgeText = 'KIZ';
        } else if (sectionName === 'skill') {
            if (index % 6 === 0) badgeText = 'ZEKA';
        }
        
        const card = createGameCardElement(game, index, isFeatured, badgeText);
        gridElement.appendChild(card);
    });
}

// Apply Search & Category filters
function applyFilters() {
    let filtered = gamesData;

    // Filter by Category
    if (activeCategory !== 'all') {
        filtered = filtered.filter(game => {
            const categories = game.Category ? game.Category.map(c => c.toLowerCase()) : [];
            const tags = game.Tag ? game.Tag.map(t => t.toLowerCase()) : [];
            
            // Check dynamic genre mapping from URL #/kategori/{name}
            if (activeCategory === 'dynamic') {
                return categories.includes(dynamicCategoryName) || tags.includes(dynamicCategoryName);
            }
            
            switch (activeCategory) {
                case 'action':
                    return categories.includes('action') || categories.includes('shooter') || categories.includes('fighting') || tags.includes('zombie');
                case 'war':
                    return categories.includes('shooter') || categories.includes('fighting') || tags.includes('war') || tags.includes('gun') || tags.includes('sniper') || tags.includes('battle');
                case 'racing':
                    return categories.includes('racing') || categories.includes('driving') || tags.includes('car') || tags.includes('moto');
                case 'skill':
                    return categories.includes('skill') || categories.includes('puzzle') || categories.includes('educational') || categories.includes('arcade') || tags.includes('logic');
                case 'adventure':
                    return categories.includes('adventure') || categories.includes('rpg') || categories.includes('platformer') || tags.includes('escape');
                case 'girls':
                    return categories.includes('girls') || categories.includes('cooking') || tags.includes('girl') || tags.includes('fashion') || tags.includes('dress') || tags.includes('makeup');
                case 'multiplayer':
                    return categories.includes('multiplayer') || tags.includes('2-player') || tags.includes('pvp') || tags.includes('co-op') || tags.includes('2player');
                default:
                    return false;
            }
        });
    }

    // Filter by Search Query
    if (searchQuery) {
        filtered = filtered.filter(game => 
            game.Title.toLowerCase().includes(searchQuery) ||
            (game.Description && game.Description.toLowerCase().includes(searchQuery))
        );
    }

    // Toggle Homepage Sections vs Single Category/Search Grid View
    if (activeCategory === 'all' && !searchQuery) {
        gamesContainer.style.display = 'none';
        noResultsMsg.style.display = 'none';
        homepageSections.style.display = 'block';
        loadMoreContainer.style.display = 'block';
        distributeGamesToSections(gamesData);
    } else {
        homepageSections.style.display = 'none';
        renderGameGrid(filtered);
        
        // Hide load more if searching or if no games returned
        if (searchQuery || filtered.length === 0 || activeCategory === 'dynamic') {
            loadMoreContainer.style.display = 'none';
        } else {
            loadMoreContainer.style.display = 'block';
        }
    }
}

// Render list of games into the Grid container
function renderGameGrid(games) {
    gamesContainer.innerHTML = '';
    
    if (games.length === 0) {
        gamesContainer.style.display = 'none';
        noResultsMsg.style.display = 'flex';
        return;
    }

    noResultsMsg.style.display = 'none';
    gamesContainer.style.display = 'grid';

    games.forEach((game, index) => {
        const card = createGameCardElement(game, index);
        gamesContainer.appendChild(card);
    });
}

// Open modal and load game iframe
function openGame(game, updateHash = true) {
    if (updateHash) {
        window.location.hash = `#/oyun/${slugify(game.Title)}`;
        return; // handleRouteChange will be triggered and open it with updateHash = false
    }

    // Show iframe spinner loader
    iframeLoader.style.display = 'flex';
    iframeLoader.style.opacity = '1';

    // Populate game metadata details
    modalGameTitle.textContent = game.Title;
    modalGameDescription.textContent = game.Description || "Bu oyun hakkında detaylı bir açıklama bulunmuyor.";
    modalGameInstructions.textContent = game.Instructions || "Oyunu yönlendirmek için ekrandaki butonları, fareyi veya yön tuşlarını (WASD) kullanabilirsiniz.";

    // Update game SEO tags
    updateSEOTags('game', game.Title);

    // Reset tabs back to "Description" (Açıklama)
    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabContents.forEach(content => content.classList.remove('active'));
    document.querySelector('[data-tab="description"]').classList.add('active');
    document.getElementById('tab-description').classList.add('active');

    // Trigger opening the modal
    gameModal.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Set game URL to start loading inside the iframe
    gameIframe.src = game.Url;
}

// Close game modal and reset state
function closeModal(updateHash = true) {
    gameModal.classList.remove('active');
    document.body.style.overflow = '';
    
    // Stop the game audio/play by emptying iframe source
    gameIframe.src = '';
    
    // Reset fullscreen mode if active
    if (document.body.classList.contains('fullscreen-active')) {
        document.body.classList.remove('fullscreen-active');
    }

    if (updateHash) {
        // Restore hash back to active category
        const map = {
            'all': '',
            'action': 'aksiyon',
            'war': 'savas',
            'racing': 'yaris',
            'skill': 'beceri',
            'adventure': 'macera',
            'girls': 'kiz',
            'multiplayer': 'iki-kisilik',
            'dynamic': `kategori/${dynamicCategoryName}`
        };
        window.location.hash = map[activeCategory] ? `#/${map[activeCategory]}` : '#/';
    }
}

// Toggle fullscreen class view
function toggleFullscreen() {
    document.body.classList.toggle('fullscreen-active');
}

// Dynamic slide-in animation stylesheet append (keeps JS clean)
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeSlideIn {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);
