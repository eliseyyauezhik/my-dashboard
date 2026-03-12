(function () {
  "use strict";

  const treeCanvas = document.getElementById("treeCanvas");
  const detailsEl = document.getElementById("nodeDetails");
  const metaEl = document.getElementById("mapMeta");
  const searchInput = document.getElementById("searchInput");
  const expandAllBtn = document.getElementById("expandAllBtn");
  const collapseAllBtn = document.getElementById("collapseAllBtn");
  const ideaForm = document.getElementById("ideaForm");
  const ideaGroup = document.getElementById("ideaGroup");
  const ideaRelatedProject = document.getElementById("ideaRelatedProject");
  const ideaTitle = document.getElementById("ideaTitle");
  const ideaDescription = document.getElementById("ideaDescription");
  const ideaTags = document.getElementById("ideaTags");
  const ideaFormStatus = document.getElementById("ideaFormStatus");

  function isFileProtocol() {
    return typeof window !== "undefined" && window.location && window.location.protocol === "file:";
  }

  function renderFileProtocolHint() {
    if (!isFileProtocol()) return;
    if (metaEl) {
      metaEl.textContent =
        "Открыто как file:// — браузер блокирует загрузку JSON. Запустите сервер: .\\start_dashboard.ps1 -Open";
    }
    if (ideaFormStatus) {
      ideaFormStatus.textContent =
        "Для загрузки данных и сохранения идей откройте карту через локальный сервер дашборда: .\\start_dashboard.ps1 -Open";
    }
    const banner = document.getElementById("fileProtocolBanner");
    if (banner) {
      banner.hidden = false;
    }
  }

  const GROUPS = [
    {
      id: "knowledge",
      label: "База знаний и навигация",
      summary: "Карты, дашборды, second brain, мониторинг, RAG и инструменты для целостного обзора.",
    },
    {
      id: "agents",
      label: "Агентные системы и навыки",
      summary: "CLI/IDE-агенты, skills, автоматизация, orchestration и reusable-подходы.",
    },
    {
      id: "education",
      label: "Образование и гранты",
      summary: "Гимназия, образовательные программы, грантовые заявки, стратегические инициативы.",
    },
    {
      id: "products",
      label: "Продукты и сервисы",
      summary: "Приложения, рейтинги, сервисные платформы, бизнес- и продуктовые гипотезы.",
    },
    {
      id: "personal",
      label: "Личная и семейная система",
      summary: "Личные контуры, family ops, организация дома и практическое применение идей в жизни.",
    },
    {
      id: "emerging",
      label: "Новые направления",
      summary: "Еще неустойчивые ветки, черновики и проекты без закрепленного смыслового кластера.",
    },
  ];

  const state = {
    dashboard: null,
    inbox: { ideas: [] },
    groups: [],
    selected: null,
    query: "",
  };

  function normalize(text) {
    return String(text || "").toLowerCase();
  }

  function escapeHtml(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  async function fetchJson(sources) {
    for (const source of sources) {
      try {
        const response = await fetch(source, { cache: "no-store" });
        if (!response.ok) continue;
        return await response.json();
      } catch (err) {
        console.warn("Source failed", source, err);
      }
    }
    return null;
  }

  async function loadDashboard() {
    const data = await fetchJson(["data/dashboard_data.json", "projects.json"]);
    if (!data) throw new Error("Dashboard data not found");
    return data;
  }

  async function loadIdeaInbox() {
    return (await fetchJson(["/api/idea-inbox", "data/idea_inbox.json"])) || { ideas: [] };
  }

  function groupForProject(project) {
    const text = normalize(
      [
        project.title,
        project.originalTitle,
        project.category,
        project.topic,
        ...(Array.isArray(project.tags) ? project.tags : []),
      ].join(" ")
    );

    if (/(карта|dashboard|дашборд|brain|knowledge|obsidian|monitor|monitoring|radar|rag|interest|систем)/.test(text)) {
      return "knowledge";
    }
    if (/(agent|агент|skill|skills|workflow|tgaggregator|telegram-агрегатор|copaw)/.test(text) || project.topic === "agents") {
      return "agents";
    }
    if (/(гимназ|davydov|образован|grant|грант|phantom)/.test(text) || project.topic === "education") {
      return "education";
    }
    if (/(семья|дом|family|дети|подарк|личн)/.test(text)) {
      return "personal";
    }
    if (project.topic === "products" || project.topic === "business" || /(app|product|smartmeeting|панел|service|strategy)/.test(text)) {
      return "products";
    }
    return "emerging";
  }

  renderFileProtocolHint();

  function groupForIdea(idea, projectGroupMap) {
    if (idea.relatedProject) {
      const key = normalize(idea.relatedProject);
      if (projectGroupMap.has(key)) return projectGroupMap.get(key);
    }
    const text = normalize([idea.title, idea.description, ...(idea.tags || [])].join(" "));
    if (/(грант|гимназ|образован)/.test(text)) return "education";
    if (/(agent|агент|skill|workflow|automation|автомат)/.test(text)) return "agents";
    if (/(dash|карта|knowledge|monitor|obsidian|brain|ideaforge)/.test(text)) return "knowledge";
    if (/(семья|дом|дети|подар)/.test(text)) return "personal";
    if (/(app|product|service|meeting|бот|инструмент)/.test(text)) return "products";
    return "emerging";
  }

  function mergeIdeas(baseIdeas, inboxIdeas) {
    const merged = [];
    const seen = new Set();
    const items = [...(baseIdeas || []), ...(inboxIdeas || [])];
    for (const idea of items) {
      const key = normalize(idea.id || idea.title);
      if (!key || seen.has(key)) continue;
      seen.add(key);
      merged.push(idea);
    }
    return merged;
  }

  function buildGroups() {
    const dashboard = state.dashboard || {};
    const groups = new Map(
      GROUPS.map((group) => [
        group.id,
        {
          ...group,
          projects: [],
          ideas: [],
        },
      ])
    );

    const chatsById = new Map((dashboard.chats || []).map((chat) => [chat.id, chat]));
    const workflowsById = new Map((dashboard.workflows || []).map((workflow) => [workflow.id, workflow]));
    const projectGroupMap = new Map();

    for (const project of dashboard.projects || []) {
      const groupId = groupForProject(project);
      projectGroupMap.set(normalize(project.title), groupId);
      projectGroupMap.set(normalize(project.id), groupId);
      const chats = (project.relatedChatIds || [])
        .map((chatId) => chatsById.get(chatId))
        .filter(Boolean)
        .slice(0, 6);
      const workflows = (project.relatedWorkflowIds || [])
        .map((workflowId) => workflowsById.get(workflowId))
        .filter(Boolean)
        .slice(0, 6);
      groups.get(groupId).projects.push({
        ...project,
        chats,
        workflows,
        ideas: [],
      });
    }

    const ideas = mergeIdeas(dashboard.ideas || [], state.inbox.ideas || []);
    for (const idea of ideas) {
      const groupId = groupForIdea(idea, projectGroupMap);
      const project = groups
        .get(groupId)
        .projects.find(
          (item) =>
            normalize(item.title) === normalize(idea.relatedProject) ||
            normalize(item.id) === normalize(idea.relatedProject)
        );
      if (project) {
        project.ideas.push(idea);
      } else {
        groups.get(groupId).ideas.push(idea);
      }
    }

    state.groups = GROUPS.map((group) => groups.get(group.id)).filter(Boolean);
  }

  function fillGroupSelect() {
    const currentValue = ideaGroup.value;
    ideaGroup.innerHTML = state.groups
      .map((group) => `<option value="${group.id}">${escapeHtml(group.label)}</option>`)
      .join("");
    if (currentValue) ideaGroup.value = currentValue;
  }

  function matchesQuery(value, query) {
    return normalize(value).includes(query);
  }

  function filterGroups(groups, query) {
    if (!query) return groups;
    return groups
      .map((group) => {
        const groupMatch = matchesQuery([group.label, group.summary].join(" "), query);
        const ideas = group.ideas.filter((idea) =>
          matchesQuery([idea.title, idea.description, (idea.tags || []).join(" ")].join(" "), query)
        );
        const projects = group.projects
          .map((project) => {
            const projectMatch = matchesQuery(
              [project.title, project.originalTitle, project.description, (project.tags || []).join(" ")].join(" "),
              query
            );
            const projectIdeas = (project.ideas || []).filter((idea) =>
              matchesQuery([idea.title, idea.description, (idea.tags || []).join(" ")].join(" "), query)
            );
            const chats = (project.chats || []).filter((chat) =>
              matchesQuery([chat.title, chat.summary, chat.theme].join(" "), query)
            );
            const workflows = (project.workflows || []).filter((workflow) =>
              matchesQuery([workflow.name, workflow.notes, workflow.source].join(" "), query)
            );
            if (!groupMatch && !projectMatch && !projectIdeas.length && !chats.length && !workflows.length) return null;
            return {
              ...project,
              ideas: projectMatch ? project.ideas : projectIdeas,
              chats: projectMatch ? project.chats : chats,
              workflows: projectMatch ? project.workflows : workflows,
            };
          })
          .filter(Boolean);
        if (!groupMatch && !projects.length && !ideas.length) return null;
        return {
          ...group,
          projects: groupMatch ? group.projects : projects,
          ideas: groupMatch ? group.ideas : ideas,
        };
      })
      .filter(Boolean);
  }

  function statusChip(project) {
    const statusClass = `status-${project.status || "research"}`;
    return `<span class="chip ${statusClass}">${escapeHtml(project.status || "research")}</span>`;
  }

  function renderIdeaNode(idea) {
    return `
      <div class="idea-item node-selectable" data-kind="idea" data-title="${escapeHtml(idea.title)}">
        <div class="idea-item-title">${escapeHtml(idea.title)}</div>
        <div class="idea-item-meta">${escapeHtml(idea.description || "Черновик идеи без описания")}</div>
      </div>
    `;
  }

  function renderProject(project) {
    const chats = project.chats || [];
    const workflows = project.workflows || [];
    const ideas = project.ideas || [];
    const subtitle = project.originalTitle ? `${project.category || ""} (${project.originalTitle})` : project.category || "";
    return `
      <details class="project-branch branch" open>
        <summary
          class="branch-summary project-summary node-selectable"
          data-kind="project"
          data-project-id="${escapeHtml(project.id)}"
        >
          <div class="branch-title-wrap">
            <div class="branch-title">${escapeHtml(project.title)}</div>
            <div class="branch-subtitle">${escapeHtml(subtitle)}</div>
          </div>
          <div class="branch-meta">${project.relatedChatsCount || 0} чатов · ${project.relatedWorkflowsCount || 0} workflows</div>
        </summary>
        <div class="project-body">
          <div class="project-desc">${escapeHtml(project.description || "")}</div>
          <div class="chip-row">
            ${statusChip(project)}
            <span class="chip">${escapeHtml(project.topic || "manual")}</span>
            <span class="chip">${escapeHtml(String(project.progress || 0))}%</span>
          </div>
          ${
            ideas.length
              ? `<div class="idea-list">${ideas.map(renderIdeaNode).join("")}</div>`
              : ""
          }
          ${
            chats.length
              ? `<div class="node-list">${chats
                  .map(
                    (chat) => `
                      <div class="node-item node-selectable" data-kind="chat" data-chat-id="${escapeHtml(chat.id)}">
                        <strong>${escapeHtml(chat.title || chat.id)}</strong>
                        <span>${escapeHtml(chat.summary || chat.theme || "Связанный чат")}</span>
                      </div>
                    `
                  )
                  .join("")}</div>`
              : ""
          }
          ${
            workflows.length
              ? `<div class="node-list">${workflows
                  .map(
                    (workflow) => `
                      <div class="node-item node-selectable" data-kind="workflow" data-workflow-id="${escapeHtml(workflow.id)}">
                        <strong>${escapeHtml(workflow.name)}</strong>
                        <span>${escapeHtml(workflow.notes || workflow.source || "Связанный workflow")}</span>
                      </div>
                    `
                  )
                  .join("")}</div>`
              : ""
          }
        </div>
      </details>
    `;
  }

  function renderTree() {
    const groups = filterGroups(state.groups, state.query);
    if (!groups.length) {
      treeCanvas.innerHTML = '<div class="empty-state">Ничего не найдено. Попробуйте изменить запрос или снять фильтр.</div>';
      return;
    }

    treeCanvas.innerHTML = groups
      .map(
        (group) => `
          <details class="branch" open data-group-id="${escapeHtml(group.id)}">
            <summary class="branch-summary group-summary node-selectable" data-kind="group" data-group-id="${escapeHtml(group.id)}">
              <div class="branch-title-wrap">
                <div class="branch-title">${escapeHtml(group.label)}</div>
                <div class="branch-subtitle">${escapeHtml(group.summary)}</div>
              </div>
              <div class="branch-meta">${group.projects.length} проектов · ${group.ideas.length} идей</div>
            </summary>
            <div class="branch-body">
              ${
                group.ideas.length
                  ? `<div class="idea-list">${group.ideas.map(renderIdeaNode).join("")}</div>`
                  : ""
              }
              <div class="project-grid">${group.projects.map(renderProject).join("")}</div>
            </div>
          </details>
        `
      )
      .join("");

    bindTreeSelection();
  }

  function setDetails(content) {
    detailsEl.innerHTML = content;
  }

  function showGroupDetails(groupId) {
    const group = state.groups.find((item) => item.id === groupId);
    if (!group) return;
    ideaGroup.value = group.id;
    ideaRelatedProject.value = "";
    setDetails(`
      <div><strong>${escapeHtml(group.label)}</strong></div>
      <div>${escapeHtml(group.summary)}</div>
      <div>Проектов: <strong>${group.projects.length}</strong></div>
      <div>Идей: <strong>${group.ideas.length}</strong></div>
    `);
  }

  function showProjectDetails(projectId) {
    for (const group of state.groups) {
      const project = group.projects.find((item) => item.id === projectId);
      if (!project) continue;
      ideaGroup.value = group.id;
      ideaRelatedProject.value = project.title;
      setDetails(`
        <div><strong>${escapeHtml(project.title)}</strong></div>
        ${project.originalTitle ? `<div>Оригинал: ${escapeHtml(project.originalTitle)}</div>` : ""}
        <div>${escapeHtml(project.description || "")}</div>
        <div>Группа: <strong>${escapeHtml(group.label)}</strong></div>
        <div>Статус: <strong>${escapeHtml(project.status || "research")}</strong> · Прогресс: <strong>${escapeHtml(String(project.progress || 0))}%</strong></div>
        <div>Чатов: <strong>${project.relatedChatsCount || 0}</strong> · Workflows: <strong>${project.relatedWorkflowsCount || 0}</strong></div>
      `);
      return;
    }
  }

  function showIdeaDetails(title) {
    const idea = mergeIdeas(state.dashboard?.ideas || [], state.inbox.ideas || []).find(
      (item) => item.title === title
    );
    if (!idea) return;
    setDetails(`
      <div><strong>${escapeHtml(idea.title)}</strong></div>
      <div>${escapeHtml(idea.description || idea.comment || "Черновая идея")}</div>
      <div>Связанный проект: <strong>${escapeHtml(idea.relatedProject || "не указан")}</strong></div>
      <div>Теги: <strong>${escapeHtml((idea.tags || []).join(", ") || "нет")}</strong></div>
      <div>Добавлено: <strong>${escapeHtml(idea.addedDate || "—")}</strong></div>
    `);
  }

  function showChatDetails(chatId) {
    const chat = (state.dashboard?.chats || []).find((item) => item.id === chatId);
    if (!chat) return;
    setDetails(`
      <div><strong>${escapeHtml(chat.title || chat.id)}</strong></div>
      <div>${escapeHtml(chat.summary || "")}</div>
      <div>Тема: <strong>${escapeHtml(chat.theme || "—")}</strong></div>
      <div>Дата: <strong>${escapeHtml(chat.date || "—")}</strong></div>
    `);
  }

  function showWorkflowDetails(workflowId) {
    const workflow = (state.dashboard?.workflows || []).find((item) => item.id === workflowId);
    if (!workflow) return;
    setDetails(`
      <div><strong>${escapeHtml(workflow.name)}</strong></div>
      <div>${escapeHtml(workflow.notes || "Связанный workflow")}</div>
      <div>Источник: <strong>${escapeHtml(workflow.source || "—")}</strong></div>
      <div>Путь: <strong>${escapeHtml(workflow.path || "—")}</strong></div>
    `);
  }

  function bindTreeSelection() {
    treeCanvas.querySelectorAll(".node-selectable").forEach((element) => {
      element.addEventListener("click", (event) => {
        event.stopPropagation();
        const kind = element.dataset.kind;
        if (kind === "group") showGroupDetails(element.dataset.groupId);
        if (kind === "project") showProjectDetails(element.dataset.projectId);
        if (kind === "idea") showIdeaDetails(element.dataset.title);
        if (kind === "chat") showChatDetails(element.dataset.chatId);
        if (kind === "workflow") showWorkflowDetails(element.dataset.workflowId);
      });
    });
  }

  function updateMeta() {
    const projects = (state.dashboard?.projects || []).length;
    const ideas = mergeIdeas(state.dashboard?.ideas || [], state.inbox.ideas || []).length;
    metaEl.textContent = `Групп: ${state.groups.length} · Проектов: ${projects} · Идей: ${ideas}`;
  }

  function setFormStatus(message, kind) {
    ideaFormStatus.textContent = message;
    ideaFormStatus.className = `form-status ${kind || ""}`.trim();
  }

  async function saveIdea(event) {
    event.preventDefault();
    const payload = {
      title: ideaTitle.value.trim(),
      group: ideaGroup.value,
      relatedProject: ideaRelatedProject.value.trim(),
      description: ideaDescription.value.trim(),
      tags: ideaTags.value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      priority: "medium",
    };

    if (!payload.title) {
      setFormStatus("Введите название идеи.", "error");
      return;
    }

    try {
      const response = await fetch("/api/idea-inbox/ideas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error("idea inbox api unavailable");
      }
      const result = await response.json();
      state.inbox.ideas.unshift(result.idea);
      buildGroups();
      fillGroupSelect();
      renderTree();
      updateMeta();
      ideaForm.reset();
      ideaGroup.value = payload.group;
      setFormStatus("Идея сохранена в idea inbox. Она уже видна на карте и подхватится общим sync.", "ok");
    } catch (err) {
      console.error(err);
      setFormStatus(
        "Не удалось сохранить идею через API. Для прямой записи запустите `python scripts/dashboard/dashboard_server.py --port 8891` и откройте дашборд через этот сервер.",
        "error"
      );
    }
  }

  function bindControls() {
    searchInput.addEventListener("input", function () {
      state.query = normalize(this.value.trim());
      renderTree();
    });

    expandAllBtn.addEventListener("click", function () {
      treeCanvas.querySelectorAll("details").forEach((item) => {
        item.open = true;
      });
    });

    collapseAllBtn.addEventListener("click", function () {
      treeCanvas.querySelectorAll("details").forEach((item) => {
        item.open = false;
      });
    });

    ideaForm.addEventListener("submit", saveIdea);
  }

  async function init() {
    try {
      state.dashboard = await loadDashboard();
      state.inbox = await loadIdeaInbox();
      buildGroups();
      fillGroupSelect();
      renderTree();
      updateMeta();
      bindControls();
      showGroupDetails(state.groups[0]?.id || "");
      setFormStatus("Сохраняйте новые ветки как короткие гипотезы. Для прямой записи нужен интерактивный сервер дашборда.", "");
    } catch (err) {
      console.error(err);
      metaEl.textContent = "Ошибка загрузки карты";
      treeCanvas.innerHTML = '<div class="empty-state">Не удалось загрузить данные карты из dashboard_data.json.</div>';
      setFormStatus("Не удалось загрузить данные карты.", "error");
    }
  }

  init();
})();
