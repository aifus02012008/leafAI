/**
 * LEAF_AI - Natural Botanical 3D Leaf Visualizer (Three.js)
 * Mô phỏng lá cây 3D tự nhiên, mềm mại, màu xanh thực vật tự nhiên (không chói neon).
 */

class Leaf3DVisualizer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container || typeof THREE === 'undefined') {
      return;
    }

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.leafMesh = null;
    this.veinMesh = null;
    this.animId = null;
    this.isScanning = false;

    this.init();
  }

  init() {
    const width = this.container.clientWidth || 200;
    const height = this.container.clientHeight || 240;

    // Scene & Camera
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    this.camera.position.set(0, 0, 18);

    // Renderer nền trong suốt
    this.renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(window.devicePixelRatio || 1);
    this.container.innerHTML = '';
    this.container.appendChild(this.renderer.domElement);

    // Ánh sáng tự nhiên mềm mại
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
    this.scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfef08a, 1.5);
    sunLight.position.set(5, 10, 8);
    this.scene.add(sunLight);

    const bounceLight = new THREE.DirectionalLight(0x86efac, 0.8);
    bounceLight.position.set(-5, -5, 5);
    this.scene.add(bounceLight);

    // Dáng lá chét vải (thuôn dài, mép nguyên)
    const shape = new THREE.Shape();
    shape.moveTo(0, -6);
    shape.bezierCurveTo(2.8, -4, 4.2, 0, 3.2, 4);
    shape.bezierCurveTo(2.2, 6, 0.8, 7.5, 0, 8);
    shape.bezierCurveTo(-0.8, 7.5, -2.2, 6, -3.2, 4);
    shape.bezierCurveTo(-4.2, 0, -2.8, -4, 0, -6);

    const extrudeSettings = {
      depth: 0.25,
      bevelEnabled: true,
      bevelSegments: 4,
      steps: 2,
      bevelSize: 0.15,
      bevelThickness: 0.15
    };
    const geometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    geometry.center();

    // Chất liệu màu xanh lá cây tự nhiên (Organic Leaf Green)
    const leafMaterial = new THREE.MeshStandardMaterial({
      color: 0x16a34a,
      roughness: 0.35,
      metalness: 0.05,
      flatShading: false
    });
    this.leafMesh = new THREE.Mesh(geometry, leafMaterial);
    this.scene.add(this.leafMesh);

    // Gân lá chính màu vàng chanh nhạt tự nhiên
    const veinCurve = new THREE.LineCurve3(
      new THREE.Vector3(0, -5.8, 0.22),
      new THREE.Vector3(0, 7.6, 0.22)
    );
    const veinGeom = new THREE.TubeGeometry(veinCurve, 20, 0.1, 8, false);
    const veinMat = new THREE.MeshStandardMaterial({ color: 0x86efac, roughness: 0.4 });
    this.veinMesh = new THREE.Mesh(veinGeom, veinMat);
    this.scene.add(this.veinMesh);

    // Tương tác xoay nhẹ bằng chuột
    let isDragging = false;
    let prevMousePos = { x: 0, y: 0 };

    this.container.addEventListener('mousedown', (e) => {
      isDragging = true;
      prevMousePos = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mouseup', () => isDragging = false);

    window.addEventListener('mousemove', (e) => {
      if (!isDragging || !this.leafMesh) return;
      const dx = e.clientX - prevMousePos.x;
      const dy = e.clientY - prevMousePos.y;
      this.leafMesh.rotation.y += dx * 0.01;
      this.veinMesh.rotation.y += dx * 0.01;
      this.leafMesh.rotation.x += dy * 0.01;
      this.veinMesh.rotation.x += dy * 0.01;
      prevMousePos = { x: e.clientX, y: e.clientY };
    });

    this.animate();
  }

  animate() {
    this.animId = requestAnimationFrame(() => this.animate());

    const rotSpeed = this.isScanning ? 0.025 : 0.005;
    if (this.leafMesh && this.veinMesh) {
      this.leafMesh.rotation.y += rotSpeed;
      this.veinMesh.rotation.y += rotSpeed;
    }

    this.renderer.render(this.scene, this.camera);
  }

  setScanning(isScanning) {
    this.isScanning = isScanning;
    if (this.leafMesh) {
      this.leafMesh.material.color.setHex(isScanning ? 0xf59e0b : 0x16a34a);
    }
  }

  resize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }
}
