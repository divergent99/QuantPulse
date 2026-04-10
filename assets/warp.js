// Hyperspeed warp background — Three.js r128
(function () {
    if (typeof THREE === "undefined") return;

    const canvas = document.createElement("canvas");
    canvas.id = "warp-canvas";
    canvas.style.cssText = "position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;opacity:0.35;";
    document.body.insertBefore(canvas, document.body.firstChild);

    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    renderer.setSize(window.innerWidth, window.innerHeight);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 2;

    const count = 1800;
    const positions = new Float32Array(count * 3);
    const velocities = new Float32Array(count);

    for (let i = 0; i < count; i++) {
        positions[i * 3]     = (Math.random() - 0.5) * 10;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
        velocities[i] = 0.002 + Math.random() * 0.006;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    const mat = new THREE.PointsMaterial({
        color: 0x00d4ff,
        size: 0.018,
        transparent: true,
        opacity: 0.7,
        sizeAttenuation: true,
    });

    const stars = new THREE.Points(geo, mat);
    scene.add(stars);

    let speed = 0.0008;
    let targetSpeed = 0.004;
    let boosting = false;
    let boostTimeout;

    document.addEventListener("click", function () {
        clearTimeout(boostTimeout);
        targetSpeed = 0.022;
        boosting = true;
        boostTimeout = setTimeout(function () {
            targetSpeed = 0.004;
            boosting = false;
        }, 900);
    });

    function animate() {
        requestAnimationFrame(animate);
        speed += (targetSpeed - speed) * 0.04;

        const pos = geo.attributes.position.array;
        for (let i = 0; i < count; i++) {
            pos[i * 3 + 2] += speed * 12;
            if (pos[i * 3 + 2] > 5) {
                pos[i * 3]     = (Math.random() - 0.5) * 10;
                pos[i * 3 + 1] = (Math.random() - 0.5) * 10;
                pos[i * 3 + 2] = -10;
            }
        }
        geo.attributes.position.needsUpdate = true;
        mat.opacity = boosting ? 0.9 : 0.6;
        mat.size = boosting ? 0.028 : 0.018;

        renderer.render(scene, camera);
    }

    animate();

    window.addEventListener("resize", function () {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
})();