// Frontend application logic
let allCompanies = [];
let currentCompany = null;
let currentQuiz = null;
let quizScore = { correct: 0, total: 0, streak: 0 };

// DOM Elements
const searchInput = document.getElementById('company-search-input');
const searchDropdown = document.getElementById('search-dropdown');
const clearSearchBtn = document.getElementById('clear-search-btn');
const quickPicks = document.getElementById('quick-picks');
const metricsContainer = document.getElementById('metrics-container');
const analysisLoading = document.getElementById('analysis-loading');
const companyDisplay = document.getElementById('company-display');

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  await fetchCompaniesList();
  renderQuickPicks();

  // Load default company (Toyota 7203 or first)
  if (allCompanies.length > 0) {
    selectCompany(allCompanies[0].id);
  }

  // Setup Search Listeners
  searchInput.addEventListener('input', handleSearchInput);
  searchInput.addEventListener('focus', () => {
    if (searchInput.value.trim().length > 0) {
      searchDropdown.classList.remove('hidden');
    }
  });

  clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    clearSearchBtn.classList.add('hidden');
    searchDropdown.classList.add('hidden');
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
      searchDropdown.classList.add('hidden');
    }
  });
});

// Switch Tabs
function switchTab(tabId) {
  const tabs = ['analysis', 'quiz', 'guide'];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}`);
    const navBtn = document.getElementById(`nav-tab-${t}`);
    if (t === tabId) {
      el.classList.remove('hidden');
      navBtn.className = "px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 bg-indigo-600 text-white shadow-sm";
    } else {
      el.classList.add('hidden');
      navBtn.className = "px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 text-slate-300 hover:text-white hover:bg-slate-800";
    }
  });

  if (tabId === 'quiz' && !currentQuiz) {
    fetchNextQuiz();
  }
}

// Fetch all companies list
async function fetchCompaniesList() {
  try {
    const res = await fetch('/api/companies');
    allCompanies = await res.json();
  } catch (err) {
    console.error('Failed to load companies:', err);
  }
}

// Render Quick Picks (Top featured companies)
function renderQuickPicks() {
  const featuredCodes = ['7203', '7974', '6758', '6861', '9983', '4063', '8058', '4661'];
  const featured = allCompanies.filter(c => featuredCodes.includes(c.code));

  quickPicks.innerHTML = featured.map(c => `
    <button onclick="selectCompany('${c.id}')" class="px-2.5 py-1 text-xs bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300 border border-slate-200 rounded-lg text-slate-700 font-medium transition">
      ${c.short_name} (${c.code})
    </button>
  `).join('');
}

// Handle incremental search
function handleSearchInput(e) {
  const query = e.target.value.trim().toLowerCase();
  if (query.length > 0) {
    clearSearchBtn.classList.remove('hidden');
  } else {
    clearSearchBtn.classList.add('hidden');
    searchDropdown.classList.add('hidden');
    return;
  }

  const matches = allCompanies.filter(c => {
    return c.name.toLowerCase().includes(query) ||
           c.short_name.toLowerCase().includes(query) ||
           c.code.includes(query) ||
           (c.sector && c.sector.toLowerCase().includes(query));
  });

  if (matches.length === 0) {
    searchDropdown.innerHTML = `
      <div class="p-4 text-center text-sm text-slate-400">
        該当する企業が見つかりませんでした
      </div>
    `;
  } else {
    searchDropdown.innerHTML = matches.map(c => `
      <div onclick="selectCompany('${c.id}')" class="px-4 py-3 hover:bg-indigo-50/80 cursor-pointer transition flex items-center justify-between group">
        <div>
          <div class="font-bold text-slate-800 group-hover:text-indigo-700 flex items-center gap-2">
            ${c.name}
            <span class="text-xs bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded font-mono">${c.code}</span>
          </div>
          <div class="text-xs text-slate-500 mt-0.5">
            ${c.sector} • ${c.standard} • ${c.fiscal_period}
          </div>
        </div>
        <i class="fa-solid fa-chevron-right text-slate-300 group-hover:text-indigo-500 text-sm"></i>
      </div>
    `).join('');
  }

  searchDropdown.classList.remove('hidden');
}

// Select a company and render metrics
async function selectCompany(companyId) {
  searchDropdown.classList.add('hidden');
  searchInput.value = '';
  clearSearchBtn.classList.add('hidden');

  companyDisplay.classList.add('hidden');
  analysisLoading.classList.remove('hidden');

  try {
    const res = await fetch(`/api/companies/${companyId}`);
    const data = await res.json();
    currentCompany = data;
    renderCompanyDetails(data);
  } catch (err) {
    console.error('Error fetching company details:', err);
  } finally {
    analysisLoading.classList.add('hidden');
    companyDisplay.classList.remove('hidden');
  }
}

// Render company header and metrics
function renderCompanyDetails(data) {
  const c = data.company;
  const metrics = data.metrics;

  document.getElementById('disp-code').textContent = `コード: ${c.code}`;
  document.getElementById('disp-sector').textContent = c.sector;
  document.getElementById('disp-standard').textContent = c.standard;
  document.getElementById('disp-fiscal-text').textContent = c.fiscal_period;
  document.getElementById('disp-name').textContent = c.name;
  document.getElementById('disp-desc').textContent = c.description;
  const discLink = document.getElementById('disp-disclosure-link');
  if (discLink) discLink.href = c.disclosure_url || `https://kabutan.jp/stock/kaiji/?code=${c.code}`;
  
  const edinetBtnLabel = document.getElementById('label-edinet-code');
  if (edinetBtnLabel) edinetBtnLabel.textContent = `EDINET: ${c.edinet_code}`;

  // Raw stats
  const raw = c.financial_raw;
  document.getElementById('stat-revenue').textContent = `${(raw.revenue / 100).toLocaleString('ja-JP', {maximumFractionDigits: 0})} 億円`;
  document.getElementById('stat-op-income').textContent = `${(raw.operating_income / 100).toLocaleString('ja-JP', {maximumFractionDigits: 0})} 億円`;
  document.getElementById('stat-net-income').textContent = `${(raw.net_income / 100).toLocaleString('ja-JP', {maximumFractionDigits: 0})} 億円`;
  
  // Market & Per-share stats
  document.getElementById('stat-price').textContent = raw.stock_price ? `${raw.stock_price.toLocaleString()} 円` : '--';
  document.getElementById('stat-eps').textContent = raw.eps ? `${raw.eps.toFixed(2)} 円` : '--';
  document.getElementById('stat-bps').textContent = raw.bps ? `${raw.bps.toFixed(2)} 円` : '--';

  // Render 7 Metric Cards: 自己資本比率, ROE, ROIC, PBR, PER, ROA, 売上高営業利益率
  const metricKeys = ['equity_ratio', 'roe', 'roic', 'pbr', 'per', 'roa', 'operating_margin'];
  metricsContainer.innerHTML = metricKeys.map(key => {
    const m = metrics[key];
    return createMetricCardHTML(m);
  }).join('');
}

// HTML generator for single metric card
function createMetricCardHTML(m) {
  // Theme color based on metric
  let colorTheme = {
    bg: 'border-blue-200 bg-blue-50/20',
    badge: 'bg-blue-100 text-blue-800 border-blue-200',
    accent: 'text-blue-600',
    icon: 'fa-shield-halved'
  };
  if (m.key === 'roe') {
    colorTheme = {
      bg: 'border-indigo-200 bg-indigo-50/20',
      badge: 'bg-indigo-100 text-indigo-800 border-indigo-200',
      accent: 'text-indigo-600',
      icon: 'fa-chart-pie'
    };
  } else if (m.key === 'roic') {
    colorTheme = {
      bg: 'border-emerald-200 bg-emerald-50/20',
      badge: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      accent: 'text-emerald-600',
      icon: 'fa-bolt'
    };
  } else if (m.key === 'pbr') {
    colorTheme = {
      bg: 'border-teal-200 bg-teal-50/20',
      badge: 'bg-teal-100 text-teal-800 border-teal-200',
      accent: 'text-teal-600',
      icon: 'fa-coins'
    };
  } else if (m.key === 'per') {
    colorTheme = {
      bg: 'border-rose-200 bg-rose-50/20',
      badge: 'bg-rose-100 text-rose-800 border-rose-200',
      accent: 'text-rose-600',
      icon: 'fa-magnifying-glass-dollar'
    };
  } else if (m.key === 'roa') {
    colorTheme = {
      bg: 'border-amber-200 bg-amber-50/20',
      badge: 'bg-amber-100 text-amber-800 border-amber-200',
      accent: 'text-amber-600',
      icon: 'fa-scale-balanced'
    };
  } else if (m.key === 'operating_margin') {
    colorTheme = {
      bg: 'border-purple-200 bg-purple-50/20',
      badge: 'bg-purple-100 text-purple-800 border-purple-200',
      accent: 'text-purple-600',
      icon: 'fa-arrow-trend-up'
    };
  }

  // Used items HTML
  const itemsHTML = m.items_used.map(item => `
    <div class="bg-white p-3 rounded-lg border border-slate-200/80 text-xs space-y-1">
      <div class="flex items-center justify-between font-bold text-slate-800">
        <span><i class="fa-solid fa-tag text-slate-400 mr-1"></i>${item.item_name}</span>
        <span class="font-mono text-indigo-700">${item.value}</span>
      </div>
      <div class="text-slate-500 flex items-start gap-1">
        <i class="fa-regular fa-file-lines text-slate-400 mt-0.5"></i>
        <span>${item.location}</span>
      </div>
      <div class="text-indigo-600 font-medium">
        <i class="fa-solid fa-location-dot mr-1"></i>掲載ページ：${item.page}
      </div>
    </div>
  `).join('');

  return `
    <div class="bg-white rounded-2xl border ${colorTheme.bg} p-6 shadow-sm hover:shadow-md transition-shadow space-y-4 animate-fade-in flex flex-col justify-between">
      <div>
        <!-- Card Header -->
        <div class="flex items-start justify-between gap-3">
          <div class="space-y-1">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <i class="fa-solid ${colorTheme.icon} ${colorTheme.accent}"></i>
              ${m.name.split('(')[0].trim()}
            </span>
            <h4 class="text-base font-bold text-slate-900">${m.name}</h4>
          </div>
          <span class="px-2.5 py-1 text-xs font-bold rounded-full border ${colorTheme.badge}">
            ${m.evaluation}
          </span>
        </div>

        <!-- Big Value Display -->
        <div class="my-4 flex items-baseline gap-2">
          <span class="text-4xl font-black tracking-tight ${colorTheme.accent}">${m.value}</span>
          <span class="text-xl font-bold text-slate-500">${m.unit}</span>
        </div>

        <p class="text-xs sm:text-sm text-slate-600 leading-relaxed mb-4">
          ${m.description}
        </p>

        <!-- Calculation Formula Box -->
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2">
          <div class="text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <i class="fa-solid fa-calculator text-indigo-500"></i>
            <span>計算式と実数値の代入</span>
          </div>
          <div class="bg-white p-2 rounded-lg border border-slate-200 text-xs font-mono text-slate-700">
            <span class="text-slate-400 block font-sans">【定義】</span>
            ${m.formula_definition}
          </div>
          <div class="bg-white p-2 rounded-lg border border-indigo-100 text-xs font-mono text-indigo-700 font-semibold">
            <span class="text-slate-400 block font-sans">【実数値】</span>
            ${m.formula_applied}
          </div>
        </div>
      </div>

      <!-- Financial Source Locations -->
      <div class="pt-3 border-t border-slate-100 space-y-2">
        <div class="text-xs font-bold text-slate-700 flex items-center justify-between">
          <span class="flex items-center gap-1">
            <i class="fa-solid fa-book-open text-emerald-500"></i>
            計算に使用した有報項目と掲載箇所
          </span>
          <span class="text-[11px] text-slate-400 font-normal">EDINET開示原典</span>
        </div>
        <div class="space-y-2">
          ${itemsHTML}
        </div>
      </div>
    </div>
  `;
}

// ==============================================================
// QUIZ MODE LOGIC
// ==============================================================

async function fetchNextQuiz() {
  const card = document.getElementById('quiz-card');
  const feedbackBox = document.getElementById('quiz-feedback-box');
  feedbackBox.classList.add('hidden');

  try {
    const res = await fetch('/api/quiz');
    const quiz = await res.json();
    currentQuiz = quiz;
    renderQuiz(quiz);
  } catch (err) {
    console.error('Failed to load quiz:', err);
  }
}

function renderQuiz(quiz) {
  document.getElementById('quiz-company-name').textContent = quiz.company_name;
  document.getElementById('quiz-company-code').textContent = quiz.code;
  document.getElementById('quiz-fiscal-period').textContent = quiz.fiscal_period;
  document.getElementById('quiz-question-title').textContent = quiz.question_title;
  document.getElementById('quiz-question-lead').textContent = quiz.question_lead;

  // Render Hint items
  const hintsContainer = document.getElementById('quiz-hints-list');
  hintsContainer.innerHTML = quiz.hint_items.map(item => `
    <div class="bg-white p-3 rounded-lg border border-amber-200/60 shadow-2xs">
      <div class="text-xs text-amber-900 font-bold flex items-center justify-between">
        <span>${item.item_name}</span>
        <span class="font-mono text-indigo-700 font-extrabold text-sm">${item.value}</span>
      </div>
      <div class="text-[11px] text-amber-700/80 mt-1">
        掲載箇所：${item.location} (${item.page})
      </div>
    </div>
  `).join('');

  // Render 3 Options buttons
  const optionsContainer = document.getElementById('quiz-options-container');
  optionsContainer.innerHTML = quiz.options.map((opt, idx) => {
    const letter = ['A', 'B', 'C'][idx];
    return `
      <button onclick="handleOptionSelect('${opt}', this)" class="option-btn w-full p-4 rounded-xl border-2 border-slate-200 bg-white hover:border-indigo-500 hover:bg-indigo-50/50 text-slate-800 font-bold text-lg flex items-center justify-between shadow-xs">
        <span class="w-8 h-8 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center text-sm font-black">
          ${letter}
        </span>
        <span class="font-mono text-xl">${opt}</span>
        <i class="fa-regular fa-circle text-slate-300 text-lg"></i>
      </button>
    `;
  }).join('');
}

async function handleOptionSelect(selectedOption, clickedBtn) {
  // Disable all option buttons
  const buttons = document.querySelectorAll('.option-btn');
  buttons.forEach(b => b.disabled = true);

  const isCorrect = (selectedOption === currentQuiz.correct_option);

  // Update Score
  quizScore.total += 1;
  if (isCorrect) {
    quizScore.correct += 1;
    quizScore.streak += 1;
  } else {
    quizScore.streak = 0;
  }
  document.getElementById('quiz-streak').textContent = quizScore.streak;
  document.getElementById('quiz-score').textContent = `${quizScore.correct} / ${quizScore.total}`;

  // Highlight choices
  buttons.forEach(btn => {
    const optText = btn.querySelector('.font-mono').textContent.trim();
    if (optText === currentQuiz.correct_option) {
      btn.className = "option-btn w-full p-4 rounded-xl border-2 border-emerald-500 bg-emerald-50 text-emerald-900 font-bold text-lg flex items-center justify-between shadow-md";
      btn.querySelector('i').className = "fa-solid fa-circle-check text-emerald-600 text-xl";
    } else if (optText === selectedOption && !isCorrect) {
      btn.className = "option-btn w-full p-4 rounded-xl border-2 border-rose-500 bg-rose-50 text-rose-900 font-bold text-lg flex items-center justify-between shadow-md";
      btn.querySelector('i').className = "fa-solid fa-circle-xmark text-rose-600 text-xl";
    } else {
      btn.className = "option-btn w-full p-4 rounded-xl border border-slate-200 bg-slate-50 text-slate-400 font-medium text-lg flex items-center justify-between opacity-50";
    }
  });

  // Display Feedback & Explanation
  const feedbackBox = document.getElementById('quiz-feedback-box');
  const banner = document.getElementById('quiz-result-banner');

  if (isCorrect) {
    banner.className = "p-4 rounded-xl flex items-center gap-3 font-bold text-lg bg-emerald-100 text-emerald-800 border border-emerald-300";
    banner.innerHTML = `
      <i class="fa-solid fa-circle-check text-2xl text-emerald-600"></i>
      <div>
        <span>正解です！見事な財務分析です！</span>
        <span class="block text-xs font-normal text-emerald-700">正解：${currentQuiz.correct_option}（${currentQuiz.explanation.evaluation}）</span>
      </div>
    `;
  } else {
    banner.className = "p-4 rounded-xl flex items-center gap-3 font-bold text-lg bg-rose-100 text-rose-800 border border-rose-300";
    banner.innerHTML = `
      <i class="fa-solid fa-circle-xmark text-2xl text-rose-600"></i>
      <div>
        <span>惜しい！不正解です。</span>
        <span class="block text-xs font-normal text-rose-700">正解は ${currentQuiz.correct_option} でした。</span>
      </div>
    `;
  }

  // Set Explanation Details
  const exp = currentQuiz.explanation;
  document.getElementById('quiz-exp-definition').textContent = exp.formula_definition;
  document.getElementById('quiz-exp-applied').textContent = exp.formula_applied;
  document.getElementById('quiz-exp-desc').textContent = exp.description;
  document.getElementById('quiz-edinet-link').href = exp.edinet_url;

  const sourcesContainer = document.getElementById('quiz-exp-sources');
  sourcesContainer.innerHTML = exp.source_details.map(s => `
    <div class="flex items-center justify-between bg-white p-2 rounded border border-slate-200/60">
      <span class="font-medium text-slate-700">${s.item_name}</span>
      <span class="text-indigo-600">${s.location} (${s.page})</span>
    </div>
  `).join('');

  feedbackBox.classList.remove('hidden');
  feedbackBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Handle Disclosure Link Click
function handleDisclosureClick(event) {
  let targetUrl = "https://kabutan.jp/stock/kaiji/?code=7203";
  if (currentCompany && currentCompany.company) {
    const comp = currentCompany.company;
    targetUrl = comp.disclosure_url || `https://kabutan.jp/stock/kaiji/?code=${comp.code}`;
  }
  
  // Ensure link href is updated
  const linkEl = document.getElementById('disp-disclosure-link');
  if (linkEl) {
    linkEl.href = targetUrl;
  }
  
  // If clicked, open targetUrl directly
  event.preventDefault();
  window.open(targetUrl, '_blank', 'noopener,noreferrer');
}

// Open EDINET Search and Copy Company Code reliably
function openEdinetWithCopy(event) {
  if (event) event.preventDefault();

  let code = "E02144";
  let name = "トヨタ自動車";
  if (currentCompany && currentCompany.company) {
    const comp = currentCompany.company;
    code = comp.edinet_code || comp.code;
    name = comp.short_name || comp.name;
  }

  // 1. Copy to clipboard with universal fallback
  copyTextToClipboard(code);

  // 2. Show user feedback toast immediately
  showToast('EDINETコードをコピーしました！', `「${code}」（${name}）をクリップボードにコピーしました。EDINET検索窓に貼り付けて検索できます。`);

  // 3. Open EDINET search synchronously to avoid popup blocker
  window.open('https://disclosure2.edinet-fsa.go.jp/', '_blank', 'noopener,noreferrer');
}

// Robust clipboard copy function (supports modern API + fallback)
function copyTextToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).catch(err => {
      fallbackCopyText(text);
    });
  } else {
    fallbackCopyText(text);
  }
}

function fallbackCopyText(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  textArea.style.position = "fixed";
  textArea.style.left = "-999999px";
  textArea.style.top = "-999999px";
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  try {
    document.execCommand('copy');
  } catch (err) {
    console.warn('Fallback copy failed', err);
  }
  document.body.removeChild(textArea);
}

// Toast notification helper
function showToast(title, desc) {
  const toast = document.getElementById('toast-notify');
  if (!toast) return;
  document.getElementById('toast-title').textContent = title;
  document.getElementById('toast-desc').textContent = desc;
  
  toast.classList.remove('translate-y-20', 'opacity-0', 'pointer-events-none');
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0', 'pointer-events-none');
  }, 4500);
}
