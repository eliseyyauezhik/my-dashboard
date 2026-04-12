(function () {
  "use strict";

  // === State ===
  let projectsData = [];
  let ideasData = [];
  let goalsData = [];
  let notesData = [];
  let signalsData = [];
  let projectRegistryData = [];
  let projectRegistryMap = new Map();
  let projectGroupsData = [];
  let projectRelationsData = [];
  let monitoringData = {
    profile: {},
    routingRules: [],
    recommendations: [],
    skillSuggestions: [],
    projectSuggestions: [],
  };
  let currentPanel = "overviewPanel";
  let currentProjectArea = "all";
  let currentSignalFilter = "all";
  let currentIdeaPriority = "all";
  let searchQuery = "";

  // --- Supabase Client ---
  let supabaseClient = null;

  function initSupabase() {
    if (typeof window.DASHBOARD_CONFIG === "undefined") {
      console.warn("DASHBOARD_CONFIG not found — Supabase disabled");
      return;
    }
    if (typeof supabase === "undefined" || !supabase.createClient) {
      console.warn("Supabase SDK not loaded");
      return;
    }
    try {
      supabaseClient = supabase.createClient(
        window.DASHBOARD_CONFIG.SUPABASE_URL,
        window.DASHBOARD_CONFIG.SUPABASE_KEY
      );
      console.log("✓ Supabase client ready");
    } catch (e) {
      console.error("Supabase init error:", e);
    }
  }

  const STATUS_LABELS = {
    active: "В работе",
    paused: "Пауза",
    research: "Исследование",
    backlog: "Бэклог",
    done: "Готово",
  };

  const STATUS_COLORS = {
    active: "#22c55e",
    paused: "#f59e0b",
    research: "#8b5cf6",
    backlog: "#64748b",
    done: "#06b6d4",
  };

  const PRIORITY_LABELS = { high: "🔥 Высокий", medium: "⚡ Средний", low: "💤 Низкий" };

  const GROUP_ICONS = {
    "news-aggregators": "📡",
    "idea-generators": "💡",
    "ai-system-growth": "🧠",
    "ai-agents": "🤖",
    "work-projects": "🏫",
  };

  // === Theme ===
  function applyTheme(theme) {
    document.body.setAttribute("data-theme", theme);
    localStorage.setItem("dashboard-theme", theme);
    const btn = document.getElementById("themeToggle");
    if (btn) btn.textContent = theme === "dark" ? "Тема: ночь" : "Тема: день";
  }

  function initTheme() {
    const saved = localStorage.getItem("dashboard-theme");
    const prefer = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    applyTheme(saved || prefer);
  }

  // === Tab Switching ===
  function switchPanel(panelId) {
    currentPanel = panelId;
    document.querySelectorAll(".dashboard-panel").forEach((p) => p.classList.remove("active"));
    document.querySelectorAll(".dashboard-tab").forEach((t) => t.classList.remove("active"));
    const panel = document.getElementById(panelId);
    if (panel) panel.classList.add("active");
    const tab = document.querySelector(`[data-panel="${panelId}"]`);
    if (tab) tab.classList.add("active");
  }

  // === Data Loading ===
  async function loadOptionalJson(source) {
    try {
      const r = await fetch(source, { cache: "no-store" });
      if (!r.ok) return null;
      return await r.json();
    } catch { return null; }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function normalizeTask(task) {
    if (typeof task === "string") return { task, done: false };
    if (!task || typeof task !== "object") return null;
    const text = task.task || task.text || "";
    if (!text) return null;
    return { task: text, done: Boolean(task.done) };
  }

  function getProjectTasks(project) {
    const source = Array.isArray(project?.keyTasks)
      ? project.keyTasks
      : Array.isArray(project?.tasks)
        ? project.tasks
        : [];
    return source.map(normalizeTask).filter(Boolean);
  }

  function getProjectNextStep(project) {
    const pending = getProjectTasks(project).find((item) => !item.done);
    if (pending?.task) return pending.task;
    return project?.projectMode?.nextStep || "Проверить текущий контекст проекта и выбрать следующий шаг.";
  }

  function setProjectRegistry(registryPayload) {
    projectRegistryData = Array.isArray(registryPayload?.projects) ? registryPayload.projects : [];
    projectRegistryMap = new Map(projectRegistryData.map((item) => [item.id, item]));
  }

  function mergeProjectWithRegistry(project) {
    const registry = projectRegistryMap.get(project.id);
    const merged = { ...project };
    if (registry) {
      merged.title = registry.title || merged.title;
      merged.status = registry.status || merged.status;
      merged.topic = registry.topic || merged.topic;
      merged.kbNote = registry.kbNote || merged.kbNote || null;
      merged.relatedChats = registry.relatedChats || merged.relatedChats || [];
      merged.relatedWorkflows = registry.relatedWorkflows || merged.relatedWorkflows || [];
      merged.projectMode = registry.projectMode || merged.projectMode || {};
      merged.launchContract = registry.launchContract || merged.launchContract || {};
    }
    merged.keyTasks = getProjectTasks(merged);
    return merged;
  }

  function applyProjectRegistry() {
    projectsData = (projectsData || []).map(mergeProjectWithRegistry);
  }

  async function copyText(text) {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      window.prompt("Скопируйте текст вручную:", text);
    }
  }

  function renderRegistryLinks(items, emptyLabel) {
    if (!Array.isArray(items) || items.length === 0) {
      return `<li><i>${emptyLabel}</i></li>`;
    }
    return items
      .slice(0, 8)
      .map((item) => {
        const title = escapeHtml(item.title || item.id || "Без названия");
        if (item.obsidianUri) {
          return `<li><a href="${escapeHtml(item.obsidianUri)}" target="_self">${title}</a></li>`;
        }
        return `<li>${title}</li>`;
      })
      .join("");
  }

  async function loadDashboardData() {
    const data = await loadOptionalJson("projects.json");
    if (!data) return;
    const registry = await loadOptionalJson("data/project_registry.json");
    setProjectRegistry(registry || data.projectRegistry || { projects: [] });
    projectsData = data.projects || [];
    applyProjectRegistry();
    projectGroupsData = data.projectGroups || [];

    // Monitoring & intelligence
    const m = data.monitoring || {};
    monitoringData.profile = m.profile || {};
    monitoringData.routingRules = m.routingRules || [];
    monitoringData.recommendations = m.recommendations || [];
    monitoringData.skillSuggestions = m.skillSuggestions || [];
    monitoringData.projectSuggestions = m.projectSuggestions || [];
  }

  // === Load from Supabase ===
  async function loadFromSupabase() {
    if (!supabaseClient) return;

    try {
      const results = await Promise.all([
        supabaseClient.from("projects").select("*").order("title"),
        supabaseClient.from("ideas").select("*").order("relevance_score", { ascending: false }),
        supabaseClient.from("goals").select("*"),
        supabaseClient.from("notes").select("*").order("created_at", { ascending: false }),
        supabaseClient.from("signals").select("*").order("created_at", { ascending: false }).limit(50),
        supabaseClient.from("project_relations").select("*")
      ]);

      const [sProj, sIdeas, sGoals, sNotes, sSignals, sRels] = results.map(r => r.data || null);

      if (sProj) projectsData = sProj;
      if (sIdeas) ideasData = sIdeas;
      if (sGoals) goalsData = sGoals;
      if (sNotes) notesData = sNotes;
      if (sSignals) signalsData = sSignals;
      if (sRels) projectRelationsData = sRels;
      applyProjectRegistry();
    } catch (err) {
      console.error("Error loading from Supabase:", err);
    }
  }

  // === Subscribe to Realtime ===
  function subscribeToSignals() {
    if (!supabaseClient) return;
    supabaseClient
      .channel("signals-realtime")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "signals" }, (payload) => {
        signalsData.unshift(payload.new);
        renderSignals();
        updateInboxBadge();
      })
      .subscribe();
  }

  // ============================================================
  //  OVERVIEW TAB
  // ============================================================
  function renderOverviewStats() {
    const el = document.getElementById("overviewStats");
    if (!el) return;

    const active = projectsData.filter((p) => p.status === "active").length;
    const total = projectsData.length;
    const ideasCount = ideasData.length;
    const signalsCount = signalsData.length;

    el.innerHTML = `
      <div class="stat-card"><div class="stat-value">${active}</div><div class="stat-label">Активных проектов</div></div>
      <div class="stat-card"><div class="stat-value">${total}</div><div class="stat-label">Всего проектов</div></div>
      <div class="stat-card"><div class="stat-value">${ideasCount}</div><div class="stat-label">Идей</div></div>
      <div class="stat-card"><div class="stat-value">${signalsCount}</div><div class="stat-label">Сигналов</div></div>
      <div class="stat-card"><div class="stat-value">${goalsData.length}</div><div class="stat-label">Целей</div></div>
    `;
  }

  // === Mind Map (SVG Graph) ===
  function renderMindMap() {
    const svg = document.getElementById("mindMapSvg");
    if (!svg) return;

    const container = document.getElementById("mindMapContainer");
    const width = container.clientWidth || 900;
    const height = 500;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.innerHTML = "";

    // 1. Build Node Map
    const nodeMap = new Map();
    // Add central node
    nodeMap.set("root", { id: "root", title: "Digital Twin", type: "root", x: width / 2, y: height / 2 });

    // Fallback: If no relations loaded yet, we build pseudo-relations based on groups
    const effectiveRelations = projectRelationsData.length > 0 ? projectRelationsData : projectsData.map(p => ({
      from_id: p.id,
      to_id: p.group_id ? `group-${p.group_id}` : "root",
      relation: "part_of"
    }));

    // Add projects
    projectsData.forEach(p => {
      nodeMap.set(p.id, {
        id: p.id, title: p.title, type: "project", status: p.status,
        x: width / 2 + (Math.random() - 0.5) * 100, y: height / 2 + (Math.random() - 0.5) * 100
      });
    });

    // Add groups if we are using fallback
    if (projectRelationsData.length === 0) {
      const groups = new Set(projectsData.map(p => p.group_id).filter(Boolean));
      groups.forEach(gid => {
        const groupTitle = projectsData.find(p => p.group_id === gid)?.group_title || gid;
        nodeMap.set(`group-${gid}`, { id: `group-${gid}`, title: groupTitle, type: "group", x: width / 2, y: height / 2 });
        effectiveRelations.push({ from_id: `group-${gid}`, to_id: "root", relation: "part_of" });
      });
    } else {
      // Connect isolated projects to root
      const connectedNodes = new Set();
      effectiveRelations.forEach(r => { connectedNodes.add(r.from_id); connectedNodes.add(r.to_id); });
      projectsData.forEach(p => {
        if (!connectedNodes.has(p.id)) {
          effectiveRelations.push({ from_id: p.id, to_id: "root", relation: "related" });
        }
      });
    }

    // 2. Simple Force Layout Simulation (Iterative)
    const nodes = Array.from(nodeMap.values());
    const edges = effectiveRelations.filter(r => nodeMap.has(r.from_id) && nodeMap.has(r.to_id)).map(r => ({
      source: nodeMap.get(r.from_id),
      target: nodeMap.get(r.to_id)
    }));

    // Fix root
    const root = nodeMap.get("root");
    root.x = width / 2;
    root.y = height / 2;

    const iterations = 100;
    const k = Math.sqrt((width * height) / nodes.length); // optimal distance

    for (let i = 0; i < iterations; i++) {
      // Repulsion
      for (let a = 0; a < nodes.length; a++) {
        for (let b = a + 1; b < nodes.length; b++) {
          let dx = nodes[a].x - nodes[b].x;
          let dy = nodes[a].y - nodes[b].y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < k * 2) {
            let force = (k * k) / dist;
            let fx = (dx / dist) * force;
            let fy = (dy / dist) * force;
            if (nodes[a] !== root) { nodes[a].x += fx * 0.1; nodes[a].y += fy * 0.1; }
            if (nodes[b] !== root) { nodes[b].x -= fx * 0.1; nodes[b].y -= fy * 0.1; }
          }
        }
      }

      // Attraction
      edges.forEach(e => {
        let dx = e.source.x - e.target.x;
        let dy = e.source.y - e.target.y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        let force = (dist * dist) / k;
        let fx = (dx / dist) * force;
        let fy = (dy / dist) * force;
        if (e.source !== root) { e.source.x -= fx * 0.05; e.source.y -= fy * 0.05; }
        if (e.target !== root) { e.target.x += fx * 0.05; e.target.y += fy * 0.05; }
      });

      // Center gravity
      nodes.forEach(n => {
        if (n !== root) {
          n.x += (width / 2 - n.x) * 0.02;
          n.y += (height / 2 - n.y) * 0.02;
        }
      });
    }

    // 3. Render
    edges.forEach(e => addLine(svg, e.source.x, e.source.y, e.target.x, e.target.y, "var(--border)"));
    nodes.forEach(n => {
      if (n.type === "root") {
        addNode(svg, n.x, n.y, n.title, 14, "var(--accent)", "#fff", 24);
      } else if (n.type === "group") {
        addNode(svg, n.x, n.y, n.title, 10, "var(--bg-card)", "var(--text-primary)", 18);
      } else {
        const color = STATUS_COLORS[n.status] || "#64748b";
        addLeafNode(svg, n.x, n.y, n.title, 8, color, n.id);
      }
    });
  }

  function addLine(svg, x1, y1, x2, y2, color) {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x1); line.setAttribute("y1", y1);
    line.setAttribute("x2", x2); line.setAttribute("y2", y2);
    line.setAttribute("stroke", color);
    line.setAttribute("stroke-width", "2.5");
    line.setAttribute("opacity", "0.7");
    svg.appendChild(line);
  }

  function addNode(svg, x, y, label, fontSize, bg, textColor, r) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${x}, ${y})`);

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("r", r);
    circle.setAttribute("fill", bg);
    circle.setAttribute("stroke", "var(--border)");
    circle.setAttribute("stroke-width", "1.5");
    g.appendChild(circle);

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dy", r + 16);
    text.setAttribute("fill", textColor);
    text.setAttribute("font-size", fontSize);
    text.setAttribute("font-family", "var(--font)");
    text.textContent = label.length > 25 ? label.substring(0, 23) + "…" : label;
    g.appendChild(text);

    svg.appendChild(g);
  }

  function addLeafNode(svg, x, y, label, fontSize, color, projectId) {
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${x}, ${y})`);
    g.style.cursor = "pointer";
    g.addEventListener("click", () => openProjectModal(projectId));

    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("r", 6);
    circle.setAttribute("fill", color);
    circle.setAttribute("stroke", "#fff");
    circle.setAttribute("stroke-width", "1");
    g.appendChild(circle);

    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("dy", 18);
    text.setAttribute("fill", "var(--text-secondary)");
    text.setAttribute("font-size", fontSize);
    text.setAttribute("font-family", "var(--font)");
    text.textContent = label.length > 20 ? label.substring(0, 18) + "…" : label;
    g.appendChild(text);

    svg.appendChild(g);
  }

  // ============================================================
  //  PROJECTS TAB (Accordion)
  // ============================================================
  function renderProjectAccordion() {
    const container = document.getElementById("projectAccordion");
    if (!container) return;

    // Group projects
    const groups = {};
    const ungrouped = [];
    for (const p of projectsData) {
      if (currentProjectArea !== "all" && p.life_area !== currentProjectArea) continue;
      if (searchQuery && !p.title.toLowerCase().includes(searchQuery)) continue;
      if (p.group_id) {
        if (!groups[p.group_id]) groups[p.group_id] = { title: p.group_title || p.group_id, projects: [] };
        groups[p.group_id].projects.push(p);
      } else {
        ungrouped.push(p);
      }
    }

    const safeTitle = (t) => t.replace(/["()]/g, '');

    let html = "";
    for (const [gid, g] of Object.entries(groups)) {
      const icon = GROUP_ICONS[gid] || "📂";
      const activeCount = g.projects.filter((p) => p.status === "active").length;

      // Build group specific schema
      let groupSchemaHtml = "";
      const groupProjIds = new Set(g.projects.map(p => p.id));
      const internalRelations = projectRelationsData.filter(r => groupProjIds.has(r.from_id) && groupProjIds.has(r.to_id));

      if (internalRelations.length > 0) {
        let mermaidStr = "graph LR\n";
        internalRelations.forEach(r => {
          const fTitle = g.projects.find(x => x.id === r.from_id)?.title || r.from_id;
          const tTitle = g.projects.find(x => x.id === r.to_id)?.title || r.to_id;
          const relLabel = RELATION_LABELS[r.relation] || r.relation;
          mermaidStr += `  ID_${r.from_id}["${safeTitle(fTitle)}"] -->|${relLabel}| ID_${r.to_id}["${safeTitle(tTitle)}"]\n`;
        });

        groupSchemaHtml = `
          <div class="group-schema-container" style="background:var(--bg); border-bottom:1px solid var(--border-light); padding:16px; margin-bottom:12px;">
            <div style="font-size:0.85rem; font-weight:600; color:var(--text-secondary); margin-bottom:12px;">Внутренняя архитектура группы (исключение дублирования):</div>
            <div class="mermaid">${mermaidStr}</div>
          </div>
        `;
      } else {
        // Create a simple loose nodes schema if $>1 projects feature no specific relations yet
        if (g.projects.length > 1) {
          let mermaidStr = "graph LR\n";
          g.projects.forEach(p => { mermaidStr += `  ID_${p.id}["${safeTitle(p.title)}"]\n`; });
          groupSchemaHtml = `
              <div class="group-schema-container" style="background:var(--bg); border-bottom:1px solid var(--border-light); padding:16px; margin-bottom:12px;">
                <div style="font-size:0.85rem; font-weight:600; color:var(--text-secondary); margin-bottom:12px;">Состав группы (связи не заданы):</div>
                <div class="mermaid">${mermaidStr}</div>
              </div>
            `;
        }
      }

      html += `
        <div class="accordion-group" data-group="${gid}">
          <div class="accordion-header" onclick="this.parentElement.classList.toggle('open')">
            <span class="accordion-icon">${icon}</span>
            <span class="accordion-title">${g.title}</span>
            <span class="accordion-count">${activeCount} активных / ${g.projects.length} всего</span>
            <span class="accordion-chevron">▸</span>
          </div>
          <div class="accordion-body">
            ${groupSchemaHtml}
            ${g.projects.map((p) => renderProjectCard(p)).join("")}
          </div>
        </div>
      `;
    }

    if (ungrouped.length) {
      html += `
        <div class="accordion-group open" data-group="ungrouped">
          <div class="accordion-header" onclick="this.parentElement.classList.toggle('open')">
            <span class="accordion-icon">📌</span>
            <span class="accordion-title">Без группы</span>
            <span class="accordion-count">${ungrouped.length}</span>
            <span class="accordion-chevron">▸</span>
          </div>
          <div class="accordion-body">
            ${ungrouped.map((p) => renderProjectCard(p)).join("")}
          </div>
        </div>
      `;
    }

    container.innerHTML = html || '<div class="no-results">Нет проектов по фильтру</div>';

    // Auto-render new mermaid schemas
    requestAnimationFrame(() => {
      try {
        if (window.mermaid) mermaid.init(undefined, container.querySelectorAll('.mermaid'));
      } catch (e) {
        console.warn("Mermaid init error via accordion", e);
      }
    });
  }

  function renderProjectCard(p) {
    const statusLabel = STATUS_LABELS[p.status] || p.status;
    const statusColor = STATUS_COLORS[p.status] || "#64748b";
    const progress = p.progress || 0;
    const tags = (p.tags || []).slice(0, 3).map((t) => `<span class="tag-chip">${t}</span>`).join("");
    const areaEmoji = p.life_area === "работа" ? "💼" : p.life_area === "я" ? "🧠" : p.life_area === "семья" ? "👨‍👩‍👧‍👦" : "";

    return `
      <div class="project-card" onclick="window._openProject('${p.id}')">
        <div class="project-card-header">
          <span class="project-card-title">${areaEmoji} ${p.title}</span>
          <span class="status-dot" style="background:${statusColor}" title="${statusLabel}"></span>
        </div>
        ${p.description ? `<div class="project-card-desc">${p.description.substring(0, 100)}${p.description.length > 100 ? "…" : ""}</div>` : ""}
        <div class="project-card-footer">
          <div class="project-card-tags">${tags}</div>
          ${progress > 0 ? `<div class="mini-progress"><div class="mini-progress-fill" style="width:${progress}%"></div></div>` : ""}
        </div>
      </div>
    `;
  }

  function renderProjectCard(p) {
    const statusLabel = STATUS_LABELS[p.status] || p.status;
    const statusColor = STATUS_COLORS[p.status] || "#64748b";
    const progress = p.progress || 0;
    const tags = (p.tags || []).slice(0, 3).map((t) => `<span class="tag-chip">${t}</span>`).join("");
    const areaEmoji = p.life_area === "СЂР°Р±РѕС‚Р°" ? "рџ’ј" : p.life_area === "СЏ" ? "рџ§ " : p.life_area === "СЃРµРјСЊСЏ" ? "рџ‘ЁвЂЌрџ‘©вЂЌрџ‘§вЂЌрџ‘¦" : "";
    const nextStep = escapeHtml(getProjectNextStep(p));
    const kbButton = p.kbNote?.obsidianUri
      ? `<button class="auth-btn" style="width:auto;padding:6px 12px;font-size:0.78rem;" onclick="event.stopPropagation(); window._openKbNote('${p.id}')">KB</button>`
      : "";
    const relatedCounts = `<span class="tag-chip">чаты: ${p.relatedChats?.length || p.relatedChatsCount || 0}</span><span class="tag-chip">workflows: ${p.relatedWorkflows?.length || p.relatedWorkflowsCount || 0}</span>`;

    return `
      <div class="project-card" onclick="window._openProject('${p.id}')">
        <div class="project-card-header">
          <span class="project-card-title">${areaEmoji} ${p.title}</span>
          <span class="status-dot" style="background:${statusColor}" title="${statusLabel}"></span>
        </div>
        ${p.description ? `<div class="project-card-desc">${p.description.substring(0, 100)}${p.description.length > 100 ? "вЂ¦" : ""}</div>` : ""}
        <div class="project-card-desc" style="font-size:0.82rem;color:var(--text-secondary);margin-top:8px;"><strong>Следующий шаг:</strong> ${nextStep}</div>
        <div class="project-card-footer">
          <div class="project-card-tags">${tags}${relatedCounts}</div>
          ${progress > 0 ? `<div class="mini-progress"><div class="mini-progress-fill" style="width:${progress}%"></div></div>` : ""}
        </div>
        <div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;">
          <button class="auth-btn" style="width:auto;padding:6px 12px;font-size:0.78rem;" onclick="event.stopPropagation(); window._openProject('${p.id}')">Project mode</button>
          ${kbButton}
        </div>
      </div>
    `;
  }

  // ============================================================
  //  INBOX TAB (Signals)
  // ============================================================
  function renderSignalCard(signal) {
    const routeColors = {
      project_update: "#22c55e",
      new_idea: "#f59e0b",
      skill_candidate: "#8b5cf6",
      reference_note: "#06b6d4",
      archive: "#64748b",
      pending: "#94a3b8",
    };
    const routeLabels = {
      project_update: "Проект",
      new_idea: "Идея",
      skill_candidate: "Навык",
      reference_note: "Заметка",
      archive: "Архив",
      pending: "Ожидание",
    };

    const color = routeColors[signal.route] || "#64748b";
    const routeLabel = routeLabels[signal.route] || signal.route || "—";
    const tags = (signal.tags || []).map((t) => `<span class="tag-chip">${t}</span>`).join("");
    const score = signal.relevance_score || 0;
    const date = signal.created_at ? new Date(signal.created_at).toLocaleDateString("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }) : "";
    const isHot = score >= 70;

    // Action buttons based on status
    let actionHtml = '';
    if (signal.action_taken) {
      actionHtml = `<div class="signal-action-done">✓ Обработано: ${signal.action_taken}</div>`;
    } else {
      actionHtml = `
        <div class="signal-actions">
          <button class="signal-action-btn" onclick="window._handleSignalAction('${signal.id}', 'idea')">💡 В Идею</button>
          <button class="signal-action-btn" onclick="window._handleSignalAction('${signal.id}', 'note')">📝 В Заметку</button>
          <button class="signal-action-btn btn-ignore" onclick="window._handleSignalAction('${signal.id}', 'ignore')">✕ Скрыть</button>
        </div>
      `;
    }

    return `
      <div class="signal-card ${isHot ? "signal-hot" : ""}" id="signal-${signal.id}">
        <div class="signal-card-header">
          <span class="signal-route-badge" style="background:${color}">${routeLabel}</span>
          <span class="signal-date">${date}</span>
        </div>
        <div class="signal-summary">${signal.summary || signal.original_text || "—"}</div>
        ${tags ? `<div class="signal-tags">${tags}</div>` : ""}
        <div class="signal-meta">
          <div class="relevance-bar"><div class="relevance-fill" style="width:${score}%;background:${score >= 70 ? "#22c55e" : score >= 40 ? "#f59e0b" : "#64748b"}"></div></div>
          <span class="relevance-label">${score}%</span>
        </div>
        ${actionHtml}
      </div>
    `;
  }

  // Expose to window for inline onclick
  window._handleSignalAction = async function (signalId, actionType) {
    if (!supabaseClient) return alert("Supabase не подключен");
    try {
      // 1. Mark signal as processed
      const actionName = actionType === 'idea' ? 'Создана идея' : actionType === 'note' ? 'Создана заметка' : 'Проигнорировано';

      const { error } = await supabaseClient
        .from('signals')
        .update({ action_taken: actionName })
        .eq('id', signalId);

      if (error) throw error;

      // 2. Optimistic UI update
      const signal = signalsData.find(s => s.id === signalId);
      if (signal) signal.action_taken = actionName;
      renderSignals();

      // 3. Create actual entity (mock for now until backend is fully wired to create API)
      if (actionType !== 'ignore') {
        alert(actionName + " (Заглушка: Здесь будет вызов создания записи в БД)");
      }
    } catch (err) {
      console.error("Signal action error:", err);
      alert("Ошибка: " + err.message);
    }
  };

  function renderSignals() {
    const container = document.getElementById("signalFeed");
    if (!container) return;

    let filtered = signalsData;
    if (currentSignalFilter !== "all") {
      filtered = signalsData.filter((s) => s.route === currentSignalFilter);
    }

    if (!filtered.length) {
      container.innerHTML = '<div class="no-results">Нет сигналов</div>';
      return;
    }
    container.innerHTML = filtered.map((s) => renderSignalCard(s)).join("");
  }

  function updateInboxBadge() {
    const badge = document.getElementById("inboxBadge");
    const countBadge = document.getElementById("signalCountBadge");
    if (badge) badge.textContent = signalsData.length > 0 ? signalsData.length : "";
    if (countBadge) countBadge.textContent = signalsData.length > 0 ? signalsData.length : "";
  }

  // ============================================================
  //  LIBRARY TAB
  // ============================================================
  function renderGoals() {
    const el = document.getElementById("goalsGrid");
    if (!el) return;

    const areaIcons = { работа: "💼", я: "🧠", семья: "👨‍👩‍👧‍👦" };
    const areaColors = { работа: "#3b82f6", я: "#8b5cf6", семья: "#f59e0b" };

    el.innerHTML = goalsData.map((g) => `
      <div class="goal-card" style="border-left: 3px solid ${areaColors[g.life_area] || "#64748b"}">
        <div class="goal-header">
          <span class="goal-area">${areaIcons[g.life_area] || "📌"} ${g.life_area}</span>
          <span class="goal-status">${g.status === "active" ? "🟢 Активна" : "⏸ Пауза"}</span>
        </div>
        <div class="goal-title">${g.title}</div>
        <div class="goal-desc">${g.description || ""}</div>
        ${g.focus_themes ? `<div class="goal-themes">${g.focus_themes.map((t) => `<span class="tag-chip">${t}</span>`).join("")}</div>` : ""}
        ${g.project_ids && g.project_ids.length ? `<div class="goal-projects">${g.project_ids.length} связанных проектов</div>` : ""}
      </div>
    `).join("") || '<div class="empty-state">Нет целей</div>';
  }

  function renderIdeasLibrary() {
    const el = document.getElementById("ideasGrid");
    const badge = document.getElementById("ideasCountBadge");
    if (!el) return;

    let filtered = ideasData;
    if (currentIdeaPriority !== "all") {
      filtered = ideasData.filter((i) => i.priority === currentIdeaPriority);
    }

    if (badge) badge.textContent = ideasData.length || "";

    el.innerHTML = filtered.map((idea) => {
      const priorityColor = idea.priority === "high" ? "#ef4444" : idea.priority === "medium" ? "#f59e0b" : "#64748b";
      const tags = (idea.tags || []).map((t) => `<span class="tag-chip">${t}</span>`).join("");
      return `
        <div class="idea-card" onclick="window._openIdea('${idea.id}')">
          <div class="idea-card-header">
            <span class="idea-priority-dot" style="background:${priorityColor}"></span>
            <span class="idea-title">${idea.title}</span>
          </div>
          <div class="idea-desc">${(idea.description || "").substring(0, 120)}${(idea.description || "").length > 120 ? "…" : ""}</div>
          ${idea.related_project ? `<div class="idea-related">↗ ${idea.related_project}</div>` : ""}
          <div class="idea-tags">${tags}</div>
          <div class="idea-footer">
            <span class="idea-score">${idea.relevance_score || 0}%</span>
            ${idea.next_step ? `<span class="idea-next">→ ${idea.next_step.substring(0, 50)}…</span>` : ""}
          </div>
        </div>
      `;
    }).join("") || '<div class="no-results">Нет идей по фильтру</div>';
  }

  function renderNotes() {
    const el = document.getElementById("notesGrid");
    const badge = document.getElementById("notesCountBadge");
    if (!el) return;

    if (badge) badge.textContent = notesData.length || "";

    if (!notesData.length) {
      el.innerHTML = '<div class="empty-state">Заметки будут появляться из сигналов и ручного добавления</div>';
      return;
    }

    el.innerHTML = notesData.map((n) => `
      <div class="note-card">
        <div class="note-title">${n.title}</div>
        <div class="note-content">${(n.content || "").substring(0, 150)}</div>
        <div class="note-tags">${(n.tags || []).map((t) => `<span class="tag-chip">${t}</span>`).join("")}</div>
      </div>
    `).join("");
  }

  // ============================================================
  //  ASSISTANT TAB
  // ============================================================
  function renderSystemProfile() {
    const el = document.getElementById("systemProfileCard");
    if (!el || !monitoringData.profile.title) return;
    const p = monitoringData.profile;

    el.innerHTML = `
      <div class="profile-card">
        <div class="profile-title">${p.title}</div>
        <div class="profile-summary">${p.summary || ""}</div>
        ${p.roles ? `<div class="profile-roles">${p.roles.map((r) => `<span class="role-tag">${r}</span>`).join("")}</div>` : ""}
        ${p.lifeAreas ? `<div class="profile-areas">${p.lifeAreas.map((a) => `
          <div class="area-chip">
            <strong>${a.label}</strong>: ${a.focus}
          </div>
        `).join("")}</div>` : ""}
      </div>
    `;
  }

  function renderRoutingRules() {
    const el = document.getElementById("systemRoutingList");
    if (!el) return;
    const rules = monitoringData.routingRules || [];
    el.innerHTML = rules.map((r) => `
      <div class="protocol-item">
        <div class="protocol-when">${r.when}</div>
        <div class="protocol-route">→ ${r.route}</div>
        <div class="protocol-action">${r.action}</div>
      </div>
    `).join("") || '<div class="empty-state">Нет правил</div>';
  }

  function renderSkillSuggestions() {
    const el = document.getElementById("monitorSkillGrid");
    if (!el) return;
    const items = monitoringData.skillSuggestions || [];
    el.innerHTML = items.map((s) => `
      <div class="suggestion-card">
        <div class="suggestion-title">🛠 ${s.title}</div>
        <div class="suggestion-summary">${s.summary || ""}</div>
        <div class="suggestion-why">${s.why || ""}</div>
      </div>
    `).join("") || '<div class="empty-state">Нет предложений</div>';
  }

  function renderProjectSuggestions() {
    const el = document.getElementById("monitorProjectGrid");
    if (!el) return;
    const items = monitoringData.projectSuggestions || [];
    el.innerHTML = items.map((s) => `
      <div class="suggestion-card">
        <div class="suggestion-title">🧪 ${s.title}</div>
        <div class="suggestion-summary">${s.summary || ""}</div>
        <div class="suggestion-why">${s.why || ""}</div>
      </div>
    `).join("") || '<div class="empty-state">Нет гипотез</div>';
  }

  function renderRecommendations() {
    const container = document.getElementById("asstRecommendations");
    if (!container) return;
    const recs = monitoringData.recommendations || [];

    // Add Report Generation Button for Digital Twin
    const headerHtml = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <h3 class="intel-subtitle" style="margin:0;">Активные действия (Скиллы)</h3>
      </div>
      <div class="suggestion-card" style="margin-bottom:16px; border-color:var(--accent);">
        <div class="suggestion-title">Сгенерировать AI-Отчет</div>
        <div class="suggestion-summary">Проанализировать все входящие сигналы за последние 24 часа и составить саммари для фокуса.</div>
        <button class="auth-btn" style="margin-top:10px; width:auto; padding:6px 16px; font-size:0.8rem;" onclick="alert('Скилл в разработке: Здесь AI агент проанализирует данные и выдаст ответ.')">⚡ Запустить анализ</button>
      </div>
      <h3 class="intel-subtitle">Рекомендации системы</h3>
    `;

    if (!recs.length) {
      container.innerHTML = headerHtml + '<div class="empty-state">Нет новых рекомендаций</div>';
      return;
    }

    container.innerHTML = headerHtml + `<div style="display:grid;gap:8px;">` +
      recs.map((r) => `<div class="recommendation-item">💡 ${r}</div>`).join("") +
      `</div>`;
  }

  // ============================================================
  //  MODALS
  // ============================================================
  function openProjectModal(projectId) {
    const p = projectsData.find((x) => x.id === projectId);
    if (!p) return;

    document.getElementById("modalTitle").textContent = p.title;
    const statusEl = document.getElementById("modalStatus");
    statusEl.textContent = STATUS_LABELS[p.status] || p.status;
    statusEl.style.background = STATUS_COLORS[p.status] || "#64748b";
    statusEl.style.color = "#fff";

    // Build Holistic System Context from Graph
    const outgoing = projectRelationsData.filter(r => r.from_id === projectId);
    const incoming = projectRelationsData.filter(r => r.to_id === projectId);
    const safeTitle = (t) => t.replace(/["()]/g, '');

    let contextHtml = "";
    if (outgoing.length > 0 || incoming.length > 0) {
      let mermaidStr = "graph LR\n";
      mermaidStr += `  Current["${safeTitle(p.title)}"]:::current\n`;

      incoming.forEach(r => {
        const fromProj = projectsData.find(x => x.id === r.from_id)?.title || r.from_id;
        const relLabel = RELATION_LABELS[r.relation] || r.relation;
        mermaidStr += `  ID_${r.from_id}["${safeTitle(fromProj)}"] -->|${relLabel}| Current\n`;
      });
      outgoing.forEach(r => {
        const toProj = projectsData.find(x => x.id === r.to_id)?.title || r.to_id;
        const relLabel = RELATION_LABELS[r.relation] || r.relation;
        mermaidStr += `  Current -->|${relLabel}| ID_${r.to_id}["${safeTitle(toProj)}"]\n`;
      });

      mermaidStr += `  classDef current fill:#3b82f6,color:#fff,stroke:#2563eb,stroke-width:2px;`;

      contextHtml = `
        <div class="modal-section" style="margin-top:16px;">
          <div class="modal-section-title" style="margin-bottom:8px; display:flex; align-items:center; gap:6px;">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
            Холистичный контекст
          </div>
          <div style="background:var(--bg); border-radius:var(--radius-sm); border:1px solid var(--border-light); padding:16px;">
            <p style="margin-top:0; margin-bottom:12px; font-size:0.85rem; color:var(--text-secondary);">Место проекта в общей экосистеме:</p>
            <div class="mermaid">${mermaidStr}</div>
          </div>
        </div>
      `;
    }

    // Build History & Tasks
    const historyHtml = `
      <div class="modal-section" style="margin-top:16px;">
        <div class="modal-section-title">⌛ История разработки</div>
        <div class="modal-desc" style="font-style:italic; border-left:3px solid var(--border); padding-left:12px; margin-top:8px;">
          Данные об истории разработки пока агрегируются из Заметок и Telegram-сигналов. 
          <br><span style="font-size:0.8em; color:var(--accent); cursor:pointer;" onclick="alert('Скилл AI-анализа историй в разработке')">⚡ Сгенерировать историю через AI</span>
        </div>
      </div>
    `;

    const tasksHtml = `
      <div class="modal-section" style="margin-top:16px;">
        <div class="modal-section-title">Предстоящие задачи</div>
        <ul class="task-list" style="margin-top:8px;">
          ${(p.tasks || []).map(t => `<li class="${t.done ? "done" : ""}">${t.done ? "✅" : "⬜"} ${t.text}</li>`).join("") || "<li><i>Нет активных задач</i></li>"}
        </ul>
      </div>
    `;

    // Future plans / essence
    let futureHtml = "";
    if (p.status === 'completed' || p.status === 'active') {
      futureHtml = `
        <div class="modal-section" style="margin-top:16px; background:var(--research-light); padding:12px; border-radius:var(--radius-sm); border:1px solid var(--research);">
          <div class="modal-section-title" style="color:var(--research);">🚀 Вектор развития (Суть)</div>
          <div style="font-size:0.85rem; margin-top:6px; color:var(--text-primary);">
            ${p.description || "Определяется в процессе. Основная задача — бесшовная интеграция с 'Мозгом'."}
          </div>
        </div>
      `;
    } else {
      futureHtml = `
        <div class="modal-section" style="margin-top:16px;">
          <div class="modal-section-title">Суть проекта</div>
          <div class="modal-desc" style="margin-top:4px;">${p.description || "Нет описания."}</div>
        </div>
      `;
    }

    // Inject content
    document.getElementById("modalContentBody").innerHTML = `
      <div class="progress-container" style="margin-bottom:12px;">
        <div class="progress-bar"><div class="progress-fill" style="width:${p.progress || 0}%"></div></div>
        <span class="progress-label">${p.progress || 0}%</span>
      </div>
      ${futureHtml}
      ${contextHtml}
      ${historyHtml}
      ${tasksHtml}
    `;

    document.getElementById("modalOverlay").classList.add("active");

    // Auto-render modal mermaid schemas
    requestAnimationFrame(() => {
      try {
        if (window.mermaid) mermaid.init(undefined, document.getElementById("modalContentBody").querySelectorAll('.mermaid'));
      } catch (e) { console.warn("Mermaid modal render error", e); }
    });
  }

  function closeProjectModal() {
    document.getElementById("modalOverlay").classList.remove("active");
  }

  function openProjectModal(projectId) {
    const p = projectsData.find((x) => x.id === projectId);
    if (!p) return;

    const tasks = getProjectTasks(p);
    const relatedChats = Array.isArray(p.relatedChats) ? p.relatedChats : [];
    const relatedWorkflows = Array.isArray(p.relatedWorkflows) ? p.relatedWorkflows : [];
    const launchPrompt = p.launchContract?.prompt || "";
    const kbUri = p.kbNote?.obsidianUri || "";

    document.getElementById("modalTitle").textContent = p.title;
    const statusEl = document.getElementById("modalStatus");
    statusEl.textContent = STATUS_LABELS[p.status] || p.status;
    statusEl.style.background = STATUS_COLORS[p.status] || "#64748b";
    statusEl.style.color = "#fff";

    const outgoing = projectRelationsData.filter((r) => r.from_id === projectId);
    const incoming = projectRelationsData.filter((r) => r.to_id === projectId);
    const safeTitle = (t) => t.replace(/["()]/g, "");

    let contextHtml = "";
    if (outgoing.length > 0 || incoming.length > 0) {
      let mermaidStr = "graph LR\n";
      mermaidStr += `  Current["${safeTitle(p.title)}"]:::current\n`;

      incoming.forEach((r) => {
        const fromProj = projectsData.find((x) => x.id === r.from_id)?.title || r.from_id;
        const relLabel = RELATION_LABELS[r.relation] || r.relation;
        mermaidStr += `  ID_${r.from_id}["${safeTitle(fromProj)}"] -->|${relLabel}| Current\n`;
      });
      outgoing.forEach((r) => {
        const toProj = projectsData.find((x) => x.id === r.to_id)?.title || r.to_id;
        const relLabel = RELATION_LABELS[r.relation] || r.relation;
        mermaidStr += `  Current -->|${relLabel}| ID_${r.to_id}["${safeTitle(toProj)}"]\n`;
      });

      mermaidStr += "  classDef current fill:#3b82f6,color:#fff,stroke:#2563eb,stroke-width:2px;";

      contextHtml = `
        <div class="modal-section" style="margin-top:16px;">
          <div class="modal-section-title" style="margin-bottom:8px; display:flex; align-items:center; gap:6px;">Холистичный контекст</div>
          <div style="background:var(--bg); border-radius:var(--radius-sm); border:1px solid var(--border-light); padding:16px;">
            <p style="margin-top:0; margin-bottom:12px; font-size:0.85rem; color:var(--text-secondary);">Место проекта в общей экосистеме:</p>
            <div class="mermaid">${mermaidStr}</div>
          </div>
        </div>
      `;
    }

    const projectModeHtml = `
      <div class="modal-section" style="margin-top:16px;">
        <div class="modal-section-title">Project mode</div>
        <div style="background:var(--bg); border-radius:var(--radius-sm); border:1px solid var(--border-light); padding:16px; display:grid; gap:12px;">
          <div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:4px;">Следующий шаг</div>
            <div style="font-size:0.92rem;">${escapeHtml(getProjectNextStep(p))}</div>
          </div>
          <div style="display:flex; gap:8px; flex-wrap:wrap;">
            ${kbUri ? `<button class="auth-btn" style="width:auto;padding:8px 14px;font-size:0.8rem;" onclick="window._openKbNote('${p.id}')">Открыть KB</button>` : ""}
            ${launchPrompt ? `<button class="auth-btn" style="width:auto;padding:8px 14px;font-size:0.8rem;" onclick="window._copyLaunchPrompt('${p.id}')">Скопировать промпт</button>` : ""}
          </div>
          <div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:4px;">Связанные чаты</div>
            <ul class="task-list" style="margin-top:6px;">${renderRegistryLinks(relatedChats, "Нет связанных чатов")}</ul>
          </div>
          <div>
            <div style="font-size:0.8rem; color:var(--text-secondary); margin-bottom:4px;">Связанные workflows</div>
            <ul class="task-list" style="margin-top:6px;">${renderRegistryLinks(relatedWorkflows, "Нет связанных workflows")}</ul>
          </div>
        </div>
      </div>
    `;

    const historyHtml = `
      <div class="modal-section" style="margin-top:16px;">
        <div class="modal-section-title">⌛ История разработки</div>
        <div class="modal-desc" style="font-style:italic; border-left:3px solid var(--border); padding-left:12px; margin-top:8px;">
          История пока собирается из заметок и сигналов. Это слой обзора, а не каноническое хранилище.
        </div>
      </div>
    `;

    const tasksHtml = `
      <div class="modal-section" style="margin-top:16px;">
        <div class="modal-section-title">Предстоящие задачи</div>
        <ul class="task-list" style="margin-top:8px;">
          ${tasks.map((t) => `<li class="${t.done ? "done" : ""}">${t.done ? "✅" : "⬜"} ${escapeHtml(t.task)}</li>`).join("") || "<li><i>Нет активных задач</i></li>"}
        </ul>
      </div>
    `;

    const futureHtml = (p.status === "done" || p.status === "active")
      ? `
        <div class="modal-section" style="margin-top:16px; background:var(--research-light); padding:12px; border-radius:var(--radius-sm); border:1px solid var(--research);">
          <div class="modal-section-title" style="color:var(--research);">Вектор развития</div>
          <div style="font-size:0.85rem; margin-top:6px; color:var(--text-primary);">
            ${p.description || "Основной смысл проекта ещё не зафиксирован в KB."}
          </div>
        </div>
      `
      : `
        <div class="modal-section" style="margin-top:16px;">
          <div class="modal-section-title">Суть проекта</div>
          <div class="modal-desc" style="margin-top:4px;">${p.description || "Нет описания."}</div>
        </div>
      `;

    document.getElementById("modalContentBody").innerHTML = `
      <div class="progress-container" style="margin-bottom:12px;">
        <div class="progress-bar"><div class="progress-fill" style="width:${p.progress || 0}%"></div></div>
        <span class="progress-label">${p.progress || 0}%</span>
      </div>
      ${futureHtml}
      ${projectModeHtml}
      ${contextHtml}
      ${historyHtml}
      ${tasksHtml}
    `;

    document.getElementById("modalOverlay").classList.add("active");

    requestAnimationFrame(() => {
      try {
        if (window.mermaid) {
          mermaid.init(undefined, document.getElementById("modalContentBody").querySelectorAll(".mermaid"));
        }
      } catch (e) {
        console.warn("Mermaid modal render error", e);
      }
    });
  }

  function openIdeaModal(ideaId) {
    const idea = ideasData.find((x) => x.id === ideaId);
    if (!idea) return;

    document.getElementById("ideaModalTitle").textContent = idea.title;
    document.getElementById("ideaModalDesc").textContent = idea.description || "";
    document.getElementById("ideaModalRelated").textContent = idea.related_project
      ? `Связанный проект: ${idea.related_project}`
      : "";
    document.getElementById("ideaModalTags").innerHTML = (idea.tags || []).map((t) => `<span class="modal-tag">${t}</span>`).join("");
    document.getElementById("ideaModalDate").textContent = idea.added_date
      ? `Добавлено: ${idea.added_date}`
      : "";

    document.getElementById("ideaModalOverlay").classList.add("active");
  }

  function closeIdeaModal() {
    document.getElementById("ideaModalOverlay").classList.remove("active");
  }

  // Expose to onclick
  window._openProject = openProjectModal;
  window._openIdea = openIdeaModal;
  window._openKbNote = function (projectId) {
    const project = projectsData.find((item) => item.id === projectId);
    const uri = project?.kbNote?.obsidianUri;
    if (uri) window.location.href = uri;
  };
  window._copyLaunchPrompt = async function (projectId) {
    const project = projectsData.find((item) => item.id === projectId);
    const prompt = project?.launchContract?.prompt;
    if (!prompt) return;
    await copyText(prompt);
  };

  // ============================================================
  //  EVENTS
  // ============================================================
  function bindEvents() {
    // Theme toggle
    document.getElementById("themeToggle")?.addEventListener("click", () => {
      const current = document.body.getAttribute("data-theme");
      applyTheme(current === "dark" ? "light" : "dark");
    });

    // Tab switching
    document.querySelectorAll(".dashboard-tab").forEach((tab) => {
      tab.addEventListener("click", () => switchPanel(tab.dataset.panel));
    });

    // Project area filter
    document.getElementById("projectFilters")?.addEventListener("click", (e) => {
      const btn = e.target.closest(".filter-pill");
      if (!btn) return;
      document.querySelectorAll("#projectFilters .filter-pill").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentProjectArea = btn.dataset.area;
      renderProjectAccordion();
    });

    // Signal filter
    document.getElementById("signalFilters")?.addEventListener("click", (e) => {
      const btn = e.target.closest(".signal-filter");
      if (!btn) return;
      document.querySelectorAll("#signalFilters .signal-filter").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentSignalFilter = btn.dataset.route;
      renderSignals();
    });

    // Ideas priority filter
    document.getElementById("ideasFilter")?.addEventListener("click", (e) => {
      const btn = e.target.closest(".filter-pill");
      if (!btn) return;
      document.querySelectorAll("#ideasFilter .filter-pill").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentIdeaPriority = btn.dataset.priority;
      renderIdeasLibrary();
    });

    // Search
    document.getElementById("searchInput")?.addEventListener("input", (e) => {
      searchQuery = (e.target.value || "").toLowerCase();
      renderProjectAccordion();
    });

    // Modal close
    document.getElementById("modalClose")?.addEventListener("click", closeProjectModal);
    document.getElementById("modalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "modalOverlay") closeProjectModal();
    });
    document.getElementById("ideaModalClose")?.addEventListener("click", closeIdeaModal);
    document.getElementById("ideaModalOverlay")?.addEventListener("click", (e) => {
      if (e.target.id === "ideaModalOverlay") closeIdeaModal();
    });

    // Escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        closeProjectModal();
        closeIdeaModal();
      }
    });
  }

  // ============================================================
  //  RENDER ALL
  // ============================================================
  function renderAll() {
    // Date
    const dateEl = document.getElementById("headerDate");
    if (dateEl) {
      dateEl.textContent = new Date().toLocaleDateString("ru-RU", {
        weekday: "long", year: "numeric", month: "long", day: "numeric",
      });
    }

    // Overview
    renderOverviewStats();
    renderMindMap();

    // Projects
    renderProjectAccordion();

    // Inbox
    renderSignals();
    updateInboxBadge();

    // Library
    renderGoals();
    renderIdeasLibrary();
    renderNotes();

    // Assistant
    renderSystemProfile();
    renderRoutingRules();
    renderSkillSuggestions();
    renderProjectSuggestions();
    renderRecommendations();
  }

  // ============================================================
  //  INIT
  // ============================================================
  async function init() {
    console.log('[Dashboard] init() started');
    try {
      initTheme();
      console.log('[Dashboard] theme ok');

      if (window.mermaid) {
        mermaid.initialize({
          startOnLoad: false,
          theme: document.body.getAttribute('data-theme') === 'dark' ? 'dark' : 'default',
          securityLevel: 'loose'
        });
      }

      initSupabase();
      console.log('[Dashboard] supabase init ok');

      bindEvents();
      console.log('[Dashboard] events bound');

      // Load local JSON first (for monitoring profile, etc.)
      await loadDashboardData();
      console.log('[Dashboard] local JSON loaded, projects:', projectsData.length, 'registry:', projectRegistryData.length);

      // Load enriched data from Supabase
      await loadFromSupabase();
      console.log('[Dashboard] supabase loaded — projects:', projectsData.length, 'ideas:', ideasData.length, 'goals:', goalsData.length, 'signals:', signalsData.length);

      // Render everything
      renderAll();
      console.log('[Dashboard] renderAll() done');

      // Subscribe to realtime
      subscribeToSignals();

      // Handle window resize for mind map
      window.addEventListener('resize', () => {
        if (currentPanel === 'overviewPanel') renderMindMap();
      });

      console.log('[Dashboard] init() complete ✓');
    } catch (err) {
      console.error('[Dashboard] FATAL ERROR in init():', err);
      // Show visible error so user doesn't see blank page
      const errBanner = document.createElement('div');
      errBanner.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;background:#ef4444;color:#fff;padding:16px 20px;font-family:monospace;font-size:13px;white-space:pre-wrap;max-height:40vh;overflow:auto;';
      errBanner.textContent = '❌ Dashboard init error:\n' + (err && err.stack ? err.stack : String(err));
      document.body.appendChild(errBanner);
    }
  }

  document.addEventListener('DOMContentLoaded', init);
})();
