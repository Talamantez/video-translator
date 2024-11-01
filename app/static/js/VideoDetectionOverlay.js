// VideoDetectionOverlay.js - A class to handle video detection overlays

class VideoDetectionOverlay {
    constructor(videoElement, canvasElement) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        
        // Bind methods
        this.updateCanvasSize = this.updateCanvasSize.bind(this);
        this.drawDetections = this.drawDetections.bind(this);
        
        // Initialize canvas sizing
        this.updateCanvasSize();
        
        // Set up resize observer
        this.resizeObserver = new ResizeObserver(this.updateCanvasSize);
        this.resizeObserver.observe(this.video);
        
        // Event listeners
        this.video.addEventListener('loadedmetadata', this.updateCanvasSize);
        window.addEventListener('resize', this.updateCanvasSize);
    }

    updateCanvasSize() {
        // Get the video's displayed size
        const videoRect = this.video.getBoundingClientRect();
        
        // Set canvas size to match video display size
        this.canvas.width = videoRect.width;
        this.canvas.height = videoRect.height;
        
        // Calculate scaling factors
        this.scaleX = this.canvas.width / this.video.videoWidth;
        this.scaleY = this.canvas.height / this.video.videoHeight;
    }

    drawDetections(detections, currentTime) {
        // Clear previous drawings
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Find detections within 0.5 seconds of current time
        const relevantDetections = detections.filter(
            d => Math.abs(d.timestamp - currentTime) < 0.5
        );

        relevantDetections.forEach(detection => {
            const [x1, y1, x2, y2] = detection.bbox;
            
            // Scale coordinates to match video display size
            const scaledX = x1 * this.scaleX;
            const scaledY = y1 * this.scaleY;
            const scaledWidth = (x2 - x1) * this.scaleX;
            const scaledHeight = (y2 - y1) * this.scaleY;

            // Draw detection box
            this.ctx.strokeStyle = `rgba(0, 255, 0, ${detection.confidence})`;
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(scaledX, scaledY, scaledWidth, scaledHeight);

            // Draw label background
            const label = `${detection.class} (${Math.round(detection.confidence * 100)}%)`;
            this.ctx.font = '14px Arial';
            const textMetrics = this.ctx.measureText(label);
            const padding = 4;
            const labelHeight = 20;

            this.ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            this.ctx.fillRect(
                scaledX,
                scaledY > labelHeight ? scaledY - labelHeight : scaledY,
                textMetrics.width + (padding * 2),
                labelHeight
            );

            // Draw label text
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillText(
                label,
                scaledX + padding,
                scaledY > labelHeight ? scaledY - 6 : scaledY + 14
            );
        });
    }

    destroy() {
        this.resizeObserver.disconnect();
        window.removeEventListener('resize', this.updateCanvasSize);
        this.video.removeEventListener('loadedmetadata', this.updateCanvasSize);
    }
}