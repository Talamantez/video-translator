async function processVideo(endpoint, data, resultContainer) {
  errorDiv.textContent = "";
  const progressContainer = document.getElementById("progressContainer");
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");

  progressContainer.style.display = "block";
  progressBar.style.width = "0%";
  progressText.textContent = "Initiating video processing...";

  // Clear previous results
  resultContainer.innerHTML = "";

  // Create a container for clips
  const clipsContainer = document.createElement("div");
  clipsContainer.id = "clipsContainer";
  resultContainer.appendChild(clipsContainer);

  let runningSummaryElement = document.createElement("div");
  runningSummaryElement.id = "runningSummary";
  resultContainer.insertBefore(runningSummaryElement, resultContainer.firstChild);

  let fakeVideoAnalysisElement = document.createElement("div");
  fakeVideoAnalysisElement.id = "fakeVideoAnalysis";
  resultContainer.insertBefore(fakeVideoAnalysisElement, resultContainer.firstChild);

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let clipCount = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.trim()) {
          try {
            const message = JSON.parse(line);
            switch (message.status) {
              case "started":
                progressText.textContent = message.message;
                break;
              case "downloading":
              case "processing":
                progressText.textContent = message.message;
                // Update progress bar
                const progress =
                  (progressBar.style.width.replace("%", "") || 0) * 1 + 5;
                progressBar.style.width = `${Math.min(progress, 95)}%`;
                break;
              case "clip_ready":
                clipCount++;
                displayClip(
                  message.data.clip,
                  message.data.output_folder,
                  clipsContainer,
                );
                // Update running summary and project title
                runningSummaryElement.innerHTML = displayRunningSummary(
                  message.data.running_summary,
                );
                progressText.textContent = `Processed ${clipCount} clip(s)`;
                break;
              case "complete":
                progressBar.style.width = "100%";
                progressText.textContent = message.message;
                // Display final fake video analysis result
                if (message.fake_detection_result) {
                  fakeVideoAnalysisElement.innerHTML = displayFakeVideoAnalysis(
                    message.fake_detection_result,
                  );
                }
                showToast("Processing complete!", "success");
                setTimeout(() => {
                  progressContainer.style.display = "none";
                }, 2000);
                break;
              default:
                console.log("Unknown message type:", message);
            }
          } catch (error) {
            console.error(
              "Error parsing JSON:",
              error,
              "Raw data:",
              line,
            );
          }
        }
      }
    }
  } catch (error) {
    console.error("Error:", error);
    showToast(`Error: ${error.message}`, "danger");
    errorDiv.textContent = `Error: ${error.message}`;
    progressContainer.style.display = "none";
  }
}

async function processVideoFile(formData) {
  errorDiv.textContent = "";
  const progressContainer = document.getElementById("progressContainer");
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");

  progressContainer.style.display = "block";
  progressBar.style.width = "0%";
  progressText.textContent = "Uploading video...";

  // Clear previous results
  urlResults.innerHTML = "";

  let runningSummaryElement = document.createElement("div");
  runningSummaryElement.id = "runningSummary";
  urlResults.insertBefore(runningSummaryElement, urlResults.firstChild);

  let fakeVideoAnalysisElement = document.createElement("div");
  fakeVideoAnalysisElement.id = "fakeVideoAnalysis";
  urlResults.insertBefore(
    fakeVideoAnalysisElement,
    urlResults.firstChild,
  );

  try {
    const uploadResponse = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    if (!uploadResponse.ok) {
      throw new Error(`HTTP error! status: ${uploadResponse.status}`);
    }

    const uploadResult = await uploadResponse.json();
    progressText.textContent = "Video uploaded successfully. Processing...";

    // Now process the uploaded video
    const processResponse = await fetch("/process", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        filename: uploadResult.filename,
        clipDuration: parseInt(clipDurationFile.value),
        targetLanguage: document.getElementById("targetLanguage").value,
      }),
    });

    if (!processResponse.ok) {
      throw new Error(`HTTP error! status: ${processResponse.status}`);
    }

    const reader = processResponse.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let clipCount = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (line.trim()) {
          try {
            const message = JSON.parse(line);
            switch (message.status) {
              case "processing":
                progressText.textContent = message.message;
                // Update progress bar
                const progress =
                  (progressBar.style.width.replace("%", "") || 0) * 1 + 5;
                progressBar.style.width = `${Math.min(progress, 95)}%`;
                break;
              case "clip_ready":
                clipCount++;
                displayClip(
                  message.data.clip,
                  message.data.output_folder,
                  urlResults,
                );
                // Update running summary
                runningSummaryElement.innerHTML = displayRunningSummary(
                  message.data.running_summary,
                );
                progressText.textContent = `Processed ${clipCount} clip(s)`;
                break;
              case "complete":
                progressBar.style.width = "100%";
                progressText.textContent = message.message;
                // Display final fake video analysis result
                if (message.fake_detection_result) {
                  fakeVideoAnalysisElement.innerHTML = displayFakeVideoAnalysis(
                    message.fake_detection_result,
                  );
                }
                showToast("Processing complete!", "success");
                setTimeout(() => {
                  progressContainer.style.display = "none";
                }, 2000);
                break;
              default:
                console.log("Unknown message type:", message);
            }
          } catch (error) {
            console.error(
              "Error parsing JSON:",
              error,
              "Raw data:",
              line,
            );
          }
        }
      }
    }
  } catch (error) {
    console.error("Error:", error);
    showToast(`Error: ${error.message}`, "danger");
    errorDiv.textContent = `Error: ${error.message}`;
    progressContainer.style.display = "none";
  }
}

function saveResult(resultName, currentResult) {
  fetch("/save_result", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: resultName, data: currentResult }),
  })
    .then((response) => response.json())
    .then((data) => {
      showToast(data.message, "success");
      updateSavedResultsList();
    })
    .catch((error) => {
      console.error("Error saving result:", error);
      showToast("Error saving result", "danger");
    });
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

function deleteResult(resultName, event) {
  event.stopPropagation(); // Prevent triggering the loadResult function
  if (
    confirm(`Are you sure you want to delete the result "${resultName}"?`)
  ) {
    fetch(`/delete_result/${resultName}`, {
      method: "DELETE",
    })
      .then((response) => response.json())
      .then((data) => {
        showToast(data.message, "success");
        updateSavedResultsList();
      })
      .catch((error) => {
        console.error("Error deleting result:", error);
        showToast("Error deleting result", "danger");
      });
  }
}

function loadResult(resultName) {
  fetch(`/load_result/${resultName}`)
    .then((response) => response.json())
    .then((data) => {
      urlResults.innerHTML = data.url || "";
      showToast("Result loaded successfully", "success");
    })
    .catch((error) => {
      console.error("Error loading result:", error);
      showToast("Error loading result", "danger");
    });
}
