// The document offset of a range boundary. Each page's text carries its first offset, so page
// numbers and the markup between pages never count. A boundary outside the pages' text, as on a
// page number, falls on the start of the next page's text, or on the end of the last one.
function documentOffset(container, node, offset) {
  const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
  const pageText = element.closest(".tagger-page-text");
  if (pageText) {
    const before = document.createRange();
    before.selectNodeContents(pageText);
    before.setEnd(node, offset);
    return Number(pageText.dataset.start) + before.toString().length;
  }
  const boundary = document.createRange();
  boundary.setStart(node, offset);
  const pageTexts = Array.from(container.querySelectorAll(".tagger-page-text"));
  const next = pageTexts.find((candidate) => boundary.comparePoint(candidate, 0) >= 0);
  if (next) {
    return Number(next.dataset.start);
  }
  const last = pageTexts[pageTexts.length - 1];
  return Number(last.dataset.start) + last.textContent.length;
}

function selectionOffsets(container) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    return null;
  }
  const range = selection.getRangeAt(0);
  if (!container.contains(range.startContainer) || !container.contains(range.endContainer)) {
    return null;
  }
  const start = documentOffset(container, range.startContainer, range.startOffset);
  const end = documentOffset(container, range.endContainer, range.endOffset);
  // A selection across pages also holds page numbers and the markup between pages: keep only
  // the pages' text, which the API checks against the stored text.
  const contents = range.cloneContents();
  const pageTexts = contents.querySelectorAll(".tagger-page-text");
  const quote = pageTexts.length
    ? Array.from(pageTexts, (pageText) => pageText.textContent).join("")
    : contents.textContent;
  if (!quote || end <= start) {
    return null;
  }
  return { start, end, quote };
}

function csrfToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

async function apiRequest(url, options) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken(),
      ...(options.headers || {}),
    },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body.detail || JSON.stringify(body);
    throw new Error(message);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

function initTagger(root) {
  const documentId = root.dataset.documentId;
  const apiUrl = root.dataset.apiUrl;
  const textEl = root.querySelector("#tagger-text");
  const selectionOut = root.querySelector("#tagger-selection");
  const form = root.querySelector("#tagger-create");
  let pending = null;

  function showSelection() {
    pending = selectionOffsets(textEl);
    selectionOut.textContent = pending ? `"${pending.quote}" (${pending.start}–${pending.end})` : "—";
  }

  textEl.addEventListener("mouseup", showSelection);
  textEl.addEventListener("keyup", showSelection);

  const goToPage = root.querySelector("#tagger-go-to-page");
  if (goToPage) {
    goToPage.addEventListener("submit", (event) => {
      event.preventDefault();
      const number = goToPage.querySelector("#tagger-page-number").value;
      const page = root.querySelector(`#tagger-page-${number}`);
      if (page) {
        textEl.scrollTop = page.offsetTop;
      }
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!pending) {
      return;
    }
    const tagSelect = form.querySelector("#tagger-tags");
    const tagIds = Array.from(tagSelect.selectedOptions).map((option) => Number(option.value));
    if (tagIds.length === 0) {
      return;
    }
    await apiRequest(apiUrl, {
      method: "POST",
      body: JSON.stringify({
        document: Number(documentId),
        start: pending.start,
        end: pending.end,
        quote: pending.quote,
        tag_ids: tagIds,
      }),
    });
    location.reload();
  });

  root.querySelectorAll(".tagger-delete").forEach((button) => {
    button.addEventListener("click", async () => {
      await apiRequest(`${apiUrl}${button.dataset.fragmentId}/`, { method: "DELETE" });
      location.reload();
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const root = document.getElementById("tagger");
  if (root) {
    initTagger(root);
  }
});
