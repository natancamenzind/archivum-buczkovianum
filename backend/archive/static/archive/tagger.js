function selectionOffsets(container) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    return null;
  }
  const range = selection.getRangeAt(0);
  if (!container.contains(range.commonAncestorContainer)) {
    return null;
  }
  const before = document.createRange();
  before.selectNodeContents(container);
  before.setEnd(range.startContainer, range.startOffset);
  const start = before.toString().length;
  const quote = range.toString();
  if (!quote) {
    return null;
  }
  return { start, end: start + quote.length, quote };
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
