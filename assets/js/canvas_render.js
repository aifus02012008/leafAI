/**
 * LEAF_AI - Clean Canvas Visualizer & Scanner
 * Vẽ Bounding Box phát hiện bệnh lá cây với phong cách giao diện sáng, tự nhiên, chuyên nghiệp.
 */
class LeafCanvasRenderer {
  constructor(canvasElement) {
    this.canvas = canvasElement;
    this.ctx = canvasElement.getContext('2d');
    this.currentImage = null;
    this.detections = [];
    this.isScanning = false;
    this.scanProgress = 0;
    this.animationFrameId = null;
    this.displayScale = 1;
    this.heatmapImage = null;
    this.showHeatmap = false;
  }

  setImage(imageSrc, callback) {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      this.currentImage = img;
      this.heatmapImage = null;
      this.showHeatmap = false;
      this.resizeCanvas();
      this.render();
      if (callback) callback();
    };
    img.src = imageSrc;
  }

  setHeatmap(heatmapSrc, callback) {
    if (!heatmapSrc) {
      this.heatmapImage = null;
      this.showHeatmap = false;
      this.render();
      if (callback) callback();
      return;
    }
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      this.heatmapImage = img;
      this.render();
      if (callback) callback();
    };
    img.src = heatmapSrc;
  }

  toggleHeatmap(show) {
    this.showHeatmap = typeof show === 'boolean' ? show : !this.showHeatmap;
    this.render();
    return this.showHeatmap;
  }

  resizeCanvas() {
    if (!this.currentImage) return;
    const container = this.canvas.parentElement;
    const cs = getComputedStyle(container);
    const padX = parseFloat(cs.paddingLeft) + parseFloat(cs.paddingRight);
    const maxWidth = (container.clientWidth - padX) || 500;
    const maxHeight = Math.min(460, Math.max(260, window.innerHeight * 0.55));

    let width = this.currentImage.naturalWidth || 640;
    let height = this.currentImage.naturalHeight || 640;

    const ratio = Math.min(maxWidth / width, maxHeight / height);
    this.canvas.width = width * ratio;
    this.canvas.height = height * ratio;
    this.displayScale = ratio;
  }

  setDetections(detections) {
    this.detections = detections || [];
    this.render();
  }

  clear() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  render() {
    this.clear();
    if (!this.currentImage) {
      this.drawPlaceholder();
      return;
    }

    // Vẽ ảnh nền (hoặc bản đồ nhiệt Grad-CAM nếu đang bật)
    if (this.showHeatmap && this.heatmapImage) {
      this.ctx.drawImage(this.heatmapImage, 0, 0, this.canvas.width, this.canvas.height);
    } else {
      this.ctx.drawImage(this.currentImage, 0, 0, this.canvas.width, this.canvas.height);
    }

    // Vẽ Bounding Boxes khoanh vùng bệnh (nếu không bật heatmap hoặc người dùng muốn cả hai)
    // Chế độ bản đồ nhiệt chỉ hiện Grad-CAM, không chồng khung lên
    if (this.detections && this.detections.length > 0 && !this.isScanning && !(this.showHeatmap && this.heatmapImage)) {
      this.drawBoundingBoxes();
    }

    // Vẽ hiệu ứng quét nếu đang phân tích
    if (this.isScanning) {
      this.drawScanningLine();
    }
  }

  drawPlaceholder() {
    const w = this.canvas.width || 480;
    const h = this.canvas.height || 320;
    this.canvas.width = w;
    this.canvas.height = h;

    this.ctx.fillStyle = '#f8fafc';
    this.ctx.fillRect(0, 0, w, h);

    // Đường viền nhẹ
    this.ctx.strokeStyle = '#e2e8f0';
    this.ctx.lineWidth = 1;
    this.ctx.strokeRect(0, 0, w, h);

    // Chữ hướng dẫn nhẹ nhàng, thân thiện
    this.ctx.fillStyle = '#64748b';
    this.ctx.font = '500 14px "Be Vietnam Pro", system-ui, sans-serif';
    this.ctx.textAlign = 'center';
    this.ctx.fillText('Chọn ảnh hoặc bật camera để bắt đầu chẩn đoán', w / 2, h / 2);
  }

  drawBoundingBoxes() {
    const scale = this.displayScale;

    this.detections.forEach((det) => {
      const [x, y, bw, bh] = det.bbox;
      const color = det.color || '#ea580c';
      const shortName = String(det.name_vi || det.class).split(' (')[0];
      const label = `${shortName} ${Math.round(det.probability_percent || det.confidence * 100)}%`;

      const sx = x * scale;
      const sy = y * scale;
      const sw = bw * scale;
      const sh = bh * scale;

      this.ctx.save();

      // Vùng phủ bán trong suốt nhẹ làm nổi bật vết bệnh
      this.ctx.fillStyle = this.hexToRgba(color, 0.12);
      this.ctx.fillRect(sx, sy, sw, sh);

      // Viền khung rõ ràng, mềm mại (Không chói neon)
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 2.5;
      this.ctx.strokeRect(sx, sy, sw, sh);

      // Nhãn thẻ hiển thị tên bệnh và % tin cậy
      this.ctx.font = '600 12px "Be Vietnam Pro", system-ui, sans-serif';
      const textWidth = this.ctx.measureText(label).width;
      const badgeH = 22;
      const badgeW = textWidth + 14;
      const badgeY = sy - badgeH > 0 ? sy - badgeH : sy;

      // Nền nhãn màu solid
      this.ctx.fillStyle = color;
      this.ctx.fillRect(sx, badgeY, badgeW, badgeH);

      // Chữ màu trắng tương phản cao
      this.ctx.fillStyle = '#ffffff';
      this.ctx.fillText(label, sx + 7, badgeY + 15);

      this.ctx.restore();
    });
  }

  drawScanningLine() {
    const w = this.canvas.width;
    const h = this.canvas.height;
    const lineY = this.scanProgress * h;

    this.ctx.save();

    // Vùng sáng quét nhẹ nhàng tự nhiên (Màu xanh lá thanh lịch)
    const gradient = this.ctx.createLinearGradient(0, lineY - 35, 0, lineY + 5);
    gradient.addColorStop(0, 'rgba(30, 122, 76, 0)');
    gradient.addColorStop(1, 'rgba(30, 122, 76, 0.25)');

    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, lineY - 35, w, 40);

    // Thanh quét màu xanh lá cây
    this.ctx.strokeStyle = '#1e7a4c';
    this.ctx.lineWidth = 2.5;
    this.ctx.beginPath();
    this.ctx.moveTo(0, lineY);
    this.ctx.lineTo(w, lineY);
    this.ctx.stroke();

    // Chữ thông báo nhẹ nhàng
    this.ctx.fillStyle = '#135c37';
    this.ctx.font = '600 12px "Be Vietnam Pro", sans-serif';
    this.ctx.textAlign = 'right';
    this.ctx.fillText('Đang quét phân tích...', w - 16, lineY - 8);

    this.ctx.restore();
  }

  hexToRgba(hex, alpha = 0.2) {
    let c = hex.replace('#', '');
    if (c.length === 3) c = c.split('').map(x => x + x).join('');
    const num = parseInt(c, 16);
    return `rgba(${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}, ${alpha})`;
  }

  startScanning(durationMs = 2000, onComplete) {
    this.isScanning = true;
    this.scanProgress = 0;
    const startTime = performance.now();

    const loop = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / durationMs, 1);
      this.scanProgress = progress;

      this.render();

      if (progress < 1) {
        this.animationFrameId = requestAnimationFrame(loop);
      } else {
        this.isScanning = false;
        this.render();
        if (onComplete) onComplete();
      }
    };

    this.animationFrameId = requestAnimationFrame(loop);
  }

  stopScanning() {
    this.isScanning = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    this.render();
  }
}
