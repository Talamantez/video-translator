// video-overlay.js
(function() {
    // Define VideoDetectionOverlay class
    class VideoDetectionOverlay {
        constructor(videoElement, canvasElement) {
            if (!videoElement || !canvasElement) {
                throw new Error("Both video and canvas elements are required");
            }

            this.video = videoElement;
            this.canvas = canvasElement;
            this.ctx = this.canvas.getContext("2d");

            // Bind methods
            this.updateCanvasSize = this.updateCanvasSize.bind(this);
            this.drawDetections = this.drawDetections.bind(this);

            // Initialize canvas sizing
            this.updateCanvasSize();

            // Set up resize observer
            this.resizeObserver = new ResizeObserver(this.updateCanvasSize);
            this.resizeObserver.observe(this.video);

            // Event listeners
            this.video.addEventListener("loadedmetadata", this.updateCanvasSize);
            window.addEventListener("resize", this.updateCanvasSize);
        }

        updateCanvasSize() {
            try {
                const videoRect = this.video.getBoundingClientRect();
                this.canvas.width = videoRect.width;
                this.canvas.height = videoRect.height;
                this.scaleX = this.canvas.width / (this.video.videoWidth || this.canvas.width);
                this.scaleY = this.canvas.height / (this.video.videoHeight || this.canvas.height);
            } catch (error) {
                console.error("Error updating canvas size:", error);
            }
        }

        drawDetections(detections, currentTime) {
            try {
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

                if (!Array.isArray(detections)) {
                    console.warn("Detections is not an array:", detections);
                    return;
                }

                const relevantDetections = detections.filter(
                    d => d && typeof d.timestamp === "number" && Math.abs(d.timestamp - currentTime) < 0.5
                );

                relevantDetections.forEach(detection => {
                    if (!detection.bbox || detection.bbox.length !== 4) {
                        console.warn("Invalid bbox:", detection.bbox);
                        return;
                    }

                    const [x1, y1, x2, y2] = detection.bbox;
                    const scaledX = x1 * this.scaleX;
                    const scaledY = y1 * this.scaleY;
                    const scaledWidth = (x2 - x1) * this.scaleX;
                    const scaledHeight = (y2 - y1) * this.scaleY;

                    // Draw box
                    this.ctx.strokeStyle = `rgba(0, 255, 0, ${detection.confidence || 1})`;
                    this.ctx.lineWidth = 2;
                    this.ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

                    // Draw label
                    const label = `${detection.class || "Unknown"} (${Math.round((detection.confidence || 0) * 100)}%)`;
                    this.ctx.font = "14px Arial";
                    const textMetrics = this.ctx.measureText(label);
                    const padding = 4;
                    const labelHeight = 20;

                    this.ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
                    this.ctx.fillRect(
                        scaledX,
                        scaledY > labelHeight ? scaledY - labelHeight : scaledY,
                        textMetrics.width + padding * 2,
                        labelHeight
                    );

                    this.ctx.fillStyle = "#ffffff";
                    this.ctx.fillText(
                        label,
                        scaledX + padding,
                        scaledY > labelHeight ? scaledY - 6 : scaledY + 14
                    );
                });
            } catch (error) {
                console.error("Error drawing detections:", error);
            }
        }

        destroy() {
            try {
                this.resizeObserver.disconnect();
                window.removeEventListener("resize", this.updateCanvasSize);
                this.video.removeEventListener("loadedmetadata", this.updateCanvasSize);
            } catch (error) {
                console.error("Error destroying overlay:", error);
            }
        }
    }

    // Create viewer function
    function createVideoViewer(clip, outputFolder) {
        const container = document.createElement('div');
        container.className = 'video-detection-container position-relative mb-4';
        
        const video = document.createElement('video');
        video.className = 'w-100';
        video.controls = true;
        video.innerHTML = `<source src="/output/${outputFolder}/${clip.filename}" type="video/mp4">`;
        
        const canvas = document.createElement('canvas');
        canvas.className = 'detection-overlay position-absolute top-0 start-0';
        canvas.style.pointerEvents = 'none';
        
        container.appendChild(video);
        container.appendChild(canvas);

        video.addEventListener('loadedmetadata', () => {
            const overlay = new VideoDetectionOverlay(video, canvas);
            video.addEventListener('timeupdate', () => {
                const detections = clip.image_recognition?.detections || [];
                overlay.drawDetections(detections, video.currentTime);
            });
        });

        return container;
    }

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .video-detection-container {
            position: relative;
            width: 100%;
            background: #000;
        }

        .detection-overlay {
            position: absolute;
            top: 0;
            left: 0;
            pointer-events: none;
            width: 100%;
            height: 100%;
        }
    `;
    document.head.appendChild(style);

    // Expose to global scope
    window.VideoDetectionOverlay = VideoDetectionOverlay;
    window.createVideoViewer = createVideoViewer;
})();
