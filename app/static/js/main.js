// main.js
document.addEventListener('DOMContentLoaded', function() {
    const videoUrl = document.getElementById("videoUrl");
    const clipDurationFile = document.getElementById("clipDurationFile");
    const clipDurationUrl = document.getElementById("clipDurationUrl");
    const videoFile = document.getElementById("videoFile");
    const processUrlBtn = document.getElementById("processUrlBtn");
    const urlResults = document.getElementById("urlResults");
    const sideMenuToggle = document.getElementById("sideMenuToggle");
    const sideMenu = document.getElementById("sideMenu");

    processFileBtn.addEventListener("click", () => {
        const file = videoFile.files[0];
        if (!file) {
            showToast("Please select a video file to upload", "warning");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("clipDuration", clipDurationFile.value);
        formData.append(
            "targetLanguage",
            document.getElementById("targetLanguage").value
        );

        processVideoFile(formData);
    });

    processUrlBtn.addEventListener("click", () => {
        if (!videoUrl.value) {
            showToast("Please enter a URL to process", "warning");
            return;
        }
        processVideo(
            "/process_url",
            {
                url: videoUrl.value,
                clipDuration: parseInt(clipDurationUrl.value),
                targetLanguage: document.getElementById("targetLanguage").value,
            },
            urlResults
        );
    });

    sideMenuToggle.addEventListener("click", () => {
        sideMenu.classList.toggle("open");
    });

    saveResultBtn.addEventListener("click", () => {
        const resultName = resultNameInput.value.trim();
        if (!resultName) {
            showToast("Please enter a name for the result", "warning");
            return;
        }

        const currentResult = {
            url: urlResults.innerHTML,
        };

        saveResult(resultName, currentResult);
    });

    // Call this function when the page loads to populate the saved results list
    updateSavedResultsList();
});