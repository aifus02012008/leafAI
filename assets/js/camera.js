/**
 * LEAF_AI - Camera & Upload Management
 * Chụp ảnh trực tiếp từ webcam/camera sau tại vườn & kéo thả upload ảnh.
 */
class LeafCameraManager {
  constructor(options = {}) {
    this.videoElement = options.videoElement;
    this.captureCanvas = document.createElement('canvas');
    this.stream = null;
    this.isStreaming = false;
    this.facingMode = 'environment'; // Ưu tiên camera sau của điện thoại khi soi lá cây
    this.onImageCaptured = options.onImageCaptured || (() => {});
  }

  async startCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("Trình duyệt không hỗ trợ truy cập Camera trực tiếp.");
    }

    try {
      this.stopCamera();
      const constraints = {
        video: {
          facingMode: { ideal: this.facingMode },
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      };

      this.stream = await navigator.mediaDevices.getUserMedia(constraints);
      if (this.videoElement) {
        this.videoElement.srcObject = this.stream;
        await this.videoElement.play();
        this.isStreaming = true;
      }
      return true;
    } catch (err) {
      console.warn("Không mở được camera:", err);
      throw err;
    }
  }

  stopCamera() {
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if (this.videoElement) {
      this.videoElement.srcObject = null;
    }
    this.isStreaming = false;
  }

  toggleFacingMode() {
    this.facingMode = this.facingMode === 'user' ? 'environment' : 'user';
    return this.startCamera();
  }

  captureSnapshot() {
    if (!this.isStreaming || !this.videoElement) return null;

    const v = this.videoElement;
    const w = v.videoWidth || 640;
    const h = v.videoHeight || 480;

    this.captureCanvas.width = w;
    this.captureCanvas.height = h;
    const ctx = this.captureCanvas.getContext('2d');
    ctx.drawImage(v, 0, 0, w, h);

    const base64Data = this.captureCanvas.toDataURL('image/jpeg', 0.92);
    this.stopCamera();
    this.onImageCaptured(base64Data, "camera_capture.jpg");
    return base64Data;
  }

  initDropZone(dropZoneElement, fileInputElement) {
    if (!dropZoneElement) return;

    // Click mở file dialog
    dropZoneElement.addEventListener('click', (e) => {
      if (e.target.tagName !== 'BUTTON' && fileInputElement) {
        fileInputElement.click();
      }
    });

    // Bàn phím: Enter / Space mở hộp chọn ảnh
    dropZoneElement.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && fileInputElement) {
        e.preventDefault();
        fileInputElement.click();
      }
    });

    // Drag over
    ['dragenter', 'dragover'].forEach(eventName => {
      dropZoneElement.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZoneElement.classList.add('drag-active');
      }, false);
    });

    // Drag leave / drop
    ['dragleave', 'drop'].forEach(eventName => {
      dropZoneElement.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZoneElement.classList.remove('drag-active');
      }, false);
    });

    // Xử lý khi thả file vào
    dropZoneElement.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        this.handleFile(files[0]);
      }
    });

    // Khi chọn file qua input
    if (fileInputElement) {
      fileInputElement.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
          this.handleFile(e.target.files[0]);
          e.target.value = ''; // cho phép chọn lại cùng một ảnh
        }
      });
    }
  }

  notify(message) {
    if (window.Leaf && window.Leaf.toast) window.Leaf.toast(message);
    else alert(message);
  }

  handleFile(file) {
    if (!file.type.startsWith('image/')) {
      this.notify("Vui lòng chọn tệp ảnh hợp lệ (.jpg, .png, .webp).");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      this.notify("Ảnh lớn hơn 10 MB. Hãy chọn ảnh nhỏ hơn hoặc chụp lại.");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target.result;
      this.onImageCaptured(base64, file.name);
    };
    reader.readAsDataURL(file);
  }
}
