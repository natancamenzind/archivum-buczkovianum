// Uploads the chosen scan from the browser straight to S3, with its progress, and puts the
// stored scan's name in the form's `scan_key` in place of the file (ARC-64). The scan then
// crosses the editor's connection once and the form saves in seconds.

function csrfToken(form) {
  const input = form.querySelector("input[name=csrfmiddlewaretoken]");
  return input ? input.value : "";
}

async function signUpload(input, file) {
  const body = new FormData();
  body.append("filename", file.name);
  const response = await fetch(input.dataset.directUpload, {
    method: "POST",
    credentials: "same-origin",
    headers: { "X-CSRFToken": csrfToken(input.form) },
    body,
  });
  if (!response.ok) {
    throw new Error(`Signing the upload failed: ${response.status}`);
  }
  return response.json();
}

function postToStorage(upload, file, progress) {
  const body = new FormData();
  Object.entries(upload.fields).forEach(([name, value]) => body.append(name, value));
  // S3 reads the file last: fields after it are ignored.
  body.append("file", file);
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("POST", upload.url);
    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        progress.value = event.loaded / event.total;
      }
    });
    request.addEventListener("load", () => {
      if (request.status >= 200 && request.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed: ${request.status}`));
      }
    });
    request.addEventListener("error", () => reject(new Error("Upload failed")));
    request.send(body);
  });
}

function setSubmitting(form, enabled) {
  form.querySelectorAll("[type=submit]").forEach((button) => {
    button.disabled = !enabled;
  });
}

function setUpDirectUpload(input) {
  const keyInput = input.form.elements.namedItem("scan_key");
  const status = document.createElement("p");
  status.className = "help";
  status.setAttribute("role", "status");
  const progress = document.createElement("progress");
  progress.hidden = true;
  input.after(status, progress);
  if (keyInput.value) {
    status.textContent = input.dataset.uploaded;
  }

  input.addEventListener("change", async () => {
    const file = input.files[0];
    keyInput.value = "";
    if (!file) {
      status.textContent = "";
      return;
    }
    status.textContent = input.dataset.uploading;
    progress.value = 0;
    progress.hidden = false;
    setSubmitting(input.form, false);
    try {
      const upload = await signUpload(input, file);
      await postToStorage(upload, file, progress);
      keyInput.value = upload.name;
      // The form posts the stored scan's name, not the file again.
      input.value = "";
      status.textContent = `${input.dataset.uploaded} (${file.name})`;
    } catch (error) {
      input.value = "";
      status.textContent = input.dataset.failed;
      console.error(error);
    } finally {
      progress.hidden = true;
      setSubmitting(input.form, true);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input[type=file][data-direct-upload]").forEach(setUpDirectUpload);
});
