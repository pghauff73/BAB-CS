(function () {
  "use strict";

  const library = window.BABCS_DOCUMENTS;
  if (!library || !Array.isArray(library.documents)) {
    document.body.innerHTML = '<div class="noscript-message">The generated documentation payload is missing. Run <code>PYTHONPATH=src python tools/build_docs_html.py</code>.</div>';
    return;
  }

  const elements = {
    body: document.body,
    tree: document.getElementById("document-tree"),
    count: document.getElementById("document-count"),
    search: document.getElementById("document-search"),
    clearSearch: document.getElementById("clear-search"),
    breadcrumbs: document.getElementById("breadcrumbs"),
    category: document.getElementById("document-category"),
    title: document.getElementById("document-title"),
    summary: document.getElementById("document-summary"),
    meta: document.getElementById("document-meta"),
    hero: document.getElementById("document-hero"),
    heroCritical: document.getElementById("hero-critical-card"),
    stage: document.querySelector(".document-stage"),
    landing: document.getElementById("landing-dashboard"),
    content: document.getElementById("document-content"),
    footer: document.getElementById("document-footer"),
    toc: document.getElementById("table-of-contents"),
    tocProgress: document.getElementById("toc-progress"),
    progress: document.getElementById("reading-progress-bar"),
    stageProgress: document.getElementById("stage-progress-bar"),
    themeToggle: document.getElementById("theme-toggle"),
    print: document.getElementById("print-document"),
    copyLink: document.getElementById("copy-link"),
    sidebarToggle: document.getElementById("sidebar-toggle"),
    sidebarScrim: document.getElementById("sidebar-scrim"),
    toast: document.getElementById("toast"),
  };

  const documentsByPath = new Map(library.documents.map((document) => [document.path, document]));
  const conceptsById = new Map(
    (Array.isArray(library.conceptGlossary) ? library.conceptGlossary : [])
      .map((concept) => [concept.id, concept])
  );
  const homeHeadings = [
    { level: 2, text: "Plain-language guide", id: "overview-language" },
    { level: 2, text: "Engineering challenges", id: "overview-challenges" },
    { level: 2, text: "Engineering projects", id: "overview-projects" },
    { level: 2, text: "Engineering workflow", id: "overview-workflow" },
    { level: 2, text: "Simulation software", id: "overview-software" },
    { level: 2, text: "Engineering evidence", id: "overview-evidence" },
    { level: 2, text: "Engineering claim boundary", id: "overview-boundary" },
  ];
  const state = {
    current: null,
    searchQuery: "",
    projectFilter: "all",
    headingObserver: null,
    toastTimer: null,
  };

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
  }

  function slugify(value) {
    const plain = value.replace(/[`*_~]/g, "").trim().toLowerCase();
    return plain.replace(/[^a-z0-9\s-]/g, "").replace(/[-\s]+/g, "-").replace(/^-|-$/g, "") || "section";
  }

  function normalizePath(currentPath, targetPath) {
    const base = currentPath.split("/").slice(0, -1);
    const parts = targetPath.startsWith("/") ? [] : base;
    for (const part of targetPath.split("/")) {
      if (!part || part === ".") {
        continue;
      }
      if (part === "..") {
        parts.pop();
      } else {
        parts.push(part);
      }
    }
    return parts.join("/");
  }

  function routeHash(path, section) {
    const parameters = new URLSearchParams();
    parameters.set("doc", path);
    if (section) {
      parameters.set("section", section);
    }
    return `#${parameters.toString()}`;
  }

  function parseRoute() {
    const parameters = new URLSearchParams(window.location.hash.slice(1));
    return {
      path: parameters.get("doc"),
      section: parameters.get("section"),
    };
  }

  function simpleInline(value) {
    return escapeHtml(value)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
      .replace(/(^|[^_])_([^_]+)_/g, "$1<em>$2</em>");
  }

  function linkHtml(label, target, document, className = "") {
    const renderedLabel = simpleInline(label);
    const classAttribute = className ? ` class="${escapeAttribute(className)}"` : "";
    if (/^(https?:|mailto:)/i.test(target)) {
      return `<a${classAttribute} href="${escapeAttribute(target)}" target="_blank" rel="noreferrer">${renderedLabel}</a>`;
    }
    if (target.startsWith("#")) {
      const section = target.slice(1);
      return `<a${classAttribute} href="${escapeAttribute(routeHash(document.path, section))}" data-doc-path="${escapeAttribute(document.path)}" data-section="${escapeAttribute(section)}">${renderedLabel}</a>`;
    }
    const [rawPath, section = ""] = target.split("#", 2);
    const decodedPath = decodeURIComponent(rawPath);
    const resolved = normalizePath(document.path, decodedPath);
    if (documentsByPath.has(resolved)) {
      return `<a${classAttribute} href="${escapeAttribute(routeHash(resolved, section))}" data-doc-path="${escapeAttribute(resolved)}" data-section="${escapeAttribute(section)}">${renderedLabel}</a>`;
    }
    const sourceRelativeTarget = `../${target}`;
    return `<a${classAttribute} href="${escapeAttribute(sourceRelativeTarget)}">${renderedLabel}</a>`;
  }

  function imageSource(target) {
    const url = target.trim();
    if (/^(https?:|data:|\/)/i.test(url)) {
      return url;
    }
    if (/^(?:\.\/)?html\//i.test(url)) {
      return url.replace(/^(?:\.\/)?html\//i, "");
    }
    return `../${url.replace(/^\.\//, "")}`;
  }

  function renderInline(value, document) {
    const tokens = [];
    const token = (html) => {
      const marker = `\u0000BABTOKEN${tokens.length}\u0000`;
      tokens.push(html);
      return marker;
    };
    let working = value;
    working = working.replace(/`([^`]+)`/g, (_, code) => token(`<code>${escapeHtml(code)}</code>`));
    working = working.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, alt, target) => {
      const [url, title = ""] = target.trim().split(/\s+"/, 2);
      const cleanTitle = title ? title.replace(/"$/, "") : "";
      const source = imageSource(url);
      return token(`<img src="${escapeAttribute(source)}" alt="${escapeAttribute(alt)}"${cleanTitle ? ` title="${escapeAttribute(cleanTitle)}"` : ""}>`);
    });
    working = working.replace(/\[\[([^\]]+)\]\]\(([^)]+)\)/g, (_, reference, target) => token(
      linkHtml(`[${reference}]`, target.trim(), document, "reference-link")
    ));
    working = working.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, target) => token(linkHtml(label, target.trim(), document)));
    let rendered = escapeHtml(working)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<strong>$1</strong>")
      .replace(/~~([^~]+)~~/g, "<del>$1</del>")
      .replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>")
      .replace(/(^|[^_])_([^_]+)_/g, "$1<em>$2</em>");
    tokens.forEach((html, index) => {
      rendered = rendered.replace(`\u0000BABTOKEN${index}\u0000`, html);
    });
    return rendered;
  }

  function tableCells(line) {
    let normalized = line.trim();
    if (normalized.startsWith("|")) {
      normalized = normalized.slice(1);
    }
    if (normalized.endsWith("|")) {
      normalized = normalized.slice(0, -1);
    }
    return normalized.split("|").map((cell) => cell.trim());
  }

  function isTableDelimiter(line) {
    const cells = tableCells(line);
    return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
  }

  function isListLine(line) {
    return /^\s*(?:[-+*]|\d+\.)\s+/.test(line);
  }

  function isBlockStart(lines, index) {
    const line = lines[index] || "";
    const next = lines[index + 1] || "";
    return /^(?:#{1,6}\s+|```|>\s?|!\[[^\]]*\]\(|\s*(?:[-+*]|\d+\.)\s+|\s*(?:---+|\*\*\*+)\s*$)/.test(line)
      || (line.includes("|") && isTableDelimiter(next));
  }

  function renderMarkdown(markdown, document) {
    const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
    const output = [];
    const headingCounts = new Map();
    let index = 0;

    while (index < lines.length) {
      const line = lines[index];
      if (!line.trim()) {
        index += 1;
        continue;
      }

      const fence = line.match(/^```\s*([^\s`]*)\s*$/);
      if (fence) {
        const language = fence[1] || "text";
        const code = [];
        index += 1;
        while (index < lines.length && !/^```\s*$/.test(lines[index])) {
          code.push(lines[index]);
          index += 1;
        }
        if (index < lines.length) {
          index += 1;
        }
        output.push(`<div class="code-block"><span class="code-label">${escapeHtml(language)}</span><button class="copy-code" type="button" data-copy-code>Copy</button><pre><code class="language-${escapeAttribute(language)}">${escapeHtml(code.join("\n"))}</code></pre></div>`);
        continue;
      }

      const heading = line.match(/^(#{1,6})\s+(.+?)\s*$/);
      if (heading) {
        const level = heading[1].length;
        const text = heading[2].trim();
        const base = slugify(text);
        const occurrence = headingCounts.get(base) || 0;
        headingCounts.set(base, occurrence + 1);
        const identifier = occurrence === 0 ? base : `${base}-${occurrence + 1}`;
        output.push(`<h${level} id="${escapeAttribute(identifier)}"><a class="heading-anchor" href="${routeHash(document.path, identifier)}" data-doc-path="${escapeAttribute(document.path)}" data-section="${escapeAttribute(identifier)}" aria-label="Link to ${escapeAttribute(text)}">#</a>${renderInline(text, document)}</h${level}>`);
        index += 1;
        continue;
      }

      if (/^\s*(?:---+|\*\*\*+)\s*$/.test(line)) {
        output.push("<hr>");
        index += 1;
        continue;
      }

      const standaloneImage = line.trim().match(/^!\[([^\]]*)\]\((\S+?)(?:\s+"([^"]+)")?\)$/);
      if (standaloneImage) {
        const [, alt, url, caption = ""] = standaloneImage;
        const source = imageSource(url);
        const visibleCaption = caption || alt;
        output.push(`<figure class="diagram-frame document-figure"><img src="${escapeAttribute(source)}" alt="${escapeAttribute(alt)}" loading="lazy">${visibleCaption ? `<figcaption>${renderInline(visibleCaption, document)}</figcaption>` : ""}</figure>`);
        index += 1;
        continue;
      }

      if (line.includes("|") && index + 1 < lines.length && isTableDelimiter(lines[index + 1])) {
        const header = tableCells(line);
        index += 2;
        const rows = [];
        while (index < lines.length && lines[index].trim() && lines[index].includes("|")) {
          rows.push(tableCells(lines[index]));
          index += 1;
        }
        const headHtml = header.map((cell) => `<th>${renderInline(cell, document)}</th>`).join("");
        const bodyHtml = rows.map((row) => `<tr>${header.map((_, cellIndex) => `<td>${renderInline(row[cellIndex] || "", document)}</td>`).join("")}</tr>`).join("");
        output.push(`<div class="table-wrap"><table><thead><tr>${headHtml}</tr></thead><tbody>${bodyHtml}</tbody></table></div>`);
        continue;
      }

      if (/^>\s?/.test(line)) {
        const quoted = [];
        while (index < lines.length && /^>\s?/.test(lines[index])) {
          quoted.push(lines[index].replace(/^>\s?/, ""));
          index += 1;
        }
        output.push(`<blockquote>${renderMarkdown(quoted.join("\n"), document)}</blockquote>`);
        continue;
      }

      const listMatch = line.match(/^\s*([-+*]|\d+\.)\s+(.+)$/);
      if (listMatch) {
        const ordered = /\d+\./.test(listMatch[1]);
        const tag = ordered ? "ol" : "ul";
        const items = [];
        while (index < lines.length) {
          const itemMatch = lines[index].match(/^\s*([-+*]|\d+\.)\s+(.+)$/);
          if (!itemMatch || /\d+\./.test(itemMatch[1]) !== ordered) {
            break;
          }
          let item = itemMatch[2].trim();
          index += 1;
          while (index < lines.length && lines[index].trim() && !isBlockStart(lines, index) && !isListLine(lines[index])) {
            item += ` ${lines[index].trim()}`;
            index += 1;
          }
          items.push(`<li>${renderInline(item, document)}</li>`);
          if (index < lines.length && !lines[index].trim()) {
            break;
          }
        }
        output.push(`<${tag}>${items.join("")}</${tag}>`);
        continue;
      }

      const paragraph = [line.trim()];
      index += 1;
      while (index < lines.length && lines[index].trim() && !isBlockStart(lines, index)) {
        paragraph.push(lines[index].trim());
        index += 1;
      }
      output.push(`<p>${renderInline(paragraph.join(" "), document)}</p>`);
    }
    return output.join("\n");
  }

  function conceptsForDocument(document) {
    return (Array.isArray(document.conceptIds) ? document.conceptIds : [])
      .map((conceptId) => conceptsById.get(conceptId))
      .filter(Boolean);
  }

  function removeRepeatedHeroSummary(root, document) {
    const summary = (document.summary || "").replace(/…$/, "").replace(/\s+/g, " ").trim();
    if (!root || !summary) {
      return;
    }
    const repeatedParagraph = Array.from(root.querySelectorAll("p")).find((paragraph) => {
      const content = paragraph.textContent.replace(/\s+/g, " ").trim();
      return content === summary || content.startsWith(summary);
    });
    if (repeatedParagraph) {
      repeatedParagraph.remove();
    }
  }

  function conceptPattern(alias) {
    const escaped = alias.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const caseSensitive = /^[A-Z][A-Z0-9+_.-]*(?: [A-Z0-9+_.-]+)*$/.test(alias);
    return new RegExp(
      `(^|[^A-Za-z0-9_])(${escaped})(?=$|[^A-Za-z0-9_])`,
      caseSensitive ? "" : "i",
    );
  }

  function annotateConceptIntroductions(root, document, introducedConceptIds = new Set()) {
    if (!root) {
      return introducedConceptIds;
    }
    const concepts = conceptsForDocument(document)
      .filter((concept) => !introducedConceptIds.has(concept.id))
      .slice()
      .sort((left, right) => {
        const leftLength = Math.max(...left.aliases.map((alias) => alias.length));
        const rightLength = Math.max(...right.aliases.map((alias) => alias.length));
        return rightLength - leftLength;
      });
    const notesByBlock = new Map();
    concepts.forEach((concept) => {
      const aliases = concept.aliases.slice().sort((left, right) => right.length - left.length);
      let annotated = false;
      for (const alias of aliases) {
        const walker = window.document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        let node = walker.nextNode();
        while (node) {
          const parent = node.parentElement;
          if (parent && !parent.closest("h1, code, pre, a, abbr, .intext-learning-note")) {
            const match = node.nodeValue.match(conceptPattern(alias));
            if (match && Number.isInteger(match.index)) {
              const start = match.index + match[1].length;
              const end = start + match[2].length;
              const fragment = window.document.createDocumentFragment();
              fragment.append(node.nodeValue.slice(0, start));
              const abbreviation = window.document.createElement("abbr");
              abbreviation.className = "concept-introduction";
              abbreviation.dataset.conceptId = concept.id;
              abbreviation.title = concept.definition;
              abbreviation.tabIndex = 0;
              abbreviation.textContent = match[2];
              fragment.append(abbreviation);
              fragment.append(node.nodeValue.slice(end));
              const block = parent.closest("table")
                || parent.closest("p, li, dd, blockquote, h2, h3, h4, h5, h6")
                || parent;
              const notes = notesByBlock.get(block) || [];
              notes.push({ abbreviation, concept, matchedText: match[2] });
              notesByBlock.set(block, notes);
              node.replaceWith(fragment);
              introducedConceptIds.add(concept.id);
              annotated = true;
              break;
            }
          }
          node = walker.nextNode();
        }
        if (annotated) {
          break;
        }
      }
    });
    let noteIndex = window.document.querySelectorAll(".intext-learning-note").length;
    notesByBlock.forEach((notes, block) => {
      notes.sort((left, right) => {
        const content = block.textContent.toLowerCase();
        return content.indexOf(left.matchedText.toLowerCase()) - content.indexOf(right.matchedText.toLowerCase());
      });
      const note = window.document.createElement("aside");
      note.className = "intext-learning-note";
      note.id = `intext-learning-note-${noteIndex}`;
      note.setAttribute("role", "note");
      const label = window.document.createElement("span");
      label.className = "intext-learning-label";
      label.textContent = "Plain words";
      note.append(label);
      const definitions = window.document.createElement("span");
      definitions.className = "intext-learning-definitions";
      notes.forEach(({ abbreviation, concept }, index) => {
        const entry = window.document.createElement("span");
        entry.className = "intext-learning-definition";
        const term = window.document.createElement("strong");
        term.textContent = concept.term;
        entry.append(term, ` — ${concept.definition}`);
        definitions.append(entry);
        if (index < notes.length - 1) {
          definitions.append(" ");
        }
        abbreviation.setAttribute("aria-describedby", note.id);
        abbreviation.setAttribute("aria-label", `${abbreviation.textContent}. ${concept.definition}`);
      });
      note.append(definitions);
      if (block.tagName === "TABLE") {
        const tableContainer = block.closest(".table-wrap") || block;
        tableContainer.insertAdjacentElement("beforebegin", note);
      } else if (["LI", "DD"].includes(block.tagName)) {
        block.append(note);
      } else {
        block.insertAdjacentElement("afterend", note);
      }
      noteIndex += 1;
    });
    return introducedConceptIds;
  }

  function renderTree() {
    const query = state.searchQuery.trim().toLowerCase();
    if (query) {
      renderSearchResults(query);
      return;
    }
    elements.count.textContent = `${library.documentCount} Markdown documents`;
    elements.clearSearch.hidden = true;
    elements.tree.innerHTML = library.categories.map((category) => {
      const links = category.documents.map((path) => {
        const document = documentsByPath.get(path);
        if (!document) {
          return "";
        }
        const active = state.current && state.current.path === path ? " active" : "";
        return `<button class="tree-link${active}" type="button" data-open-document="${escapeAttribute(path)}"><span class="tree-link-copy"><span class="tree-link-title">${escapeHtml(document.title)}</span><span class="tree-link-kind">${escapeHtml(document.kind || "Guide")}</span></span><small>${document.readingMinutes} min</small></button>`;
      }).join("");
      const open = state.current && state.current.category === category.name ? " open" : category.name === "Documentation Home" ? " open" : "";
      return `<details class="tree-group"${open}><summary><span>${escapeHtml(category.name)}</span><small>${category.documents.length}</small></summary>${links}</details>`;
    }).join("");
  }

  function searchScore(document, terms) {
    const title = document.title.toLowerCase();
    const path = document.path.toLowerCase();
    const summary = document.summary.toLowerCase();
    const content = document.markdown.toLowerCase();
    let score = 0;
    for (const term of terms) {
      if (!content.includes(term) && !title.includes(term) && !path.includes(term)) {
        return -1;
      }
      if (title === term) score += 120;
      if (title.startsWith(term)) score += 70;
      if (title.includes(term)) score += 45;
      if (path.includes(term)) score += 25;
      if (summary.includes(term)) score += 18;
      if (content.includes(term)) score += 5;
    }
    return score;
  }

  function highlighted(value, terms) {
    let rendered = escapeHtml(value);
    for (const term of terms) {
      const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      rendered = rendered.replace(new RegExp(`(${escaped})`, "ig"), "<mark>$1</mark>");
    }
    return rendered;
  }

  function renderSearchResults(query) {
    const terms = query.split(/\s+/).filter(Boolean);
    const results = library.documents
      .map((document) => ({ document, score: searchScore(document, terms) }))
      .filter((item) => item.score >= 0)
      .sort((left, right) => right.score - left.score || left.document.title.localeCompare(right.document.title));
    elements.count.textContent = `${results.length} result${results.length === 1 ? "" : "s"}`;
    elements.clearSearch.hidden = false;
    if (!results.length) {
      elements.tree.innerHTML = '<div class="empty-state">No documentation matches this search.</div>';
      return;
    }
    elements.tree.innerHTML = `<p class="search-results-label">Search results</p>${results.map(({ document }) => {
      const active = state.current && state.current.path === document.path ? " active" : "";
      const summary = document.summary || `${document.wordCount.toLocaleString()} words in ${document.category}`;
      return `<button class="search-result${active}" type="button" data-open-document="${escapeAttribute(document.path)}"><strong>${highlighted(document.title, terms)}</strong><span>${highlighted(summary, terms)}</span></button>`;
    }).join("")}`;
  }

  function renderToc(document, additionalHeadings = []) {
    const headings = additionalHeadings.concat(
      document.headings.filter((heading) => heading.level >= 2 && heading.level <= 4)
    );
    elements.toc.innerHTML = headings.length
      ? headings.map((heading) => `<a class="depth-${heading.level}" href="${routeHash(document.path, heading.id)}" data-doc-path="${escapeAttribute(document.path)}" data-section="${escapeAttribute(heading.id)}">${escapeHtml(heading.text)}</a>`).join("")
      : '<span class="empty-state">No subsections</span>';
    updateTocProgress(headings.length ? 0 : -1, headings.length);
    observeHeadings(headings);
  }

  function updateTocProgress(index, total) {
    const current = total && index >= 0 ? index + 1 : 0;
    elements.tocProgress.textContent = `${current} / ${total}`;
    elements.tocProgress.setAttribute(
      "aria-label",
      total ? `Section ${current} of ${total}` : "No subsections",
    );
  }

  function observeHeadings(headings) {
    if (state.headingObserver) {
      state.headingObserver.disconnect();
    }
    if (!("IntersectionObserver" in window) || !headings.length) {
      return;
    }
    const tocLinks = new Map(Array.from(elements.toc.querySelectorAll("a")).map((link) => [link.dataset.section, link]));
    state.headingObserver = new IntersectionObserver((entries) => {
      const visible = entries.filter((entry) => entry.isIntersecting).sort((left, right) => left.boundingClientRect.top - right.boundingClientRect.top);
      if (!visible.length) {
        return;
      }
      tocLinks.forEach((link) => link.classList.remove("active"));
      const link = tocLinks.get(visible[0].target.id);
      if (link) {
        link.classList.add("active");
        updateTocProgress(
          headings.findIndex((heading) => heading.id === visible[0].target.id),
          headings.length,
        );
      }
    }, { rootMargin: "-80px 0px -70% 0px", threshold: [0, 1] });
    headings.forEach((heading) => {
      const target = document.getElementById(heading.id);
      if (target) {
        state.headingObserver.observe(target);
      }
    });
  }

  function attachCodeActions() {
    elements.content.querySelectorAll("[data-copy-code]").forEach((button) => {
      button.addEventListener("click", async () => {
        const code = button.closest(".code-block").querySelector("code").textContent;
        await copyText(code);
        button.textContent = "Copied";
        window.setTimeout(() => { button.textContent = "Copy"; }, 1200);
      });
    });
  }

  function dashboardLink(path, label, className = "") {
    const classAttribute = className ? ` class="${escapeAttribute(className)}"` : "";
    return `<a${classAttribute} href="${escapeAttribute(routeHash(path, ""))}" data-doc-path="${escapeAttribute(path)}">${escapeHtml(label)}</a>`;
  }

  function externalLink(target, label, className = "") {
    const classAttribute = className ? ` class="${escapeAttribute(className)}"` : "";
    return `<a${classAttribute} href="${escapeAttribute(target)}" target="_blank" rel="noreferrer">${escapeHtml(label)}</a>`;
  }

  function dashboardSectionLink(section, label, className = "") {
    const classAttribute = className ? ` class="${escapeAttribute(className)}"` : "";
    return `<a${classAttribute} href="${escapeAttribute(routeHash("index.md", section))}" data-doc-path="index.md" data-section="${escapeAttribute(section)}">${escapeHtml(label)}</a>`;
  }

  function applyProjectFilter(filter) {
    state.projectFilter = filter;
    let visible = 0;
    elements.landing.querySelectorAll("[data-project-domains]").forEach((card) => {
      const domains = card.dataset.projectDomains.split(" ");
      const matches = filter === "all" || domains.includes(filter);
      card.hidden = !matches;
      if (matches) {
        visible += 1;
      }
    });
    elements.landing.querySelectorAll("[data-project-filter]").forEach((button) => {
      const active = button.dataset.projectFilter === filter;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    const count = elements.landing.querySelector("[data-project-count]");
    if (count) {
      count.textContent = `${visible} engineering project${visible === 1 ? "" : "s"}`;
    }
  }

  function renderLandingDashboard() {
    const metrics = library.siteMetrics;
    const engineeringProjects = [
      {
        domains: ["power", "verification"],
        label: "Power Conversion",
        title: "Buck-converter control schedule screening",
        challenge: "Compare numerical methods while preserving switch-event alignment, continuous inductor current, output ripple, diode conduction, and energy accounting.",
        fit: "BAB-CS can supervise a reduced-order resistor-inductor-capacitor (RLC) model—a simplified circuit that keeps the behavior needed for this question—with event-forced replay and repeatable work reports.",
        outputs: ["event evidence", "ripple", "energy", "fixed work"],
        boundary: "Reduced-order numerical experiment; not a production semiconductor, magnetic, electromagnetic-interference, or thermal model.",
        path: "POWER_STAGE_SANDBOX.md",
      },
      {
        domains: ["power", "verification"],
        label: "Drives and Switching",
        title: "H-bridge dead-time and resistor-inductor load reversal",
        challenge: "Verify positive and negative load-voltage schedules, dead-time intervals when opposing switches are both off, current continuity, history resets, and rejected steps around switching boundaries.",
        fit: "BAB-CS exposes event timing, replay work, fallback causes, and accepted-state authority across the scheduled four-switch bridge abstraction.",
        outputs: ["dead time", "polarity", "replay", "rejections"],
        boundary: "No body-diode, shoot-through, gate-driver, motor, or parasitic-device fidelity is implied.",
        path: "POWER_STAGE_SANDBOX.md",
      },
      {
        domains: ["power", "verification"],
        label: "Power Integrity",
        title: "Direct-current link startup and interruption qualification",
        challenge: "Study startup inrush, stored energy, interruption decay, event boundaries, and numerical-method robustness for a simplified resistor-inductor-capacitor link with a declared path for continuing current.",
        fit: "BAB-CS combines refined-replay authority, phase and energy diagnostics, anchor evidence, and exact configuration provenance.",
        outputs: ["startup", "interruption", "energy decay", "anchors"],
        boundary: "Not a contactor, protection, battery, fault-current, insulation, or hardware-safety model.",
        path: "POWER_STAGE_SANDBOX.md",
      },
      {
        domains: ["analog", "verification"],
        label: "Analog Protection",
        title: "Diode-clamped sensor or interface transient",
        challenge: "Compare how proposed numerical methods handle nonlinear clipping, equation mismatch, iterative convergence, rapidly changing behavior, reference promotion, and error under smaller timesteps.",
        fit: "BAB-CS provides a bounded idealized diode experiment with visible nonlinear iteration, correction, safer-method fallback, and a mapped comparison with ngspice.",
        outputs: ["clipping", "residuals", "fallback", "ngspice"],
        boundary: "Use a specialist SPICE workflow for package parasitics, temperature corners, manufacturer macromodels, and production sign-off.",
        path: "EXTERNAL_COMPARISON.md",
      },
      {
        domains: ["analog", "verification"],
        label: "Resonant Systems",
        title: "Inductor-capacitor phase and energy retention study",
        challenge: "Separate phase error—the timing shift of an oscillation—from energy drift—the numerical gain or loss of stored energy—over long simulations.",
        fit: "BAB-CS reports phase, energy, recursive bounds, time since independent checking, and replay effects separately rather than hiding them inside one error score.",
        outputs: ["phase", "energy", "long horizon", "replay"],
        boundary: "The study qualifies the declared lumped model and numerical authority, not losses or parasitics absent from that model.",
        path: "BOUND_COVERAGE_ATLAS.md",
      },
      {
        domains: ["verification"],
        label: "Numerical Architecture",
        title: "Numerical-method selection for a simplified digital twin",
        challenge: "Choose a proposed numerical method under a fixed timestep, fixed accuracy target, or fixed work budget without letting that method approve its own result.",
        fit: "The Method Observatory runs all seven proposed methods under one controller and preserves the exact measured row used for each selection.",
        outputs: ["method matrix", "accuracy", "work", "evidence origin"],
        boundary: "A simplified simulation component is not automatically a validated digital twin, meaning a trusted software representation of an operating physical system.",
        path: "METHOD_OBSERVATORY.md",
      },
      {
        domains: ["verification"],
        label: "Software Qualification",
        title: "Solver, dependency, or packaging regression qualification",
        challenge: "Determine whether a numerical backend, source change, or wheel build altered trajectories, diagnostics, work counts, or accepted authority.",
        fit: "BAB-CS couples deterministic outputs with source hashes, installed-wheel isolation, source-versus-wheel equivalence, and fail-closed qualification gates.",
        outputs: ["regression", "hashes", "wheel", "determinism"],
        boundary: "Passing the repository suite is engineering evidence, not independent certification or release approval.",
        path: "TEACHING_AND_REPRODUCIBILITY_LAB.md",
      },
      {
        domains: ["education"],
        label: "Engineering Education",
        title: "Reproducible circuit-equation and convergence laboratory",
        challenge: "Teach how circuit equations, error reduction under smaller timesteps, phase, energy, observe-only candidate execution, packaging, and evidence origin interact.",
        fit: "The six-exercise lab moves from modified nodal analysis—a standard way to turn a circuit into equations—to isolated installed-package equivalence with reviewed fixtures.",
        outputs: ["circuit equations", "convergence", "phase/energy", "reproducibility"],
        boundary: "Exercises demonstrate declared numerical concepts; they do not substitute for device-design or safety-validation training.",
        path: "TEACHING_AND_REPRODUCIBILITY_LAB.md",
      },
    ];
    const projectCards = engineeringProjects.map((project, index) => `
      <article class="engineering-project-card" data-project-domains="${escapeAttribute(project.domains.join(" "))}">
        <div class="project-card-heading">
          <span class="project-number">${String(index + 1).padStart(2, "0")}</span>
          <p class="project-domain">${escapeHtml(project.label)}</p>
        </div>
        <h3>${escapeHtml(project.title)}</h3>
        <dl class="project-detail-list">
          <div><dt>Engineering challenge</dt><dd>${escapeHtml(project.challenge)}</dd></div>
          <div><dt>Why BAB-CS fits</dt><dd>${escapeHtml(project.fit)}</dd></div>
        </dl>
        <div class="project-output-row">${project.outputs.map((output) => `<span>${escapeHtml(output)}</span>`).join("")}</div>
        <p class="project-boundary"><strong>Boundary:</strong> ${escapeHtml(project.boundary)}</p>
        ${dashboardLink(project.path, "Open supporting documentation", "card-link")}
      </article>`).join("");
    const externalCases = metrics.external.caseIds
      .map((caseId) => `<span class="case-chip">${escapeHtml(caseId)}</span>`)
      .join("");
    const evidenceCards = [
      [metrics.tests.methods, "test methods", `${metrics.tests.modules} syntax-inspected modules`],
      [metrics.comparison.matrixRows, "comparison rows", `${metrics.comparison.cases} canonical cases · ${metrics.comparison.methods} methods`],
      [metrics.observatory.matrixRows, "observatory rows", `${metrics.observatory.cases} cases · ${metrics.observatory.methods} bounded candidates`],
      [metrics.powerStage.matrixRows, "sandbox rows", `${metrics.powerStage.cases} reduced-order numerical experiments`],
      [metrics.external.cases, "ngspice cases", "scheduled cross-implementation evidence"],
      [metrics.teachingLab.exercises, "lab exercises", "modified nodal analysis through source/wheel equivalence"],
    ].map(([value, label, detail]) => `
      <article class="metric-card">
        <strong>${Number(value).toLocaleString()}</strong>
        <span>${escapeHtml(label)}</span>
        <small>${escapeHtml(detail)}</small>
      </article>`).join("");

    elements.landing.innerHTML = `
      <div class="landing-actions" aria-label="Engineering starting points">
        ${dashboardSectionLink("overview-projects", "Explore engineering projects", "primary-link")}
        ${dashboardSectionLink("overview-software", "Compare simulation software", "secondary-link")}
        ${dashboardLink("POWER_STAGE_SANDBOX.md", "Open the power-stage sandbox", "secondary-link")}
      </div>

      <section class="overview-section language-section" id="overview-language">
        <div class="section-heading split-heading">
          <div>
            <p class="eyebrow">Plain-Language Guide</p>
            <h2>Understand the authority model before reading the measurements</h2>
          </div>
          <p>Bounded-Authority-Based-Circuit-Simulation (BAB-CS) is a circuit-simulation architecture in which a fast numerical method may propose the next state, but separate checks decide whether that state can become the official result.</p>
        </div>
        <div class="concept-grid">
          <article><h3>Candidate method</h3><p>The numerical formula that proposes the next capacitor voltages and inductor currents. It is useful, but it does not approve itself.</p></article>
          <article><h3>Numerical authority</h3><p>The independent calculation and rules that decide whether a proposed timestep is accepted, corrected, recomputed, or rejected.</p></article>
          <article><h3>Projection</h3><p>A circuit-equation solve that adjusts a proposed dynamic state so node voltages and branch currents satisfy the model’s electrical constraints.</p></article>
          <article><h3>Replay</h3><p>An independent recomputation of a recent interval with a trusted implicit method, meaning a method that solves the new state as part of its own equations.</p></article>
          <article><h3>Reduced-order model</h3><p>A deliberately simplified model that retains only the behavior needed for the engineering question. It is not a production device model.</p></article>
          <article><h3>Deterministic evidence</h3><p>Results whose important files, work counts, and hashes are repeatable for the same declared source, configuration, and environment.</p></article>
        </div>
      </section>

      <section class="overview-section" id="overview-challenges">
        <div class="section-heading split-heading">
          <div>
            <p class="eyebrow">Engineering Challenges</p>
            <h2>Use simulation evidence to support decisions, not merely generate waveforms</h2>
          </div>
          <p>BAB-CS is suited to simplified circuit studies where switching time, numerical-method choice, nonlinear-solve success, oscillation timing, stored energy, safer-method fallback, or reproducible delivery must remain visible to engineering review.</p>
        </div>
        <div class="engineering-capability-grid">
          <article><span>01</span><h3>Power conversion</h3><p>Screen switching schedules, ripple, continuity, startup, interruption, and stored-energy behavior before moving to detailed device and thermal models.</p></article>
          <article><span>02</span><h3>Analog transients</h3><p>Study resistor-capacitor, resistor-inductor, resonant, and diode-limited behavior with visible convergence, equation mismatch, phase, energy, and authority evidence.</p></article>
          <article><span>03</span><h3>Numerical qualification</h3><p>Compare proposed integration formulas under a fixed timestep, accuracy target, or work budget while independent methods control the accepted state.</p></article>
          <article><span>04</span><h3>Reproducible delivery</h3><p>Package source, the installable Python wheel, tests, file fingerprints, diagnostics, external checks, and claim boundaries into one repeatable engineering record.</p></article>
        </div>
      </section>

      <section class="overview-section" id="overview-projects">
        <div class="section-heading">
          <p class="eyebrow">Engineering Project Portfolio</p>
          <h2>Projects well suited to BAB-CS</h2>
          <p>Each project below uses the implemented circuit and authority surface. Filters organize the portfolio by engineering domain; every card states both the expected evidence and the boundary that must remain visible.</p>
        </div>
        <div class="project-toolbar">
          <div class="project-filters" role="group" aria-label="Filter engineering projects">
            <button type="button" data-project-filter="all" aria-pressed="true">All projects</button>
            <button type="button" data-project-filter="power" aria-pressed="false">Power conversion</button>
            <button type="button" data-project-filter="analog" aria-pressed="false">Analog transients</button>
            <button type="button" data-project-filter="verification" aria-pressed="false">Verification</button>
            <button type="button" data-project-filter="education" aria-pressed="false">Education</button>
          </div>
          <span class="project-count" data-project-count>${engineeringProjects.length} engineering projects</span>
        </div>
        <div class="engineering-project-grid">${projectCards}</div>
      </section>

      <section class="overview-section" id="overview-workflow">
        <div class="section-heading split-heading">
          <div>
            <p class="eyebrow">Engineering Workflow</p>
            <h2>Carry numerical authority from the question to the decision package</h2>
          </div>
          <p>The recommended workflow begins with a bounded abstraction and ends with a reproducible evidence package. Specialist simulation tools enter when the project needs broader models, multidomain fidelity, deployment, or scale.</p>
        </div>
        <figure class="diagram-frame featured-diagram">
          <img src="assets/engineering-workflow.svg" width="1200" height="650" alt="Engineering workflow from challenge definition through bounded modeling, candidate comparison, authority evidence, external challenge, and reproducible delivery">
          <figcaption>BAB-CS connects the engineering question to the exact model, authority chain, comparison row, external check, and claim boundary used to support the decision.</figcaption>
        </figure>
        <figure class="diagram-frame compact-diagram">
          <img src="assets/authority-loop.svg" width="1200" height="650" alt="BAB-CS authority loop from candidate integration through projection, independent authority, correction, acceptance, replay, and fail-closed fallback">
          <figcaption>Within each run, the candidate proposes work while independent evidence controls accepted state, fallback, rejection, and replay.</figcaption>
        </figure>
        <div class="comparison-actions">
          ${dashboardLink("ARCHITECTURE.md", "Inspect the authority architecture", "text-link")}
          ${dashboardLink("ERROR_BOUND_MODEL.md", "Review the error-bound model", "text-link")}
        </div>
      </section>

      <section class="overview-section comparison-section" id="overview-software">
        <div class="section-heading split-heading">
          <div>
            <p class="eyebrow">Simulation Software Landscape</p>
            <h2>BAB-CS complements specialist engineering simulators</h2>
          </div>
          <p>The comparison below follows each product’s official emphasis. It is a workflow map, not a ranking: it identifies where BAB-CS adds inspectable numerical governance and where another simulator is the better primary environment. SPICE means Simulation Program with Integrated Circuit Emphasis, the widely used family of circuit-simulation methods and tools.</p>
        </div>
        <figure class="diagram-frame">
          <img src="assets/software-landscape.svg" width="1200" height="720" alt="Role map for BAB-CS, ngspice and LTspice, PLECS, Simscape Electrical, and Xyce across an engineering program">
          <figcaption>Use the tools as complementary layers: BAB-CS for bounded numerical experiments and evidence; specialist simulators for device breadth, power-electronics systems, multiple physical domains, hardware-in-the-loop testing, or very large circuits.</figcaption>
        </figure>
        <div class="comparison-table-wrap">
          <table class="comparison-table software-comparison-table">
            <thead>
              <tr><th>Software</th><th>Official emphasis</th><th>Relationship to BAB-CS</th><th>Prefer this environment when</th></tr>
            </thead>
            <tbody>
              <tr><th>BAB-CS</th><td>Proposed-step integration, independent acceptance authority, replay, diagnostics, deterministic work counts, and reproducibility.</td><td>Primary environment for supervising numerical methods and studying evidence-focused simplified models.</td><td>The engineering decision depends on why a timestep passed, changed authority, was recomputed, or failed.</td></tr>
              <tr><th>${externalLink("https://ngspice.sourceforge.io/", "ngspice", "official-product-link")}</th><td>Open-source SPICE simulation spanning device-level, behavioral, analog, and digital interactions, with scripting and shared-library capabilities.</td><td>Current BAB-CS external comparison target for equivalent mapped cases.</td><td>You need broader SPICE analyses, device models, analog-and-digital capabilities, scripting, or an independent implementation check.</td></tr>
              <tr><th>${externalLink("https://www.analog.com/en/resources/design-tools-and-calculators/ltspice-simulator.html", "LTspice", "official-product-link")}</th><td>SPICE simulation, graphical schematic capture, waveform viewing, and Analog Devices models and demo circuits.</td><td>Complementary device-design and schematic workflow; not a BAB-CS authority source.</td><td>You need interactive analog design, vendor-supplied reusable device models, schematic probing, and waveform exploration.</td></tr>
              <tr><th>${externalLink("https://www.plexim.com/products", "PLECS", "official-product-link")}</th><td>Complete power-electronics systems with controls, switching events, nonlinear elements, thermal management, code generation, and hardware-in-the-loop workflows, where real controller hardware is tested against a simulated plant.</td><td>Natural next stage after a BAB-CS simplified converter or switching-schedule qualification.</td><td>You need system-level power-converter design, detailed controls, thermal behavior, deployment, or real-time testing.</td></tr>
              <tr><th>${externalLink("https://www.mathworks.com/products/simscape-electrical.html", "Simscape Electrical", "official-product-link")}</th><td>Electronic, mechatronic, and electrical power systems including semiconductors, motors, grids, multiple physical domains, controls, and hardware-in-the-loop testing.</td><td>Broader system-integration environment for plants whose physics extend beyond the BAB-CS circuit abstraction.</td><td>You need mechanical, thermal, hydraulic, grid, motor, control, virtual-test, or hardware-in-the-loop integration.</td></tr>
              <tr><th>${externalLink("https://xyce.sandia.gov/", "Xyce", "official-product-link")}</th><td>Open-source, SPICE-compatible high-performance analog simulation for extremely large circuits on one processor or many processors working together.</td><td>Complementary scale-oriented simulator; not currently a repository-integrated BAB-CS comparison adapter.</td><td>You need very large circuit problems or parallel execution, meaning work divided across processors, beyond the intended BAB-CS qualification scale.</td></tr>
            </tbody>
          </table>
        </div>
        <figure class="diagram-frame compact-diagram">
          <img src="assets/external-comparison.svg" width="1200" height="720" alt="Role comparison among raw candidate methods, BAB-CS active supervision, internal implicit authority, and mapped ngspice simulation">
          <figcaption>Within the current repository, ngspice supplies cross-implementation evidence for equivalent mapped cases. It is not an oracle and never becomes BAB-CS accepted-state authority.</figcaption>
        </figure>
        <figure class="diagram-frame">
          <img src="assets/speedup-accuracy-by-size-blueprint.svg" width="1200" height="720" alt="Non-measured blueprint placing BAB-CS speedup versus ngspice beside trajectory accuracy against the same circuit-size ordering">
          <figcaption>Benchmark chart blueprint only: the left panel makes speedup and the 1× parity boundary obvious; the right panel keeps BAB-CS and ngspice trajectory error visible beside it. Schematic marks are not measurements.</figcaption>
        </figure>
        <div class="external-case-row" aria-label="Scheduled BAB-CS external comparison cases">
          <span>Current ngspice mapped set</span>${externalCases}
        </div>
        <div class="comparison-actions">
          ${dashboardLink("EXTERNAL_COMPARISON.md", "Read the ngspice translation contract", "text-link")}
          ${dashboardLink("COMPARISON_PROTOCOL.md", "Review the full comparison protocol", "text-link")}
        </div>
      </section>

      <section class="overview-section" id="overview-evidence">
        <div class="section-heading">
          <p class="eyebrow">Engineering Evidence Surface</p>
          <h2>Qualification counts come from canonical repository owners</h2>
          <p>The site derives these values from Python test syntax, benchmark manifests, scheduled comparison configuration, the teaching lab, and the complete Markdown tree. They describe coverage and evidence volume—not certification or universal performance.</p>
        </div>
        <div class="metric-grid">${evidenceCards}</div>
        <figure class="diagram-frame">
          <img src="assets/qualification-surface.svg" width="1200" height="690" alt="Graph of current BAB-CS tests, comparison rows, observatory rows, sandbox rows, documents, lab exercises, and mapped ngspice cases">
          <figcaption>The measured surface supports engineering review of the declared models, methods, and artifacts while keeping timing and universal-accuracy claims out of qualification gates.</figcaption>
        </figure>
        <figure class="diagram-frame compact-diagram">
          <img src="assets/evidence-hierarchy.svg" width="1200" height="610" alt="BAB-CS evidence hierarchy separating analytic, replay, implicit, external, anchor, and packaging evidence">
          <figcaption>Analytic truth, refined replay, local implicit authority, external simulation, anchor evidence, and packaging equivalence retain distinct engineering roles.</figcaption>
        </figure>
      </section>

      <section class="overview-section boundary-section" id="overview-boundary">
        <div>
          <p class="eyebrow">Engineering Claim Boundary</p>
          <h2>Use BAB-CS where its authority model adds value—and hand off when fidelity requirements grow</h2>
        </div>
        <p>BAB-CS does not replace production semiconductor models, parasitic extraction, thermal or electromagnetic analysis, plants spanning multiple kinds of physics, hardware-in-the-loop deployment, or large-scale parallel SPICE. Its strongest role is to make simplified transient experiments, proposed-method behavior, accepted-state authority, and reproducible evidence inspectable before and alongside those specialist workflows.</p>
      </section>

      <div class="documentation-map-intro">
        <p class="eyebrow">Complete Documentation Tree</p>
        <h2>Continue from the engineering portfolio into implementation evidence</h2>
        <p>The full generated tree follows, preserving direct links, headings, citations, source paths, reading estimates, and deterministic content hashes for every Markdown document.</p>
      </div>`;
    elements.landing.hidden = false;
    applyProjectFilter("all");
    return homeHeadings;
  }

  function renderDocument(doc, options = {}) {
    state.current = doc;
    const section = options.section || "";
    const updateHistory = options.updateHistory !== false;
    const isHome = doc.path === "index.md";
    elements.hero.classList.toggle("home-hero", isHome);
    elements.heroCritical.hidden = !isHome;
    elements.hero.querySelectorAll(".intext-learning-note").forEach((note) => note.remove());
    elements.content.classList.toggle("documentation-map", isHome);
    elements.category.textContent = isHome ? "Engineering Simulation with Bounded Authority" : doc.category;
    elements.title.textContent = isHome
      ? "Make engineering simulation decisions with numerical authority you can defend."
      : doc.title;
    elements.summary.textContent = isHome
      ? "Bounded-Authority-Based-Circuit-Simulation (BAB-CS) addresses a critical engineering problem: a waveform can look plausible even when event timing, nonlinear convergence, accumulated phase, stored energy, or packaged software has drifted. BAB-CS keeps the proposed step, the independent acceptance decision, and the resulting evidence visible."
      : doc.summary;
    elements.meta.innerHTML = isHome
      ? [
        `<span>${library.siteMetrics.observatory.methods} bounded candidates</span>`,
        `<span>${library.siteMetrics.observatory.cases} observatory circuits</span>`,
        `<span>${library.siteMetrics.external.cases} mapped external cases</span>`,
        `<span>${library.documentCount} embedded documents</span>`,
      ].join("")
      : [
        `<span>${escapeHtml(doc.path)}</span>`,
        `<span>${doc.wordCount.toLocaleString()} words</span>`,
        `<span>${doc.readingMinutes} min read</span>`,
        `<span>SHA ${doc.sha256.slice(0, 12)}</span>`,
      ].join("");
    elements.breadcrumbs.innerHTML = isHome
      ? "<span>BAB-CS</span><span class=\"separator\">/</span><span>Engineering applications and simulator landscape</span>"
      : `<span>${escapeHtml(doc.category)}</span><span class="separator">/</span><span>${escapeHtml(doc.title)}</span>`;
    elements.landing.hidden = true;
    elements.landing.innerHTML = "";
    const additionalHeadings = isHome ? renderLandingDashboard() : [];
    elements.content.innerHTML = `<div class="document-prose">${renderMarkdown(doc.markdown, doc)}</div>`;
    const documentProse = elements.content.querySelector(".document-prose");
    const introducedConceptIds = isHome
      ? new Set()
      : annotateConceptIntroductions(elements.summary, doc);
    if (!isHome) {
      removeRepeatedHeroSummary(documentProse, doc);
    }
    annotateConceptIntroductions(documentProse, doc, introducedConceptIds);
    elements.footer.innerHTML = `Source: <code>docs/${escapeHtml(doc.path)}</code> · Documentation SHA <code>${library.sourceSha256.slice(0, 12)}</code> · Evidence-owner SHA <code>${library.siteMetrics.sourceSha256.slice(0, 12)}</code>.`;
    document.title = isHome ? "BAB-CS · Engineering Applications and Simulation Evidence" : `${doc.title} · BAB-CS Documentation`;
    renderToc(doc, additionalHeadings);
    renderTree();
    attachCodeActions();
    try {
      window.localStorage.setItem("babcs-doc-path", doc.path);
    } catch (_) {
      void 0;
    }
    if (updateHistory) {
      window.history.pushState(null, "", routeHash(doc.path, section));
    }
    const target = section ? window.document.getElementById(section) : null;
    scrollDocumentTarget(target, options.instant === true);
    window.requestAnimationFrame(updateReadingProgress);
    closeSidebar();
  }

  function openPath(path, section, options = {}) {
    const doc = documentsByPath.get(path) || documentsByPath.get("index.md") || library.documents[0];
    renderDocument(doc, { ...options, section });
  }

  function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.add("visible");
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => elements.toast.classList.remove("visible"), 1800);
  }

  async function copyText(value) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }

  function closeSidebar() {
    elements.body.classList.remove("sidebar-open");
  }

  function setTheme(theme) {
    document.documentElement.dataset.theme = theme;
    elements.themeToggle.setAttribute("aria-label", theme === "dark" ? "Use light theme" : "Use dark theme");
    try {
      window.localStorage.setItem("babcs-doc-theme", theme);
    } catch (_) {
      void 0;
    }
  }

  function initialTheme() {
    try {
      const stored = window.localStorage.getItem("babcs-doc-theme");
      if (stored === "light" || stored === "dark") {
        return stored;
      }
    } catch (_) {
      void 0;
    }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function updateReadingProgress() {
    const stageBottom = elements.stage.getBoundingClientRect().bottom + window.scrollY;
    const stageTop = elements.stage.getBoundingClientRect().top + window.scrollY;
    const available = Math.max(1, stageBottom - stageTop - window.innerHeight);
    const progress = Math.max(0, Math.min(1, (window.scrollY - stageTop) / available));
    elements.progress.style.width = `${progress * 100}%`;
    elements.stageProgress.style.width = `${progress * 100}%`;
  }

  function scrollDocumentTarget(target, instant) {
    if (instant) {
      const root = window.document.documentElement;
      const previousBehavior = root.style.scrollBehavior;
      root.style.scrollBehavior = "auto";
      if (target) {
        target.scrollIntoView({ block: "start" });
      } else {
        window.scrollTo(0, 0);
      }
      root.style.scrollBehavior = previousBehavior;
      return;
    }
    if (target) {
      target.scrollIntoView({ block: "start", behavior: "smooth" });
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  elements.tree.addEventListener("click", (event) => {
    const button = event.target.closest("[data-open-document]");
    if (button) {
      openPath(button.dataset.openDocument, "");
    }
  });

  elements.content.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-doc-path]");
    if (!link) {
      return;
    }
    event.preventDefault();
    openPath(link.dataset.docPath, link.dataset.section || "");
  });

  elements.landing.addEventListener("click", (event) => {
    const filterButton = event.target.closest("[data-project-filter]");
    if (filterButton) {
      applyProjectFilter(filterButton.dataset.projectFilter);
      return;
    }
    const link = event.target.closest("a[data-doc-path]");
    if (!link) {
      return;
    }
    event.preventDefault();
    openPath(link.dataset.docPath, link.dataset.section || "");
  });

  elements.toc.addEventListener("click", (event) => {
    const link = event.target.closest("a[data-doc-path]");
    if (!link) {
      return;
    }
    event.preventDefault();
    openPath(link.dataset.docPath, link.dataset.section || "");
  });

  elements.search.addEventListener("input", () => {
    state.searchQuery = elements.search.value;
    renderTree();
  });

  elements.clearSearch.addEventListener("click", () => {
    elements.search.value = "";
    state.searchQuery = "";
    renderTree();
    elements.search.focus();
  });

  elements.themeToggle.addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });

  elements.print.addEventListener("click", () => window.print());

  elements.copyLink.addEventListener("click", async () => {
    await copyText(window.location.href);
    showToast("Document link copied");
  });

  elements.sidebarToggle.addEventListener("click", () => elements.body.classList.add("sidebar-open"));
  elements.sidebarScrim.addEventListener("click", closeSidebar);

  window.addEventListener("hashchange", () => {
    const route = parseRoute();
    openPath(route.path || "index.md", route.section || "", { updateHistory: false, instant: true });
  });

  window.addEventListener("scroll", updateReadingProgress, { passive: true });
  window.addEventListener("resize", updateReadingProgress);

  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && !/input|textarea|select/i.test(document.activeElement.tagName)) {
      event.preventDefault();
      elements.search.focus();
    }
    if (event.key === "Escape") {
      closeSidebar();
      if (document.activeElement === elements.search && elements.search.value) {
        elements.search.value = "";
        state.searchQuery = "";
        renderTree();
      }
    }
  });

  setTheme(initialTheme());
  const route = parseRoute();
  let storedPath = "";
  try {
    storedPath = window.localStorage.getItem("babcs-doc-path") || "";
  } catch (_) {
    void 0;
  }
  openPath(route.path || storedPath || "index.md", route.section || "", { updateHistory: false, instant: true });
}());
