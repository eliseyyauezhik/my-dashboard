(function () {
  "use strict";

  let projectsData = [];
  let upgradePathsData = [];
  let ideasData = [];
  let chatsData = [];
  let workflowsData = [];
  let projectGroupsData = [];
  let archivesData = [];
  let consolidationData = {};
  let dashboardStats = {};
  let telegramData = {
    stats: {},
    summary: {},
    sources: [],
    areaBuckets: [],
    skillSuggestions: [],
    projectSuggestions: [],
    processingProtocol: [],
  };
  let monitoringData = {
    profile: {},
    stats: {},
    processingProtocol: [],
    routingRules: [],
    recommendations: [],
    skillSuggestions: [],
    projectSuggestions: [],
  };
  let ideaRouterData = {
    summary: {},
    queue: [],
    clusters: [],
    recommendations: [],
  };
  let currentFilter = "all";
  let currentGroupFilter = "all";
  let currentPanel = "projectsPanel";
  let searchQuery = "";
  let currentSignalFilter = "all";
  let signalsData = [];

  // --- Supabase Client ---
  const _cfg = window.DASHBOARD_CONFIG || {};
  let supabaseClient = null;
  try {
    if (_cfg.SUPABASE_URL && _cfg.SUPABASE_KEY && typeof supabase !== 'undefined' && supabase.createClient) {
      supabaseClient = supabase.createClient(_cfg.SUPABASE_URL, _cfg.SUPABASE_KEY);
    }
  } catch (e) {
    console.warn('Supabase SDK not loaded:', e);
  }

  const STATUS_LABELS = {
    active: "В работе",
    paused: "Пауза",
    research: "Исследование",
    backlog: "Бэклог",
    done: "Готово",
  };

  const PRIORITY_LABELS = {
    high: "Высокий",
    medium: "Средний",
    low: "Низкий",
  };

  function isFileProtocol() {
    return typeof window !== "undefined" && window.location && window.location.protocol === "file:";
  }

  function renderFileProtocolHint() {
    if (!isFileProtocol()) return;
    const el = document.getElementById("syncInfo");
    if (el) {
      el.textContent =
        "Открыто как file:// — браузер блокирует загрузку JSON. Запустите сервер: .\\start_dashboard.ps1 -Open";
    }
    const banner = document.getElementById("fileProtocolBanner");
    if (banner) {
      banner.hidden = false;
    }
  }

  async function loadDashboardData() {
    const sources = ["data/dashboard_data.json", "projects.json"];
    let lastError = null;
    for (const source of sources) {
      try {
        const res = await fetch(source, { cache: "no-store" });
        if (!res.ok) continue;
        const data = await res.json();
        return { data, source };
      } catch (err) {
        lastError = err;
      }
    }
    throw lastError || new Error("Не удалось загрузить основные данные дашборда");
  }

  async function loadOptionalJson(source) {
    try {
      const res = await fetch(source, { cache: "no-store" });
      if (!res.ok) return null;
      return await res.json();
    } catch (err) {
      console.warn(`Optional source not loaded: ${source}`, err);
      return null;
    }
  }

  async function loadFirstOptionalJson(sources) {
    for (const source of sources) {
      const data = await loadOptionalJson(source);
      if (data) return data;
    }
    return null;
  }

  function mergeIdeas(baseIdeas, inboxPayload) {
    const extras = Array.isArray(inboxPayload?.ideas) ? inboxPayload.ideas : [];
    const result = [...(baseIdeas || [])];
    const seen = new Set(result.map((idea) => String(idea.id || idea.title || "").toLowerCase()));
    extras.forEach((idea) => {
      const key = String(idea.id || idea.title || "").toLowerCase();
      if (!key || seen.has(key)) return;
      seen.add(key);
      result.push({
        id: idea.id || key,
        title: idea.title || "Новая идея",
        description: idea.description || idea.comment || "",
        tags: Array.isArray(idea.tags) ? idea.tags : [],
        priority: idea.priority || "medium",
        relatedProject: idea.relatedProject || "",
        addedDate: idea.addedDate || "",
      });
    });
    return result;
  }

  function toDateLabel(dateStr) {
    const d = dateStr ? new Date(dateStr) : new Date();
    if (Number.isNaN(d.getTime())) return dateStr || "—";
    return d.toLocaleDateString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function renderDate(dateStr) {
    const el = document.getElementById("headerDate");
    if (!el) return;
    const d = dateStr ? new Date(dateStr) : new Date();
    const options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
    el.textContent = d.toLocaleDateString("ru-RU", options);
  }

  function renderSyncInfo(generatedAt, source) {
    const el = document.getElementById("syncInfo");
    if (!el) return;
    const ts = generatedAt ? toDateLabel(generatedAt) : "нет метки";
    const telegramTs = telegramData.meta?.generatedAt ? ` · Telegram: ${toDateLabel(telegramData.meta.generatedAt)}` : "";
    el.textContent = `Источник: ${source} · Обновлено: ${ts}${telegramTs}`;
  }

  function applyTheme(theme) {
    const body = document.body;
    if (!body) return;
    const normalized = theme === "dark" ? "dark" : "light";
    body.setAttribute("data-theme", normalized);
    localStorage.setItem("dashboardTheme", normalized);
    const toggle = document.getElementById("themeToggle");
    if (toggle) {
      toggle.textContent = normalized === "dark" ? "Тема: ночь" : "Тема: день";
    }
  }

  function initTheme() {
    let theme = localStorage.getItem("dashboardTheme");
    if (!theme) {
      theme = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    applyTheme(theme);
  }

  function switchPanel(panelId) {
    currentPanel = panelId;
    document.querySelectorAll(".dashboard-tab").forEach((button) => {
      button.classList.toggle("active", button.dataset.panel === panelId);
    });
    document.querySelectorAll(".dashboard-panel").forEach((panel) => {
      panel.classList.toggle("active", panel.id === panelId);
    });
  }

  function cleanupLegacySections() {
    const projectsPanel = document.getElementById("projectsPanel");
    if (projectsPanel) {
      const legacyFeedLayout = projectsPanel.querySelector(".feed-layout");
      if (legacyFeedLayout) {
        const title = legacyFeedLayout.previousElementSibling;
        if (title && title.classList.contains("section-title")) {
          title.remove();
        }
        legacyFeedLayout.remove();
      }
    }
    const consolidationEl = document.getElementById("consolidationSummary");
    if (consolidationEl) {
      const maybeSubtitle = consolidationEl.nextElementSibling;
      if (maybeSubtitle && maybeSubtitle.classList.contains("intel-subtitle")) {
        maybeSubtitle.remove();
      }
    }
  }

  function renderProjectGroupTabs() {
    const container = document.getElementById("projectGroupTabs");
    if (!container) return;
    const groups = projectGroupsData || [];
    if (!groups.length) {
      container.innerHTML = "";
      currentGroupFilter = "all";
      return;
    }
    if (currentGroupFilter !== "all" && !groups.some((group) => group.id === currentGroupFilter)) {
      currentGroupFilter = "all";
    }
    const allCount = projectsData.length;
    const items = [{ id: "all", title: "Все категории", projectCount: allCount }, ...groups];
    container.innerHTML = items
      .map(
        (item) => `
          <button type="button" class="group-tab${currentGroupFilter === item.id ? " active" : ""}" data-group="${item.id}">
            ${item.title} <span class="count">${item.projectCount || 0}</span>
          </button>
        `
      )
      .join("");
  }

  function buildProjectSubtitle(project) {
    const category = project.category || "Без категории";
    return project.originalTitle ? `${category} (${project.originalTitle})` : category;
  }

  function renderProtocolItems(targetId, items, mode) {
    const list = document.getElementById(targetId);
    if (!list) return;
    if (!items || !items.length) {
      list.innerHTML = '<div class="no-results">Нет данных</div>';
      return;
    }

    list.innerHTML = items
      .map((item) => {
        if (mode === "routing") {
          return `
            <div class="protocol-item">
              <div class="protocol-step">${item.when || ""}</div>
              <div class="protocol-detail"><strong>${item.route || ""}</strong>${item.action ? ` · ${item.action}` : ""}</div>
            </div>
          `;
        }
        return `
          <div class="protocol-item">
            <div class="protocol-step">${item.step || ""}</div>
            <div class="protocol-detail">${item.detail || ""}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderSimpleTextList(targetId, items) {
    const list = document.getElementById(targetId);
    if (!list) return;
    if (!items || !items.length) {
      list.innerHTML = '<div class="no-results">Нет данных</div>';
      return;
    }

    list.innerHTML = items
      .map(
        (item) => `
          <div class="protocol-item">
            <div class="protocol-detail">${item}</div>
          </div>
        `
      )
      .join("");
  }

  function renderSystemProfile() {
    const container = document.getElementById("systemProfileCard");
    if (!container) return;
    const profile = monitoringData.profile || {};
    const stats = monitoringData.stats || {};
    if (!profile.summary) {
      container.innerHTML = '<div class="no-results">Профиль интересов еще не собран</div>';
      return;
    }

    const roles = (profile.roles || []).slice(0, 6).map((item) => `<span class="tag">${item}</span>`).join("");
    const themes = (profile.focusThemes || []).slice(0, 6).map((item) => `<span class="tag">${item}</span>`).join("");
    const focus = (profile.currentFocusProjects || []).slice(0, 5).join(", ");
    const sources = (profile.sourceHighlights || []).slice(0, 5).join(", ");
    const cadence = (profile.reviewCadence || [])
      .map((item) => `${item.label}: ${item.value}`)
      .join(" · ");

    container.innerHTML = `
      <div class="feed-card intel-card">
        <div class="feed-top">
          <span class="feed-title">${profile.title || "Системная карта интересов"}</span>
          <span class="feed-pill neutral">${stats.activeProjects || 0} активных</span>
        </div>
        <div class="feed-desc">${profile.summary || ""}</div>
        <div class="card-tags">${roles}</div>
        <div class="card-tags">${themes}</div>
        <div class="feed-meta">${focus ? `Фокус: ${focus}` : "Фокус пока не определен"}</div>
        <div class="feed-meta">${sources ? `Источники: ${sources}` : "Источники появятся после sync"}</div>
        <div class="feed-bottom">
          <span>идей: ${stats.ideas || 0}</span>
          <span>источников: ${stats.trackedSources || 0}</span>
          <span>архив: ${(stats.archivedProjects || 0) + (stats.archivedChats || 0)}</span>
        </div>
        ${cadence ? `<div class="feed-meta">${cadence}</div>` : ""}
      </div>
    `;
  }

  // --- Signals (Supabase) ---

  async function loadSignals() {
    if (!supabaseClient) return;
    try {
      const { data, error } = await supabaseClient
        .from('signals')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(50);
      if (error) throw error;
      signalsData = data || [];
    } catch (err) {
      console.warn('Failed to load signals from Supabase:', err);
    }
  }

  function renderSignalCard(signal) {
    const routeLabels = {
      project_update: 'Проект', new_idea: 'Идея', skill_candidate: 'Навык',
      reference_note: 'Заметка', archive: 'Архив', pending: 'Входящее',
    };
    const routeColors = {
      project_update: '#34d399', new_idea: '#60a5fa', skill_candidate: '#f472b6',
      reference_note: '#a78bfa', archive: '#94a3b8', pending: '#fbbf24',
    };
    const typeIcons = {
      news: '📰', tool: '🔧', idea: '💡', pattern: '🔁', resource: '📦', event: '📅',
    };

    const route = signal.route || 'pending';
    const routeLabel = routeLabels[route] || route;
    const routeColor = routeColors[route] || '#94a3b8';
    const typeIcon = typeIcons[signal.signal_type] || '📋';
    const score = signal.relevance_score || 0;
    const tags = (signal.tags || []).slice(0, 4);
    const dateStr = signal.created_at
      ? new Date(signal.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
      : '';

    return `
      <div class="signal-card" data-signal-id="${signal.id}">
        <div class="signal-card-header">
          <span class="signal-route-badge" style="--route-color: ${routeColor}">${routeLabel}</span>
          <span class="signal-type">${typeIcon}</span>
          <span class="signal-date">${dateStr}</span>
        </div>
        <div class="signal-summary">${signal.summary || 'Без описания'}</div>
        ${signal.next_step ? `<div class="signal-next-step">→ ${signal.next_step}</div>` : ''}
        <div class="signal-footer">
          <div class="signal-tags">${tags.map(t => `<span class="signal-tag">${t}</span>`).join('')}</div>
          <div class="signal-relevance" title="Релевантность: ${score}%">
            <div class="signal-relevance-bar">
              <div class="signal-relevance-fill" style="width:${score}%; background: ${score >= 70 ? '#34d399' : score >= 40 ? '#fbbf24' : '#94a3b8'}"></div>
            </div>
            <span class="signal-score">${score}</span>
          </div>
        </div>
        ${signal.routed_to_project ? `<div class="signal-project">📌 ${signal.routed_to_project}</div>` : ''}
      </div>`;
  }

  function renderSignals() {
    const feed = document.getElementById('signalFeed');
    const badge = document.getElementById('signalCountBadge');
    if (!feed) return;

    const filtered = currentSignalFilter === 'all'
      ? signalsData
      : signalsData.filter(s => s.route === currentSignalFilter);

    if (badge) badge.textContent = signalsData.length ? `(${signalsData.length})` : '';

    if (!filtered.length) {
      feed.innerHTML = '<div class="no-results">Нет сигналов' +
        (currentSignalFilter !== 'all' ? ' в этой категории' : '') +
        '. Отправьте сообщение вашему Telegram-боту!</div>';
      return;
    }

    feed.innerHTML = filtered.map(renderSignalCard).join('');

    // Update overview counter
    renderOverview();
  }

  function subscribeToSignals() {
    if (!supabaseClient) return;
    try {
      supabaseClient
        .channel('signals-realtime')
        .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'signals' }, (payload) => {
          signalsData.unshift(payload.new);
          renderSignals();
        })
        .subscribe();
    } catch (err) {
      console.warn('Realtime subscription failed:', err);
    }
  }

  function getGroupScopedProjects() {
    if (currentGroupFilter === "all") return projectsData;
    return projectsData.filter((project) => project.groupId === currentGroupFilter);
  }

  function renderOverview() {
    const el = document.getElementById("overviewGrid");
    if (!el) return;

    const scopedProjects = getGroupScopedProjects();
    const projectsCount = currentGroupFilter === "all" ? dashboardStats.projects ?? projectsData.length : scopedProjects.length;
    const chatsCount = dashboardStats.chats ?? chatsData.length;
    const workflowsCount = dashboardStats.workflows ?? workflowsData.length;
    const activeCount =
      currentGroupFilter === "all"
        ? dashboardStats.activeProjects ??
        projectsData.filter((project) => String(project.status).toLowerCase() === "active").length
        : scopedProjects.filter((project) => String(project.status).toLowerCase() === "active").length;
    const missingCount =
      currentGroupFilter === "all"
        ? dashboardStats.missingProjects ??
        projectsData.filter((project) => String(project.migrationStatus || "").includes("missing")).length
        : scopedProjects.filter((project) => String(project.migrationStatus || "").includes("missing")).length;
    const telegramSources = telegramData.stats?.uniqueSources ?? 0;

    const cards = [
      { label: "Проекты", value: projectsCount },
      { label: "Активные", value: activeCount },
      { label: "Сигналы", value: signalsData.length, accent: true },
      { label: "Чаты", value: chatsCount },
      { label: "Workflows", value: workflowsCount },
      { label: "Telegram", value: telegramSources },
    ];

    el.innerHTML = cards
      .map(
        (card) => `
        <div class="overview-card">
          <div class="overview-value">${card.value}</div>
          <div class="overview-label">${card.label}</div>
        </div>
      `
      )
      .join("");
  }

  function renderStats() {
    const scoped = getGroupScopedProjects();
    const counts = { all: scoped.length };
    scoped.forEach((project) => {
      counts[project.status] = (counts[project.status] || 0) + 1;
    });

    const bar = document.getElementById("statsBar");
    if (!bar) return;

    const chips = [
      { key: "all", label: "Все", dotClass: "all-dot" },
      { key: "active", label: "В работе", dotClass: "active-dot" },
      { key: "research", label: "Исследование", dotClass: "research-dot" },
      { key: "paused", label: "Пауза", dotClass: "paused-dot" },
      { key: "backlog", label: "Бэклог", dotClass: "backlog-dot" },
      { key: "done", label: "Готово", dotClass: "done-dot" },
    ];

    bar.innerHTML = chips
      .map((chip) => {
        const count = counts[chip.key] || 0;
        if (chip.key !== "all" && count === 0) return "";
        const active = currentFilter === chip.key ? " active" : "";
        return `
          <button class="stat-chip${active}" data-filter="${chip.key}">
            <span class="stat-dot ${chip.dotClass}"></span>
            ${chip.label} <span class="count">${count}</span>
          </button>
        `;
      })
      .join("");
  }

  function getFilteredProjects() {
    const scoped = getGroupScopedProjects();
    return scoped.filter((project) => {
      const matchFilter = currentFilter === "all" || project.status === currentFilter;
      if (!searchQuery) return matchFilter;
      const q = searchQuery.toLowerCase();
      const haystack = [
        project.title,
        project.originalTitle,
        project.description,
        project.category,
        project.topic,
        ...(Array.isArray(project.tags) ? project.tags : []),
      ]
        .join(" ")
        .toLowerCase();
      return matchFilter && haystack.includes(q);
    });
  }

  function renderProjects() {
    const grid = document.getElementById("projectGrid");
    if (!grid) return;
    const filtered = getFilteredProjects();

    if (!filtered.length) {
      grid.innerHTML = '<div class="no-results">Проекты не найдены</div>';
      return;
    }

    grid.innerHTML = filtered
      .map((project) => {
        const tasksDone = Array.isArray(project.keyTasks) ? project.keyTasks.filter((task) => task.done).length : 0;
        const tasksTotal = Array.isArray(project.keyTasks) ? project.keyTasks.length : 0;
        const progressClass = project.progress >= 70 ? "high" : project.progress >= 30 ? "medium" : "low";
        const tagsHtml = (project.tags || []).slice(0, 5).map((tag) => `<span class="tag">${tag}</span>`).join("");
        const webLinks = (project.webLinks || [])
          .slice(0, 2)
          .map(
            (link) =>
              `<a class="project-link" href="${link.url}" target="_blank" rel="noopener noreferrer">${link.label || "Сайт проекта"}</a>`
          )
          .join("");
        return `
          <div class="project-card" data-id="${project.id}">
            <div class="card-header">
              <div>
                <div class="card-title">${project.title}</div>
                <div class="card-category">${buildProjectSubtitle(project)}</div>
              </div>
              <span class="status-badge status-${project.status}">${STATUS_LABELS[project.status] || project.status}</span>
            </div>
            <div class="card-desc">${project.description || ""}</div>
            ${webLinks ? `<div class="project-links">${webLinks}</div>` : ""}
            ${project.tasks
            ? `
              <div class="project-tasks">
                ${(project.tasks.todo || []).map(t => `<div class="task-todo">☐ ${t}</div>`).join('')}
                ${(project.tasks.done || []).map(t => `<div class="task-done">☑ ${t}</div>`).join('')}
              </div>
            `
            : ""
          }
            <div class="progress-container">
              <div class="progress-bar">
                <div class="progress-fill ${progressClass}" style="width:${project.progress || 0}%"></div>
              </div>
              <span class="progress-label">${project.progress || 0}%</span>
            </div>
            <div class="card-tags">${tagsHtml}</div>
            <div class="card-footer">
              <span class="card-tasks">☑ ${tasksDone}/${tasksTotal} задач</span>
              <span>${project.lastUpdated || "—"}</span>
            </div>
            <div class="card-footer card-meta-row">
              <span>💬 ${project.relatedChatsCount || 0}</span>
              <span>🔃 ${project.relatedWorkflowsCount || 0}</span>
              <span>${project.topic || ""}</span>
            </div>
          </div>
        `;
      })
      .join("");
  }

  function renderChats() {
    const list = document.getElementById("chatList");
    if (!list) return;
    if (!chatsData.length) {
      list.innerHTML = '<div class="no-results">Нет данных по чатам</div>';
      return;
    }

    list.innerHTML = chatsData
      .slice(0, 16)
      .map((chat) => {
        const statusClass = chat.recoveryStatus === "recovered" ? "ok" : "warn";
        return `
          <div class="feed-card">
            <div class="feed-top">
              <span class="feed-title">${chat.title || chat.id}</span>
              <span class="feed-pill ${statusClass}">${chat.recoveryStatus || "n/a"}</span>
            </div>
            <div class="feed-meta">${chat.date || "—"} · ${chat.theme || "Без темы"}</div>
            <div class="feed-desc">${chat.summary || ""}</div>
            <div class="feed-bottom">
              <span>ID: ${chat.id}</span>
              <span>Связей: ${(chat.relatedProjectIds || []).length}</span>
            </div>
          </div>
        `;
      })
      .join("");
  }

  function renderWorkflows() {
    const list = document.getElementById("workflowList");
    if (!list) return;
    if (!workflowsData.length) {
      list.innerHTML = '<div class="no-results">Нет данных по workflows</div>';
      return;
    }

    list.innerHTML = workflowsData
      .slice(0, 16)
      .map(
        (workflow) => `
          <div class="feed-card">
            <div class="feed-top">
              <span class="feed-title">${workflow.name}</span>
              <span class="feed-pill neutral">${(workflow.relatedProjectIds || []).length} проектов</span>
            </div>
            <div class="feed-meta">${workflow.source || "source: n/a"}</div>
            <div class="feed-desc">${workflow.notes || ""}</div>
            <div class="feed-bottom">
              <span>${workflow.path || "path: n/a"}</span>
            </div>
          </div>
        `
      )
      .join("");
  }

  function renderIdeas() {
    const grid = document.getElementById("ideasGrid");
    if (!grid) return;
    if (!ideasData.length) {
      grid.innerHTML = "";
      return;
    }

    grid.innerHTML = ideasData
      .map((idea) => {
        const tagsHtml = (idea.tags || []).slice(0, 3).map((tag) => `<span class="tag">${tag}</span>`).join("");
        return `
          <div class="idea-card" data-idea-id="${idea.id}">
            <div class="idea-card-header">
              <div class="idea-card-title">${idea.title}</div>
              <span class="priority-dot priority-${idea.priority}" title="${PRIORITY_LABELS[idea.priority] || ""} приоритет"></span>
            </div>
            ${idea.routeLabel ? `<div class="idea-route-line"><span class="route-pill">${idea.routeLabel}</span>${idea.themeLabel ? `<span>${idea.themeLabel}</span>` : ""}</div>` : ""}
            <div class="idea-card-desc">${idea.description}</div>
            ${idea.routingNextStep ? `<div class="idea-card-next">${idea.routingNextStep}</div>` : ""}
            <div class="idea-card-footer">
              <div class="card-tags">${tagsHtml}</div>
              ${idea.relatedProject ? `<span class="idea-related">→ ${idea.relatedProject}</span>` : ""}
            </div>
          </div>
        `;
      })
      .join("");
  }

  function renderUpgrades() {
    const grid = document.getElementById("upgradeGrid");
    if (!grid || !upgradePathsData.length) {
      if (grid) grid.innerHTML = "";
      return;
    }

    grid.innerHTML = upgradePathsData
      .map(
        (upgrade) => `
          <div class="upgrade-card">
            <div class="upgrade-card-title">⬆ ${upgrade.title}</div>
            <div class="upgrade-card-desc">${upgrade.description}</div>
            <div class="upgrade-meta">
              <span>⏱ ${upgrade.timeEstimate}</span>
              <span>🔧 ${upgrade.complexity}</span>
            </div>
          </div>
        `
      )
      .join("");
  }

  function renderTelegramSummary() {
    const container = document.getElementById("telegramSummary");
    if (!container) return;

    if (!telegramData.sources || !telegramData.sources.length) {
      container.innerHTML = '<div class="no-results">Telegram intelligence пока не сгенерирован</div>';
      return;
    }

    const summary = telegramData.summary || {};
    const stats = telegramData.stats || {};

    const cards = [
      { label: "Источники", value: stats.uniqueSources || telegramData.sources.length },
      { label: "Экспорты", value: stats.exportsScanned || 0 },
      { label: "Дубликаты", value: stats.duplicateExports || 0 },
      { label: "Сообщения", value: stats.messageCount || 0 },
    ];

    const recommendations = (summary.recommendations || []).slice(0, 3);
    const risks = (summary.risks || []).slice(0, 2);

    container.innerHTML = `
      <div class="intel-overview-grid">
        ${cards
        .map(
          (card) => `
              <div class="overview-card">
                <div class="overview-value">${card.value}</div>
                <div class="overview-label">${card.label}</div>
              </div>
            `
        )
        .join("")}
      </div>
      <div class="intel-note">${summary.overview || ""}</div>
      <div class="intel-text-block">
        <div class="intel-subtitle">Что делать дальше</div>
        ${recommendations.map((item) => `<div class="protocol-item"><strong>${item}</strong></div>`).join("")}
      </div>
      <div class="intel-text-block intel-risk-block">
        <div class="intel-subtitle">Риски процесса</div>
        ${risks.map((item) => `<div class="protocol-item">${item}</div>`).join("")}
      </div>
    `;
  }

  function renderTelegramSources() {
    const grid = document.getElementById("telegramSourceGrid");
    if (!grid) return;
    const sources = telegramData.sources || [];
    if (!sources.length) {
      grid.innerHTML = "";
      return;
    }

    grid.innerHTML = sources
      .slice(0, 8)
      .map((source) => {
        const tags = (source.topKeywords || []).slice(0, 4).map((tag) => `<span class="tag">${tag}</span>`).join("");
        return `
          <div class="feed-card intel-card">
            <div class="feed-top">
              <span class="feed-title">${source.title}</span>
              <span class="feed-pill neutral">${source.rankScore}/100</span>
            </div>
            <div class="feed-meta">${source.lifeAreaLabel} · ${source.themeLabel} · ${source.messageCount} сообщений</div>
            <div class="feed-desc">${source.summary}</div>
            <div class="card-tags">${tags}</div>
            <div class="feed-bottom">
              <span>${toDateLabel(source.lastDate)}</span>
              <span>дублей: ${source.duplicateCount || 0}</span>
            </div>
          </div>
        `;
      })
      .join("");
  }

  function renderTelegramAreas() {
    const grid = document.getElementById("telegramAreaGrid");
    if (!grid) return;
    const buckets = telegramData.areaBuckets || [];
    if (!buckets.length) {
      grid.innerHTML = '<div class="no-results">Нет распределения по зонам</div>';
      return;
    }

    grid.innerHTML = buckets
      .map(
        (bucket) => `
          <div class="intel-bucket-card">
            <div class="intel-bucket-top">
              <div class="intel-bucket-title">${bucket.label}</div>
              <div class="feed-pill neutral">${bucket.count}</div>
            </div>
            <div class="feed-meta">${(bucket.topThemes || []).join(" · ")}</div>
            <div class="feed-desc">${(bucket.sourceTitles || []).slice(0, 4).join(", ")}</div>
          </div>
        `
      )
      .join("");
  }

  function renderSuggestions(targetId, items, kind) {
    const grid = document.getElementById(targetId);
    if (!grid) return;
    if (!items || !items.length) {
      grid.innerHTML = '<div class="no-results">Нет предложений</div>';
      return;
    }

    grid.innerHTML = items
      .map((item) => {
        const meta = kind === "skill" ? (item.basedOn || []).slice(0, 3).join(", ") : `${item.category || ""}`;
        const badge = kind === "skill" ? item.code || item.id || "skill" : meta || "project";
        return `
          <div class="feed-card intel-card">
            <div class="feed-top">
              <span class="feed-title">${item.title}</span>
              <span class="feed-pill neutral">${badge}</span>
            </div>
            <div class="feed-desc">${item.summary || ""}</div>
            <div class="feed-meta">${item.why || meta || ""}</div>
          </div>
        `;
      })
      .join("");
  }

  function renderProtocol() {
    const list = document.getElementById("processingProtocolList");
    if (!list) return;
    const steps = telegramData.processingProtocol || [];
    if (!steps.length) {
      list.innerHTML = '<div class="no-results">Нет протокола</div>';
      return;
    }

    list.innerHTML = steps
      .map(
        (item) => `
          <div class="protocol-item">
            <div class="protocol-step">${item.step}</div>
            <div class="protocol-detail">${item.detail}</div>
          </div>
        `
      )
      .join("");
  }

  function renderTelegramIntel() {
    renderTelegramSummary();
    renderTelegramSources();
    renderTelegramAreas();
    renderSuggestions("skillSuggestionGrid", telegramData.skillSuggestions || [], "skill");
    renderSuggestions("projectSuggestionGrid", telegramData.projectSuggestions || [], "project");
    renderProtocol();
  }

  function renderMonitoringIntel() {
    renderSystemProfile();
    renderProtocolItems("systemProtocolList", monitoringData.processingProtocol || [], "protocol");
    renderProtocolItems("systemRoutingList", monitoringData.routingRules || [], "routing");
    renderSuggestions("monitorSkillGrid", monitoringData.skillSuggestions || [], "skill");
    renderSuggestions("monitorProjectGrid", monitoringData.projectSuggestions || [], "project");
    renderSimpleTextList("monitorRecommendationList", monitoringData.recommendations || []);
  }

  function renderProjectGroupsAndArchive() {
    const groupGrid = document.getElementById("projectGroupGrid");
    const consolidationEl = document.getElementById("consolidationSummary");
    const archiveList = null;

    if (groupGrid) {
      if (!projectGroupsData.length) {
        groupGrid.innerHTML = '<div class="no-results">Группы пока не собраны</div>';
      } else {
        groupGrid.innerHTML = projectGroupsData
          .map(
            (group) => `
              <div class="feed-card intel-card">
                <div class="feed-top">
                  <span class="feed-title">${group.title}</span>
                  <span class="feed-pill neutral">${group.projectCount || 0}</span>
                </div>
                <div class="feed-meta">Активных: ${group.activeProjects || 0} · Исследование: ${group.researchProjects || 0}</div>
                <div class="feed-desc">${(group.projectTitles || []).slice(0, 4).join(", ")}</div>
              </div>
            `
          )
          .join("");
      }
    }

    if (consolidationEl) {
      const cards = [
        { label: "Архив проектов", value: consolidationData.archivedProjects || 0 },
        { label: "Архив чатов", value: consolidationData.archivedChats || 0 },
        { label: "Merge проектов", value: consolidationData.projectMerges || 0 },
        { label: "Merge чатов", value: consolidationData.chatMerges || 0 },
      ];
      consolidationEl.innerHTML = `
        <div class="intel-overview-grid">
          ${cards
          .map(
            (card) => `
                <div class="overview-card">
                  <div class="overview-value">${card.value}</div>
                  <div class="overview-label">${card.label}</div>
                </div>
              `
          )
          .join("")}
        </div>
      `;
      const metricCards = consolidationEl.querySelectorAll(".overview-card");
      if (metricCards.length >= 4) {
        metricCards[0].remove();
        metricCards[1].remove();
      }
    }

    if (false) {
      if (!archivesData.length) {
        archiveList.innerHTML = '<div class="no-results">Архив пуст</div>';
      } else {
        archiveList.innerHTML = archivesData
          .slice(0, 24)
          .map(
            (item) => `
              <div class="protocol-item">
                <div class="protocol-step">[${item.kind || "source"}] ${item.title || item.id || "source"}</div>
                <div class="protocol-detail">${item.reason || ""}${item.mergedInto ? ` → ${item.mergedInto}` : ""}</div>
              </div>
            `
          )
          .join("");
      }
    }
  }

  function renderIdeaRouter() {
    const summaryEl = document.getElementById("ideaRouterSummary");
    const queueEl = document.getElementById("ideaRouterQueue");
    const clusterEl = document.getElementById("ideaRouterClusterGrid");
    const summary = ideaRouterData.summary || {};
    const queue = ideaRouterData.queue || [];
    const clusters = ideaRouterData.clusters || [];

    if (summaryEl) {
      if (!summary.totalIdeas) {
        summaryEl.innerHTML = '<div class="no-results">Idea router пока не собран</div>';
      } else {
        const cards = [
          { label: "Идей", value: summary.totalIdeas || 0 },
          { label: "Проект", value: summary.routedToProject || 0 },
          { label: "Skills", value: summary.skillCandidates || 0 },
          { label: "Гипотезы", value: summary.projectHypotheses || 0 },
          { label: "Заметки", value: summary.referenceNotes || 0 },
          { label: "Архив", value: summary.archiveItems || 0 },
        ];
        summaryEl.innerHTML = `
          <div class="intel-overview-grid">
            ${cards
            .map(
              (card) => `
                  <div class="overview-card">
                    <div class="overview-value">${card.value}</div>
                    <div class="overview-label">${card.label}</div>
                  </div>
                `
            )
            .join("")}
          </div>
        `;
      }
    }

    if (queueEl) {
      if (!queue.length) {
        queueEl.innerHTML = '<div class="no-results">Очередь пока пуста</div>';
      } else {
        queueEl.innerHTML = queue
          .map(
            (item) => `
              <div class="protocol-item idea-route-item">
                <div class="protocol-step">${item.title}</div>
                <div class="protocol-detail">
                  <span class="route-pill">${item.routeLabel}</span>
                  ${item.relatedProject ? `<strong>→ ${item.relatedProject}</strong> · ` : ""}
                  ${item.reason}
                </div>
                <div class="route-next-step">${item.nextStep || ""}</div>
              </div>
            `
          )
          .join("");
      }
    }

    if (clusterEl) {
      if (!clusters.length) {
        clusterEl.innerHTML = '<div class="no-results">Нет кластеров идей</div>';
      } else {
        clusterEl.innerHTML = clusters
          .map(
            (cluster) => `
              <div class="feed-card intel-card idea-cluster-card">
                <div class="feed-top">
                  <span class="feed-title">${cluster.title}</span>
                  <span class="feed-pill neutral">${cluster.ideaCount}</span>
                </div>
                <div class="feed-meta">${cluster.lifeAreaLabel || "—"} · ${cluster.themeLabel || "—"}</div>
                <div class="feed-desc">${cluster.summary || ""}</div>
                <div class="card-tags">${(cluster.topTags || []).slice(0, 4).map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
                <div class="feed-bottom">
                  <span>${cluster.routeBiasLabel || ""}</span>
                  <span>${cluster.nextStep || ""}</span>
                </div>
              </div>
            `
          )
          .join("");
      }
    }
  }

  function openProjectModal(projectId) {
    const project = projectsData.find((item) => item.id === projectId);
    if (!project) return;

    document.getElementById("modalTitle").textContent = project.title;
    document.getElementById("modalCategory").textContent = `${buildProjectSubtitle(project)} · ${project.topic || ""}`;
    document.getElementById("modalStatus").textContent = STATUS_LABELS[project.status] || project.status;
    document.getElementById("modalStatus").className = "status-badge status-" + project.status;
    document.getElementById("modalDesc").textContent = project.description || "";
    document.getElementById("modalProgress").style.width = (project.progress || 0) + "%";
    document.getElementById("modalProgress").className =
      "progress-fill " + ((project.progress || 0) >= 70 ? "high" : (project.progress || 0) >= 30 ? "medium" : "low");
    document.getElementById("modalProgressLabel").textContent = (project.progress || 0) + "%";

    const taskList = document.getElementById("modalTasks");
    if (project.keyTasks && project.keyTasks.length > 0) {
      taskList.innerHTML = project.keyTasks
        .map(
          (task) => `
            <li class="task-item">
              <span class="task-check ${task.done ? "checked" : ""}">${task.done ? "✓" : ""}</span>
              <span class="task-text ${task.done ? "done-task" : ""}">${task.task}</span>
            </li>
          `
        )
        .join("");
    } else {
      taskList.innerHTML = '<li class="task-item" style="color:var(--text-muted)">Нет задач</li>';
    }

    const notesEl = document.getElementById("modalNotes");
    const fullNotes = [project.notes, project.sourcePath ? `Source: ${project.sourcePath}` : "", project.destinationPath ? `Destination: ${project.destinationPath}` : ""]
      .filter(Boolean)
      .join("\n");
    if (fullNotes) {
      notesEl.textContent = fullNotes;
      document.getElementById("modalNotesWrap").style.display = "";
    } else {
      document.getElementById("modalNotesWrap").style.display = "none";
    }

    document.getElementById("modalTags").innerHTML = (project.tags || []).map((tag) => `<span class="tag">${tag}</span>`).join("");
    document.getElementById("modalOverlay").classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeProjectModal() {
    document.getElementById("modalOverlay").classList.remove("open");
    document.body.style.overflow = "";
  }

  function openIdeaModal(ideaId) {
    const idea = ideasData.find((item) => item.id === ideaId);
    if (!idea) return;

    document.getElementById("ideaModalTitle").textContent = "💡 " + idea.title;
    document.getElementById("ideaModalDesc").textContent = [idea.description, idea.routingNextStep].filter(Boolean).join(" ");
    document.getElementById("ideaModalTags").innerHTML = (idea.tags || []).map((tag) => `<span class="tag">${tag}</span>`).join("");
    document.getElementById("ideaModalDate").textContent = "Добавлено: " + (idea.addedDate || "—");

    const related = document.getElementById("ideaModalRelated");
    const routeBits = [];
    if (idea.routeLabel) routeBits.push("<strong>Исход:</strong> " + idea.routeLabel);
    if (idea.relatedProject) routeBits.push("<strong>Связанный проект:</strong> " + idea.relatedProject);
    if (idea.lifeAreaLabel || idea.themeLabel) {
      routeBits.push("<strong>Контур:</strong> " + [idea.lifeAreaLabel, idea.themeLabel].filter(Boolean).join(" / "));
    }
    if (idea.routingReason) routeBits.push(idea.routingReason);
    if (routeBits.length) {
      related.innerHTML = "<strong>Связанный проект:</strong> " + idea.relatedProject;
      related.innerHTML = routeBits.join("<br>");
      related.style.display = "";
    } else {
      related.style.display = "none";
    }

    document.getElementById("ideaModalOverlay").classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeIdeaModal() {
    document.getElementById("ideaModalOverlay").classList.remove("open");
    document.body.style.overflow = "";
  }

  function bindEvents() {
    const statsBar = document.getElementById("statsBar");
    if (statsBar) {
      statsBar.addEventListener("click", function (event) {
        const chip = event.target.closest(".stat-chip");
        if (!chip) return;
        currentFilter = chip.dataset.filter;
        renderStats();
        renderOverview();
        renderProjects();
      });
    }

    const searchInput = document.getElementById("searchInput");
    if (searchInput) {
      searchInput.addEventListener("input", function (event) {
        searchQuery = event.target.value.trim();
        renderProjects();
      });
    }

    const groupTabs = document.getElementById("projectGroupTabs");
    if (groupTabs) {
      groupTabs.addEventListener("click", function (event) {
        const tab = event.target.closest(".group-tab");
        if (!tab) return;
        currentGroupFilter = tab.dataset.group || "all";
        renderProjectGroupTabs();
        renderOverview();
        renderStats();
        renderProjects();
      });
    }

    const mainTabs = document.getElementById("mainTabs");
    if (mainTabs) {
      mainTabs.addEventListener("click", function (event) {
        const tab = event.target.closest(".dashboard-tab");
        if (!tab) return;
        switchPanel(tab.dataset.panel);
      });
    }

    const themeToggle = document.getElementById("themeToggle");
    if (themeToggle) {
      themeToggle.addEventListener("click", function () {
        const current = document.body.getAttribute("data-theme") || "light";
        applyTheme(current === "dark" ? "light" : "dark");
      });
    }

    const projectGrid = document.getElementById("projectGrid");
    if (projectGrid) {
      projectGrid.addEventListener("click", function (event) {
        const card = event.target.closest(".project-card");
        if (!card) return;
        openProjectModal(card.dataset.id);
      });
    }

    const ideasGrid = document.getElementById("ideasGrid");
    if (ideasGrid) {
      ideasGrid.addEventListener("click", function (event) {
        const card = event.target.closest(".idea-card");
        if (!card) return;
        openIdeaModal(card.dataset.ideaId);
      });
    }

    const modalClose = document.getElementById("modalClose");
    const modalOverlay = document.getElementById("modalOverlay");
    if (modalClose) modalClose.addEventListener("click", closeProjectModal);
    if (modalOverlay) {
      modalOverlay.addEventListener("click", function (event) {
        if (event.target === this) closeProjectModal();
      });
    }

    const ideaModalClose = document.getElementById("ideaModalClose");
    const ideaModalOverlay = document.getElementById("ideaModalOverlay");
    if (ideaModalClose) ideaModalClose.addEventListener("click", closeIdeaModal);
    if (ideaModalOverlay) {
      ideaModalOverlay.addEventListener("click", function (event) {
        if (event.target === this) closeIdeaModal();
      });
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeProjectModal();
        closeIdeaModal();
      }
    });

    // Signal filter buttons
    const signalFilters = document.getElementById('signalFilters');
    if (signalFilters) {
      signalFilters.addEventListener('click', function (event) {
        const btn = event.target.closest('.signal-filter');
        if (!btn) return;
        currentSignalFilter = btn.dataset.route;
        signalFilters.querySelectorAll('.signal-filter').forEach(b => b.classList.toggle('active', b === btn));
        renderSignals();
      });
    }
  }

  async function init() {
    try {
      renderFileProtocolHint();
      const [{ data, source }, optionalTelegram, optionalIdeaInbox] = await Promise.all([
        loadDashboardData(),
        loadOptionalJson("data/telegram_intelligence.json"),
        loadFirstOptionalJson(["/api/idea-inbox", "data/idea_inbox.json"]),
      ]);

      projectsData = data.projects || [];
      upgradePathsData = data.upgradePaths || [];
      ideasData = mergeIdeas(data.ideas || [], optionalIdeaInbox);
      chatsData = data.chats || [];
      workflowsData = data.workflows || [];
      dashboardStats = data.stats || {};
      monitoringData = data.monitoring || monitoringData;
      projectGroupsData = data.projectGroups || monitoringData.projectGroups || [];
      consolidationData = data.consolidation || monitoringData.consolidation || {};
      ideaRouterData = data.ideaRouter || ideaRouterData;
      if (optionalTelegram) {
        telegramData = optionalTelegram;
      }

      initTheme();
      cleanupLegacySections();
      renderDate(data.meta?.lastUpdated);
      renderSyncInfo(data.meta?.generatedAt, source);
      renderProjectGroupTabs();
      renderOverview();
      renderStats();
      renderProjects();
      renderTelegramIntel();
      renderMonitoringIntel();
      renderProjectGroupsAndArchive();
      renderIdeaRouter();
      renderIdeas();
      renderUpgrades();
      switchPanel(currentPanel);
      bindEvents();

      // Load signals from Supabase
      await loadSignals();
      renderSignals();
      subscribeToSignals();
    } catch (err) {
      console.error("Load error:", err);
      const grid = document.getElementById("projectGrid");
      if (grid) {
        if (isFileProtocol()) {
          grid.innerHTML =
            '<div class="no-results no-results--error">Дашборд открыт как <code>file://</code>, поэтому браузер блокирует загрузку <code>data/*.json</code>.<br>Запустите локальный сервер и откройте <code>http://127.0.0.1:8891/index.html</code>:<br><code>python scripts/dashboard/dashboard_server.py --port 8891</code></div>';
        } else {
          grid.innerHTML =
            '<div class="no-results no-results--error">Ошибка загрузки данных. Проверьте наличие и валидность <code>data/dashboard_data.json</code> и <code>data/telegram_intelligence.json</code>. Для стабильной работы открывайте дашборд через локальный сервер: <code>python scripts/dashboard/dashboard_server.py --port 8891</code></div>';
        }
      }
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
