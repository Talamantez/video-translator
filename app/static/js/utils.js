// utils.js
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
          <h6>Speech Recognition:</h6>
          <div class="text-content">${
        clip.speech_text || "No speech detected."
      }</div>
          <h6>OCR Text:</h6>
          <div>${clip.ocr_text || "No text detected in video."}</div>
          <h6>Translation:</h6>
          <div>${clip.translated_text || "Translation not available."}</div>
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

function displayRunningSummary(summary) {
  updateProjectTitle(summary);
  return `
      <div class="running-summary">
        <h4>Running Summary</h4>
        <div class="summary-section">
          <h5>Key Topics:</h5>
          <ul class="summary-list">
            ${
    summary.key_topics
      .map((topic) => `<li>${topic}</li>`)
      .join("")
  }
          </ul>
        </div>
        <div class="summary-section">
          <h5>Main Entities:</h5>
          <ul class="summary-list">
            ${
    summary.main_entities
      .map((entity) => `<li>${entity}</li>`)
      .join("")
  }
          </ul>
        </div>
        <div class="summary-section">
          <h5>Recognized Objects:</h5>
          <ul class="summary-list">
            ${
    summary.recognized_objects
      .map((object) => `<li>${object}</li>`)
      .join("")
  }
          </ul>
        </div>
        <div class="important-sentences">
          <h5>Important Sentences:</h5>
          <ul>
            ${
    summary.important_sentences
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
  console.log("Creating clip element with summary:", clip.summary);
  const clipElement = document.createElement("div");
  clipElement.className = "clip";
  clipElement.innerHTML = `
      <h5><b>${clip.clip_name}</b></h5>
      <div class="video-container">
        <div class="video-info">
          <span>Source: ${clip.source_url || "Not available"}</span>
          <br>
          <span>Last accessed: ${clip.access_time || "Not available"}</span>
        </div>
        <video width="100%" controls>
          <source src="/output/${outputFolder}/${clip.filename}" type="video/mp4">
        </video>
      </div>
      <p>Start: ${clip.start ? clip.start.toFixed(2) : "N/A"}s | End: ${
    clip.end ? clip.end.toFixed(2) : "N/A"
  }s</p>
      <div>${displaySummary(clip.summary)}</div>
      <div class="image-recognition-results">
        <h6>Image Recognition Results:</h6>
        <p>${displayImageRecognitionResults(clip.image_recognition)}</p>
      </div>
        <h6>Translation:</h6>
        <div class="text-content">${
    clip.translated_text || "Translation not available."
  }</div>
        <h6>Speech Recognition:</h6>
        <div class="text-content">${
    clip.speech_text || "No speech detected."
  }</div>
        <h6>OCR Text:</h6>
        <div class="text-content">${
    clip.ocr_text || "No text detected in video."
  }</div>
    `;
  return clipElement;
}

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

function displayClip(clip, outputFolder, resultContainer) {
  const clipElement = createClipElement(clip, outputFolder);
  resultContainer.appendChild(clipElement);
  resultContainer.scrollTop = resultContainer.scrollHeight;
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
