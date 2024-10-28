// utils.js

const DEBUG = true;
function debugLog(...args) {
  if (DEBUG) {
    console.log(...args);
  }
}

function showToast(message, type = "info") {
  const toastContainer = document.querySelector(".toast-container");
  const toast = document.createElement("div");
  toast.className = `toast align-items-center text-white bg-${type} border-0`;
  toast.setAttribute("role", "alert");
  toast.setAttribute("aria-live", "assertive");
  toast.setAttribute("aria-atomic", "true");

  toast.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;

  toastContainer.appendChild(toast);
  const bsToast = new bootstrap.Toast(toast);
  bsToast.show();

  toast.addEventListener("hidden.bs.toast", () => {
    toastContainer.removeChild(toast);
  });
}

function displayClips(clips, outputFolder, resultContainer) {
  resultContainer.innerHTML = "";
  const summaryColumn = document.getElementById("summaryColumn");

  if (clips && clips.length > 0) {
    const clipContainer = document.createElement("div");
    clipContainer.className = "clip-container";

    clips.forEach((clip, index) => {
      const clipElement = document.createElement("div");
      clipElement.className = "clip";
      clipElement.innerHTML = `
          <h5>Clip ${clip.filename}</h5>
          <p>Start: ${clip.start ? clip.start.toFixed(2) : "N/A"}s | End: ${
        clip.end ? clip.end.toFixed(2) : "N/A"
      }s</p>
          <video width="20%" controls>
            <source src="/output/${outputFolder}/${clip.filename}" type="video/mp4">
          </video>
          <div class="content-section">
            <h6>Speech Recognition:</h6>
            <div class="text-content">${
        clip.speech_text || "No speech detected."
      }</div>
            <h6>Speech Translation:</h6>
            <div class="text-content translated-content">${
        clip.speech_translated || "No speech translation available."
      }</div>
          </div>
          <div class="content-section">
            <h6>OCR Text:</h6>
            <div class="text-content">${
        clip.ocr_text || "No text detected in video."
      }</div>
            <h6>OCR Translation:</h6>
            <div class="text-content translated-content">${
        clip.ocr_translated || "No OCR translation available."
      }</div>
          </div>
          <div class="content-section">
            <h6>Image Recognition Results:</h6>
            <p>${displayImageRecognitionResults(clip.image_recognition)}</p>
          </div>
        `;
      clipContainer.appendChild(clipElement);
    });

    resultContainer.appendChild(clipContainer);
  } else {
    resultContainer.innerHTML =
      "<p>No clips were generated. The video might be too short or there was an error during processing.</p>";
  }
}

function displayFakeVideoAnalysis(fakeDetectionResult) {
  const badgeClass = fakeDetectionResult.potential_manipulation
    ? "alert"
    : "pass";
  const badgeText = fakeDetectionResult.potential_manipulation
    ? "Potential Manipulation Detected"
    : "No Manipulation Detected";

  let analysisHtml = `
      <div class="fake-video-badge ${badgeClass}">
        ${badgeText}
      </div>
      <div class="fake-video-info">
        <h5>Detailed Video Analysis Report</h5>
        <p>Our system performed a comprehensive analysis to check for potential video manipulation:</p>
        <ul>
          <li><strong>Frame Rate Analysis:</strong> ${
    getAnalysisDetail(
      fakeDetectionResult,
      "frame_rate",
    )
  }</li>
          <li><strong>Video Quality Consistency:</strong> ${
    getAnalysisDetail(
      fakeDetectionResult,
      "quality",
    )
  }</li>
          <li><strong>Facial Proportion Changes:</strong> ${
    getAnalysisDetail(
      fakeDetectionResult,
      "facial_proportions",
    )
  }</li>
          <li><strong>Color Distribution Analysis:</strong> ${
    getAnalysisDetail(
      fakeDetectionResult,
      "color_distribution",
    )
  }</li>
        </ul>
    `;

  if (fakeDetectionResult.potential_manipulation) {
    analysisHtml += `
        <p><strong>Potential issues detected:</strong></p>
        <ul>
          ${
      fakeDetectionResult.reasons
        .map((reason) => `<li>${reason}</li>`)
        .join("")
    }
        </ul>
        <p>These findings suggest that the video may have been altered. However, please note that some legitimate editing techniques or unique filming conditions can occasionally trigger these alerts.</p>
      `;
  } else {
    analysisHtml += `
        <p><strong>Analysis Conclusion:</strong> Our comprehensive checks did not detect any clear signs of manipulation in this video. The content appears to be consistent with typical unaltered footage.</p>
      `;
  }

  analysisHtml += `
      <p><strong>Note:</strong> While our analysis is thorough, it's not infallible. Always consider the context of the video and use critical thinking when evaluating its authenticity. If you have concerns about the content, we recommend seeking additional verification from trusted sources.</p>
    </div>
    `;

  return analysisHtml;
}

function drawOverlays(canvas, currentTime, data) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw YOLO detections
  if (data.image_recognition?.detections) {
    const relevantDetections = data.image_recognition.detections.filter(
      (d) => Math.abs(d.timestamp - currentTime) < 0.5,
    );

    relevantDetections.forEach((det) => {
      const [x1, y1, x2, y2] = det.bbox;
      const width = x2 - x1;
      const height = y2 - y1;

      ctx.strokeStyle = "#00ff00";
      ctx.lineWidth = 2;
      ctx.strokeRect(x1, y1, width, height);

      const label = `${det.class} ${Math.round(det.confidence * 100)}%`;
      ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
      ctx.fillRect(x1, y1 - 20, ctx.measureText(label).width + 10, 20);
      ctx.fillStyle = "#fff";
      ctx.font = "14px Arial";
      ctx.fillText(label, x1 + 5, y1 - 5);
    });
  }

  // Draw OCR and Speech overlays
  drawTextOverlays(ctx, currentTime, data);
}

function drawTextOverlays(ctx, currentTime, data) {
  const padding = 10;
  ctx.font = "16px Arial";

  // Draw OCR at top
  if (data.ocr_text) {
    const y = 30;
    drawTextWithBackground(ctx, data.ocr_text, padding, y, "#00ff00");
    if (data.ocr_translated) {
      drawTextWithBackground(
        ctx,
        data.ocr_translated,
        padding,
        y + 25,
        "#aaffaa",
      );
    }
  }

  // Draw Speech at bottom
  if (data.speech_text) {
    const y = canvas.height - 60;
    drawTextWithBackground(ctx, data.speech_text, padding, y, "#ffffff");
    if (data.speech_translated) {
      drawTextWithBackground(
        ctx,
        data.speech_translated,
        padding,
        y + 25,
        "#aaccff",
      );
    }
  }
}

function drawTextWithBackground(ctx, text, x, y, color) {
  const metrics = ctx.measureText(text);
  const padding = 5;

  ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
  ctx.fillRect(x - padding, y - 16, metrics.width + (padding * 2), 24);

  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}

function setupVideoViewer(video, canvas, data) {
  video.addEventListener("timeupdate", () => {
    drawOverlays(canvas, video.currentTime, data);
  });
}

function getAnalysisDetail(result, check) {
  const details = {
    frame_rate:
      "We examined the consistency of frame rates throughout the video.",
    quality: "We looked for unexpected changes in video quality or resolution.",
    facial_proportions:
      "We analyzed facial features for unnatural changes or distortions.",
    color_distribution:
      "We checked for unusual shifts in color patterns or lighting.",
  };

  let status = result[check] ? "✓ Passed" : "⚠ Flagged";
  return `${status} - ${details[check]}`;
}

function displaySummary(summary) {
  if (!summary || summary.error) {
    return `<p>${summary ? summary.error : "No summary available"}</p>`;
  }

  let summaryHtml = "";

  if (summary.entities && summary.entities.length > 0) {
    summaryHtml += `<p><strong>Key Entities:</strong> ${
      summary.entities.join(
        ", ",
      )
    }</p>`;
  }

  if (summary.key_phrases && summary.key_phrases.length > 0) {
    summaryHtml += `<p><strong>Key Phrases:</strong> ${
      summary.key_phrases.join(
        ", ",
      )
    }</p>`;
  }

  if (
    summary.important_sentences &&
    summary.important_sentences.length > 0
  ) {
    summaryHtml +=
      `<div class="important-sentences"><h6>Important Sentences:</h6><ul>`;
    summary.important_sentences.forEach((sentence) => {
      summaryHtml += `<li>${sentence}</li>`;
    });
    summaryHtml += `</ul></div>`;
  }

  return (
    summaryHtml || "<p>No meaningful content found in the summary.</p>"
  );
}

function handleStreamedData(data, resultContainer) {
  switch (data.status) {
    case "started":
      console.log(data.message);
      break;
    case "processing":
      updateProgressBar(data.message);
      break;
    case "clip_ready":
      displayClip(
        data.data.clip,
        data.data.output_folder,
        resultContainer,
      );
      updateRunningSummary(data.data.running_summary);
      break;
    case "complete":
      console.log(data.message);
      displayFakeVideoAnalysis(data.fake_detection_result);
      hideProgressBar();
      break;
    case "error":
      console.error(data.message);
      showErrorMessage(data.message);
      hideProgressBar();
      break;
    default:
      console.log("Unknown message type:", data);
  }
}

function showErrorMessage(message) {
  // Display error message to the user
  const errorDiv = document.getElementById("error");
  errorDiv.textContent = message;
  errorDiv.style.display = "block";
}

function addPlaceholder(resultContainer) {
  const placeholder = document.createElement("div");
  placeholder.className = "clip-placeholder";
  placeholder.innerHTML = '<p class="placeholder-text">Processing clip...</p>';
  resultContainer.appendChild(placeholder);
  resultContainer.scrollTop = resultContainer.scrollHeight;
}

function replacePlaceholderWithClip(clip, outputFolder, resultContainer) {
  const placeholder = resultContainer.querySelector(".clip-placeholder");
  if (placeholder) {
    const clipElement = createClipElement(clip, outputFolder);
    resultContainer.replaceChild(clipElement, placeholder);
  } else {
    // If no placeholder is available, just append the new clip
    const clipElement = createClipElement(clip, outputFolder);
    resultContainer.appendChild(clipElement);
  }
  resultContainer.scrollTop = resultContainer.scrollHeight;
}

function updateProjectTitle(summary) {
  const titleElement = document.querySelector(".project-title h2");
  if (summary && summary.key_topics && summary.key_topics.length > 0) {
    const topTopics = summary.key_topics.slice(0, 3).join(", ");
    titleElement.textContent = `Analyzing: ${topTopics}`;
  } else {
    titleElement.textContent =
      "Multi-Modal Video Analysis and Summarization Platform";
  }
}

function displayRunningSummary(summary = {}) {
  if (!summary) {
    return '<div class="alert alert-info">No summary available yet</div>';
  }

  return `
      <div class="running-summary">
          <h4>Running Summary</h4>
          <div class="summary-section">
              <h5>Key Topics:</h5>
              <ul class="summary-list">
                  ${
    (summary.key_phrases || []) // Changed from key_topics to key_phrases
      .map((topic) => `<li>${topic}</li>`)
      .join("")
  }
              </ul>
          </div>
          <div class="summary-section">
              <h5>Main Entities:</h5>
              <ul class="summary-list">
                  ${
    (summary.entities || [])
      .map((entity) => `<li>${entity}</li>`)
      .join("")
  }
              </ul>
          </div>
          <div class="summary-section">
              <h5>Recognized Objects:</h5>
              <ul class="summary-list">
                  ${
    (summary.recognized_objects || [])
      .map((object) => `<li>${object}</li>`)
      .join("")
  }
              </ul>
          </div>
          <div class="important-sentences">
              <h5>Important Sentences:</h5>
              <ul>
                  ${
    (summary.important_sentences || [])
      .map((sentence) => `<li>"${sentence}"</li>`)
      .join("")
  }
              </ul>
              <p class="important-sentences-note">Note: Sentences have been filtered for relevance and coherence.</p>
          </div>
      </div>
  `;
}

function createClipElement(clip, outputFolder) {
  console.log("Creating clip element with data:", clip);
  const clipElement = document.createElement("div");
  clipElement.className = "clip";

  // Generate unique IDs for this clip's video and canvas
  const videoId = `video-${Math.random().toString(36).substr(2, 9)}`;
  const canvasId = `canvas-${Math.random().toString(36).substr(2, 9)}`;

  clipElement.innerHTML = `
      <h5><b>${clip.clip_name}</b></h5>
      <div class="video-container position-relative">
          <video id="${videoId}" width="100%" controls>
              <source src="/output/${outputFolder}/${clip.filename}" type="video/mp4">
          </video>
          <canvas id="${canvasId}" class="detection-overlay"></canvas>
      </div>
      <div class="detection-stats mt-3">
          <h6>Detected Objects:</h6>
          <ul class="list-unstyled">
              ${
    (clip.image_recognition.detections || [])
      .map((det) => `
                      <li class="mb-1">
                          <span class="badge bg-primary">${det.class}</span>
                          <small class="text-muted">
                              ${(det.confidence * 100).toFixed(1)}% at ${
        det.timestamp.toFixed(1)
      }s
                          </small>
                      </li>
                  `).join("")
  }
          </ul>
          
          <h6 class="mt-3">Scene Classifications:</h6>
          <ul class="list-unstyled">
              ${
    (clip.image_recognition.classifications || [])
      .map((cls) => `
                      <li class="mb-1">
                          <span class="badge bg-secondary">${cls.label}</span>
                          <small class="text-muted">
                              ${(cls.confidence * 100).toFixed(1)}%
                          </small>
                      </li>
                  `).join("")
  }
          </ul>
      </div>
      <div class="mt-3">
          <h6>Speech Recognition:</h6>
          <div class="text-content">${
    clip.speech_text || "No speech detected."
  }</div>
          <h6>Speech Translation:</h6>
          <div class="text-content translated-content">${
    clip.speech_translated || "No speech translation available."
  }</div>
      </div>
      <div class="mt-3">
          <h6>OCR Text:</h6>
          <div class="text-content">${
    clip.ocr_text || "No text detected in video."
  }</div>
          <h6>OCR Translation:</h6>
          <div class="text-content translated-content">${
    clip.ocr_translated || "No OCR translation available."
  }</div>
      </div>
      <div class="mt-3">${displaySummary(clip.summary)}</div>
  `;

  // Set up detection overlay after the element is added to the DOM
  setTimeout(() => {
    const video = document.getElementById(videoId);
    const canvas = document.getElementById(canvasId);

    if (video && canvas) {
      setupDetectionOverlay(
        video,
        canvas,
        clip.image_recognition.detections || [],
      );
    }
  }, 0);

  return clipElement;
}

function setupDetectionOverlay(video, canvas, detections) {
  // Set up canvas positioning
  canvas.style.position = "absolute";
  canvas.style.top = "0";
  canvas.style.left = "0";
  canvas.style.pointerEvents = "none";

  // Initialize canvas when video metadata is loaded
  video.addEventListener("loadedmetadata", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  });

  // Update detections while video plays
  video.addEventListener("timeupdate", () => {
    const currentTime = video.currentTime;
    drawDetections(canvas, currentTime, detections);
  });
}

function drawDetections(canvas, currentTime, detections) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Find detections within 0.5 seconds of current time
  const relevantDetections = detections.filter(
    (d) => Math.abs(d.timestamp - currentTime) < 0.5,
  );

  relevantDetections.forEach((detection) => {
    const [x1, y1, x2, y2] = detection.bbox;
    const width = x2 - x1;
    const height = y2 - y1;

    // Draw box
    ctx.strokeStyle = "#00ff00";
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, width, height);

    // Draw label background
    const label = `${detection.class} ${
      Math.round(detection.confidence * 100)
    }%`;
    ctx.font = "14px Arial";
    const textMetrics = ctx.measureText(label);
    const textHeight = 20;
    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(
      x1,
      y1 > textHeight ? y1 - textHeight : y1,
      textMetrics.width + 10,
      textHeight,
    );

    // Draw label text
    ctx.fillStyle = "#ffffff";
    ctx.fillText(
      label,
      x1 + 5,
      y1 > textHeight ? y1 - 5 : y1 + 15,
    );
  });
}

// Add CSS for the detection overlay
document.head.insertAdjacentHTML(
  "beforeend",
  `
  <style>
      .video-wrapper {
          position: relative;
          width: 100%;
          background: #000;
          margin-bottom: 1rem;
      }

      .detection-overlay {
          position: absolute;
          top: 0;
          left: 0;
          pointer-events: none;
          z-index: 1;
      }

      .ocr-text {
          text-shadow: 2px 2px 2px rgba(0,0,0,0.8);
          font-family: Arial, sans-serif;
      }

      .ocr-translated {
          font-style: italic;
          opacity: 0.9;
      }
  </style>
`,
);

function displayImageRecognitionResults(results) {
  if (!results || results.length === 0) {
    return "No objects recognized in the video.";
  }

  const topResults = results.slice(0, 5); // Display top 5 recognized objects
  return topResults
    .map(
      (result) => `${result.label} (${(result.confidence * 100).toFixed(2)}%)`,
    )
    .join(", ");
}

function removePlaceholders(resultContainer) {
  const placeholders = resultContainer.querySelectorAll(".clip-placeholder");
  placeholders.forEach((placeholder) => placeholder.remove());
}

function updateSavedResultsList() {
  fetch("/list_saved_results")
    .then((response) => response.json())
    .then((results) => {
      savedResultsList.innerHTML = "";
      results.forEach((result) => {
        const resultElement = document.createElement("div");
        resultElement.className = "saved-result-item";
        resultElement.innerHTML = `
            <span>${result}</span>
            <span class="delete-btn" onclick="deleteResult('${result}', event)">🗑️</span>
          `;
        resultElement.addEventListener("click", () => loadResult(result));
        savedResultsList.appendChild(resultElement);
      });
    })
    .catch((error) => {
      console.error("Error fetching saved results:", error);
      showToast("Error fetching saved results", "danger");
    });
}

function displayClip(clip, outputFolder, resultContainer) {
  console.log("Displaying clip:", clip);
  const viewer = createVideoViewer(clip, outputFolder);
  resultContainer.appendChild(viewer);
  resultContainer.scrollTop = resultContainer.scrollHeight;
}

function renderDetections(imageRecognition) {
  if (!imageRecognition?.detections?.length) {
    return "<p>No detections found</p>";
  }

  return imageRecognition.detections
    .map((det) => `
          <div class="detection-item">
              <span class="badge bg-primary">${det.class}</span>
              <small>${(det.confidence * 100).toFixed(1)}%</small>
              <small class="text-muted">at ${det.timestamp?.toFixed(1)}s</small>
          </div>
      `)
    .join("");
}
function setupVideoViewer(video, canvas, data) {
  video.addEventListener("timeupdate", () => {
    drawOverlays(canvas, video.currentTime, data);
  });
}
// Add this helper function to safely access nested properties
function safeGet(obj, path, defaultValue = null) {
  try {
    return path.split(".").reduce((o, k) => o[k], obj) ?? defaultValue;
  } catch (e) {
    console.warn(`Error accessing path ${path}:`, e);
    return defaultValue;
  }
}

function processOCRResults(ocrText, translatedText) {
  // This is a placeholder - you'll need to modify based on your actual OCR output format
  return ocrText.split("\n").map((text, index) => {
    const translated = translatedText.split("\n")[index];
    return {
      text: text,
      translated: translated,
      // You'll need to get actual bounding boxes from your OCR output
      bbox: [100, 100 + (index * 50), 300, 30],
      confidence: 0.9,
    };
  }).filter((result) => result.text.trim() !== "");
}

function createVideoViewer(clip, outputFolder) {
  console.log("Creating viewer for clip:", clip);
  const container = document.createElement("div");
  container.className = "video-detection-container mb-4";

  // Create elements first
  const video = document.createElement("video");
  video.className = "w-100";
  video.controls = true;

  const canvas = document.createElement("canvas");
  canvas.className = "detection-overlay";

  // Create HTML structure
  container.innerHTML = `
      <div class="card">
          <div class="card-header">
              <h5 class="mb-0">${clip.clip_name || "Unnamed Clip"}</h5>
          </div>
          <div class="card-body">
              <div class="video-wrapper position-relative">
                  <div id="video-container"></div>
              </div>
              
              <div class="mt-3">
                  <div class="row">
                      <div class="col-md-4">
                          <h6>Detections:</h6>
                          <div class="detection-list">
                              ${renderDetections(clip.image_recognition)}
                          </div>
                      </div>
                      
                      <div class="col-md-4">
                          <h6>OCR Text:</h6>
                          <div class="text-content">${
    clip.ocr_text || "No text detected."
  }</div>
                          <div class="text-content text-muted mt-2">
                              ${
    clip.ocr_translated || "No translation available."
  }
                          </div>
                      </div>

                      <div class="col-md-4">
                          <h6>Speech Recognition:</h6>
                          <div class="text-content">${
    clip.speech_text || "No speech detected."
  }</div>
                          <div class="text-content text-muted mt-2">
                              ${
    clip.speech_translated || "No translation available."
  }
                          </div>
                      </div>
                  </div>
              </div>
          </div>
      </div>
  `;

  // Insert video and canvas
  const videoWrapper = container.querySelector(".video-wrapper");
  video.innerHTML =
    `<source src="/output/${outputFolder}/${clip.filename}" type="video/mp4">`;
  videoWrapper.appendChild(video);
  videoWrapper.appendChild(canvas);

  // Set up overlays
  const overlayData = {
    image_recognition: clip.image_recognition,
    ocr_text: clip.ocr_text,
    ocr_translated: clip.ocr_translated,
    speech_text: clip.speech_text,
    speech_translated: clip.speech_translated,
  };

  // Initialize video and canvas
  video.addEventListener("loadedmetadata", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    setupVideoViewer(video, canvas, overlayData);
  });

  return container;
}

function getColorForConfidence(confidence) {
  const hue = confidence * 120; // 0 = red, 120 = green
  return `hsl(${hue}, 70%, 45%)`;
}

function setupDetectionOverlay(video, canvas, detections) {
  canvas.style.position = "absolute";
  canvas.style.top = "0";
  canvas.style.left = "0";
  canvas.style.pointerEvents = "none";

  video.addEventListener("loadedmetadata", () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
  });

  video.addEventListener("timeupdate", () => {
    const currentTime = video.currentTime;
    drawDetections(canvas, currentTime, detections);

    // Highlight current detections in the list
    const detectionItems = document.querySelectorAll(".detection-item");
    detectionItems.forEach((item) => {
      const timestamp = parseFloat(item.dataset.timestamp);
      if (Math.abs(currentTime - timestamp) < 0.5) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });
  });
}

function drawDetections(canvas, currentTime, detections) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Find detections within 0.5 seconds of current time
  const relevantDetections = detections.filter(
    (d) => Math.abs(d.timestamp - currentTime) < 0.5,
  );

  relevantDetections.forEach((detection) => {
    const [x1, y1, x2, y2] = detection.bbox;
    const width = x2 - x1;
    const height = y2 - y1;

    // Draw box
    ctx.strokeStyle = getColorForConfidence(detection.confidence);
    ctx.lineWidth = 2;
    ctx.strokeRect(x1, y1, width, height);

    // Draw label background
    const label = `${detection.class} ${
      Math.round(detection.confidence * 100)
    }%`;
    ctx.font = "14px Arial";
    const textMetrics = ctx.measureText(label);
    const textHeight = 20;
    ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
    ctx.fillRect(
      x1,
      y1 > textHeight ? y1 - textHeight : y1,
      textMetrics.width + 10,
      textHeight,
    );

    // Draw label text
    ctx.fillStyle = "#ffffff";
    ctx.fillText(
      label,
      x1 + 5,
      y1 > textHeight ? y1 - 5 : y1 + 15,
    );
  });
}

// Add the required styles to the document
document.head.insertAdjacentHTML(
  "beforeend",
  `
  <style>
      .video-detection-container {
          max-width: 1200px;
          margin: 0 auto;
      }
      
      .video-wrapper {
          position: relative;
          width: 100%;
          background: #000;
      }
      
      .detection-overlay {
          position: absolute;
          top: 0;
          left: 0;
          pointer-events: none;
      }
      
      .detection-item {
          padding: 8px;
          margin-bottom: 4px;
          background: #f8f9fa;
          border-radius: 4px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          transition: all 0.3s;
      }
      
      .detection-item.active {
          background: #e9ecef;
          transform: scale(1.02);
      }
      
      .classification-item {
          margin-bottom: 12px;
      }
      
      .classification-label {
          display: block;
          margin-bottom: 4px;
      }
      
      .detection-time {
          color: #6c757d;
          font-size: 0.875em;
      }
  </style>
`,
);
