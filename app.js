const presets = {
  ttClassic: [
    layer("Дерево", 2.8, 420000, 30, 0.42, 0.32, "none"),
    layer("Карбон", 0.45, 980000, 15, 0.33, 0.26, "none"),
    layer("Дерево", 2.6, 410000, 28, 0.42, 0.33, "none"),
    layer("Губка", 2.0, 90000, 48, 0.62, 0.51, "none"),
    layer("Топшит", 1.7, 120000, 36, 0.92, 0.8, "out")
  ],
  ttInverted: [
    layer("Дерево", 2.8, 420000, 30, 0.42, 0.32, "none"),
    layer("Карбон", 0.45, 980000, 15, 0.33, 0.26, "none"),
    layer("Дерево", 2.6, 410000, 28, 0.42, 0.33, "none"),
    layer("Губка", 2.1, 98000, 49, 0.66, 0.54, "none"),
    layer("Топшит", 1.8, 130000, 38, 0.96, 0.84, "in")
  ],
  hardCourt: [
    layer("Полимер", 2.0, 300000, 30, 0.5, 0.4, "none"),
    layer("Бетон", 20, 1300000, 12, 0.46, 0.38, "none")
  ]
};

const state = {
  layers: cloneLayers(presets.ttClassic),
  result: null,
  compareRuns: [],
  anim: { idx: 0, playing: false, raf: 0, lastTs: 0 }
};

const el = {
  tbody: document.querySelector("#layersTable tbody"),
  validation: document.getElementById("validation"),
  metrics: document.getElementById("metrics"),
  compare: document.getElementById("compare"),
  checksOutput: document.getElementById("checksOutput"),
  canvas: document.getElementById("vizCanvas"),
  timeSlider: document.getElementById("timeSlider"),
  chartForces: document.getElementById("chartForces"),
  chartKin: document.getElementById("chartKinematics")
};

wire();
renderLayers();
runAndRender();

function wire() {
  document.getElementById("addLayer").addEventListener("click", () => {
    state.layers.push(layer("Новый", 1.0, 100000, 20, 0.6, 0.5, "none"));
    renderLayers();
  });

  document.getElementById("applyPreset").addEventListener("click", () => {
    const key = document.getElementById("presetSelect").value;
    state.layers = cloneLayers(presets[key]);
    renderLayers();
    runAndRender();
  });

  document.getElementById("runSim").addEventListener("click", runAndRender);

  document.getElementById("saveRun").addEventListener("click", () => {
    if (!state.result) return;
    const label = `${new Date().toLocaleTimeString()} (${document.getElementById("ballType").value})`;
    state.compareRuns.unshift({ label, m: state.result.metrics });
    state.compareRuns = state.compareRuns.slice(0, 3);
    renderCompare();
  });

  document.getElementById("runChecks").addEventListener("click", runSelfChecks);

  el.timeSlider.addEventListener("input", () => {
    if (!state.result) return;
    stopAnimation();
    state.anim.idx = Math.floor(parseFloat(el.timeSlider.value) * (state.result.frames.length - 1));
    drawFrame(state.result.frames[state.anim.idx]);
  });

  ["showVectors", "showPressure", "showPatch"].forEach((id) => {
    document.getElementById(id).addEventListener("change", () => {
      if (state.result) drawFrame(state.result.frames[state.anim.idx]);
    });
  });

  document.getElementById("animSpeed").addEventListener("input", () => {
    if (state.result && state.anim.playing) {
      stopAnimation();
      startAnimation();
    }
  });

  el.canvas.addEventListener("click", () => {
    if (!state.result) return;
    if (state.anim.playing) {
      stopAnimation();
    } else {
      startAnimation();
    }
  });
}

function layer(material, thicknessMm, k, c, muS, muK, pimples) {
  return {
    material,
    thicknessMm,
    stiffness: k,
    damping: c,
    muS,
    muK,
    pimples,
    pimpleStiffness: 220,
    pimpleDensity: 8,
    pimpleHeightMm: 1.0
  };
}

function cloneLayers(arr) {
  return arr.map((x) => ({ ...x }));
}

function renderLayers() {
  el.tbody.innerHTML = "";
  state.layers.forEach((lay, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input value="${lay.material}" data-k="material"/></td>
      <td><input type="number" step="0.1" value="${lay.thicknessMm}" data-k="thicknessMm"/></td>
      <td><input type="number" step="1000" value="${lay.stiffness}" data-k="stiffness"/></td>
      <td><input type="number" step="1" value="${lay.damping}" data-k="damping"/></td>
      <td><input type="number" step="0.01" value="${lay.muS}" data-k="muS"/></td>
      <td><input type="number" step="0.01" value="${lay.muK}" data-k="muK"/></td>
      <td>
        <select data-k="pimples">
          <option value="none" ${lay.pimples === "none" ? "selected" : ""}>нет</option>
          <option value="out" ${lay.pimples === "out" ? "selected" : ""}>наружу</option>
          <option value="in" ${lay.pimples === "in" ? "selected" : ""}>внутрь</option>
        </select>
      </td>
      <td>
        <button data-act="up">↑</button>
        <button data-act="down">↓</button>
        <button data-act="del">×</button>
      </td>
    `;

    tr.querySelectorAll("input,select").forEach((inp) => {
      inp.addEventListener("change", () => {
        const key = inp.dataset.k;
        let val = inp.value;
        if (key !== "material" && key !== "pimples") val = parseFloat(val);
        state.layers[i][key] = val;
        validateLayers();
        runAndRender();
      });
    });

    tr.querySelector("[data-act='up']").addEventListener("click", () => {
      if (i < 1) return;
      [state.layers[i - 1], state.layers[i]] = [state.layers[i], state.layers[i - 1]];
      renderLayers();
      runAndRender();
    });

    tr.querySelector("[data-act='down']").addEventListener("click", () => {
      if (i >= state.layers.length - 1) return;
      [state.layers[i + 1], state.layers[i]] = [state.layers[i], state.layers[i + 1]];
      renderLayers();
      runAndRender();
    });

    tr.querySelector("[data-act='del']").addEventListener("click", () => {
      state.layers.splice(i, 1);
      renderLayers();
      runAndRender();
    });

    el.tbody.appendChild(tr);
  });

  validateLayers();
}

function validateLayers() {
  if (!state.layers.length) {
    el.validation.textContent = "Нужен минимум 1 слой";
    el.validation.style.color = "#a2281f";
    return false;
  }
  for (const lay of state.layers) {
    if (
      lay.thicknessMm <= 0 || lay.stiffness <= 0 || lay.damping < 0 || lay.muS < 0 || lay.muK < 0 || lay.muK > lay.muS
    ) {
      el.validation.textContent = "Ошибка в параметрах слоев: t>0, k>0, c>=0, mu_k <= mu_s";
      el.validation.style.color = "#a2281f";
      return false;
    }
  }
  el.validation.textContent = "Слойная структура валидна";
  el.validation.style.color = "#356b2b";
  return true;
}

function readInput() {
  const speed = num("inSpeed", 11);
  const angleDeg = num("inAngle", 35);
  const spinRps = num("inSpin", 120) * parseFloat(document.getElementById("spinDir").value);

  const ballType = document.getElementById("ballType").value;
  const rad = num("ballRadius", 20) / 1000;

  const ball = {
    type: ballType,
    radius: rad,
    mass: ballType === "hollow" ? 0.0027 : 0.014,
    stiffness: num("ballStiff", 62000),
    damping: num("ballDamp", 10.5),
    inertiaFactor: ballType === "hollow" ? 0.67 : 0.4
  };

  return {
    collision: {
      speed,
      angleDeg,
      omega: spinRps * Math.PI * 2
    },
    ball,
    layers: state.layers.map((x) => ({ ...x }))
  };
}

function runAndRender() {
  if (!validateLayers()) return;

  const input = readInput();
  const result = simulateContact(input);
  state.result = result;
  state.anim.idx = 0;
  renderMetrics(result.metrics);
  renderCompare();
  renderCharts(result);
  el.timeSlider.value = "0";
  drawFrame(result.frames[0]);
  startAnimation();
}

function simulateContact({ collision, ball, layers }) {
  const g = 9.81;
  const dt = 0.00012;
  const maxT = 0.08;
  const theta = (collision.angleDeg * Math.PI) / 180;

  let vn = -Math.max(0.1, collision.speed * Math.sin(theta));
  let vt = collision.speed * Math.cos(theta);
  let omega = collision.omega;

  let depth = 0;
  let depthRate = -vn;
  let peakDepth = 0;

  const m = ball.mass;
  const I = ball.inertiaFactor * m * ball.radius * ball.radius;

  const eq = equivalentSurface(layers);
  const kN = eq.kN + ball.stiffness;
  const cN = eq.cN + ball.damping;

  const kT = eq.kT;
  let stickDisp = 0;
  let pimpleTilt = 0;

  const t = [];
  const normal = [];
  const tang = [];
  const def = [];
  const slip = [];
  const omg = [];
  const pressure = [];
  const patchR = [];

  let contactStarted = false;
  let contactEnded = false;
  let energyLoss = 0;
  let slipTime = 0;
  let impulseN = 0;
  let impulseT = 0;

  for (let time = 0; time < maxT; time += dt) {
    let fn = 0;
    let ft = 0;

    if (depth > 0 || vn < 0) {
      contactStarted = true;
      const x = Math.max(0, depth);
      const xn = Math.pow(x + 1e-9, 1.35);
      fn = Math.max(0, kN * xn + cN * Math.max(0, depthRate));

      const vRel = vt - omega * ball.radius;
      const muS = eq.muS * (1 + Math.abs(pimpleTilt) * 0.35);
      const muK = eq.muK * (1 + Math.abs(pimpleTilt) * 0.2);

      stickDisp += vRel * dt;
      const ftTrial = -kT * stickDisp;
      const fStaticMax = muS * fn;
      if (Math.abs(ftTrial) <= fStaticMax) {
        ft = ftTrial;
      } else {
        ft = -Math.sign(vRel || 1) * muK * fn;
        stickDisp = -ft / Math.max(1, kT);
        slipTime += dt;
      }

      if (eq.hasPimples) {
        const tiltGain = eq.pimpleCompliance;
        const tiltRestore = eq.pimpleRestore;
        pimpleTilt += dt * (tiltGain * ft - tiltRestore * pimpleTilt);
        pimpleTilt = clamp(pimpleTilt, -0.42, 0.42);
        ft *= 1 + 0.2 * Math.abs(pimpleTilt);
      }

      const an = (fn / m) - g;
      const at = ft / m;
      const alpha = -(ft * ball.radius) / I;

      vn += an * dt;
      vt += at * dt;
      omega += alpha * dt;

      depthRate += -vn * dt * 900;
      depth += depthRate * dt;
      depth = Math.max(0, depth);
      peakDepth = Math.max(peakDepth, depth);

      impulseN += fn * dt;
      impulseT += ft * dt;
      energyLoss += Math.abs(ft * (vRel * dt)) + cN * depthRate * depthRate * dt;

      if (contactStarted && depth <= 0 && vn > 0.02 && time > 0.0016) {
        contactEnded = true;
      }
    }

    const pr = fn / Math.max(1e-6, Math.PI * contactPatchRadius(ball.radius, depth) ** 2);
    t.push(time);
    normal.push(fn);
    tang.push(ft);
    def.push(depth);
    slip.push(vt - omega * ball.radius);
    omg.push(omega);
    pressure.push(pr);
    patchR.push(contactPatchRadius(ball.radius, depth));

    if (contactEnded) {
      break;
    }
  }

  const contactTime = t[t.length - 1] || 0;
  const post = simulatePostFlight(vt, vn, omega, contactTime, 0.12, 0.0012);

  const frames = buildFrames({
    t,
    normal,
    tang,
    def,
    slip,
    omg,
    pressure,
    patchR,
    post,
    layers,
    ball,
    pimpleTilt
  });

  const outSpeed = Math.hypot(post.vx[post.vx.length - 1], post.vy[post.vy.length - 1]);
  const outAngle = Math.atan2(post.vy[post.vy.length - 1], post.vx[post.vx.length - 1]) * 180 / Math.PI;

  const metrics = {
    vOut: outSpeed,
    omegaOut: post.omega[post.omega.length - 1],
    angleOut: outAngle,
    contactTimeMs: contactTime * 1000,
    maxDefMm: peakDepth * 1000,
    slipShare: (slipTime / Math.max(contactTime, 1e-6)) * 100,
    energyLoss,
    impulseN,
    impulseT
  };

  return { t, normal, tang, def, slip, omg, pressure, patchR, post, metrics, frames };
}

function equivalentSurface(layers) {
  let kAcc = 0;
  let cAcc = 0;
  let muS = 0;
  let muK = 0;
  let wMu = 0;
  let hasPimples = false;
  let pimpleCompliance = 0;
  let pimpleRestore = 0;

  layers.forEach((lay, idx) => {
    const thick = Math.max(0.1, lay.thicknessMm) / 1000;
    const weight = 1 / (1 + idx * 0.6);
    const k = (lay.stiffness / thick) * weight * 0.00045;
    const c = lay.damping * weight;

    kAcc += 1 / Math.max(1e-8, k);
    cAcc += c;
    muS += lay.muS * weight;
    muK += lay.muK * weight;
    wMu += weight;

    if (lay.pimples !== "none") {
      hasPimples = true;
      const sign = lay.pimples === "out" ? 1 : 0.7;
      pimpleCompliance += sign * (1 / Math.max(40, lay.pimpleStiffness || 220));
      pimpleRestore += 14 + idx * 2;
    }
  });

  return {
    kN: 1 / Math.max(1e-8, kAcc),
    cN: cAcc,
    kT: (1 / Math.max(1e-8, kAcc)) * 0.32,
    muS: muS / Math.max(1, wMu),
    muK: muK / Math.max(1, wMu),
    hasPimples,
    pimpleCompliance: pimpleCompliance * 360,
    pimpleRestore: Math.max(14, pimpleRestore)
  };
}

function simulatePostFlight(vx0, vy0, omega0, tStart, duration, dt) {
  const g = 9.81;
  const x = [];
  const y = [];
  const vx = [];
  const vy = [];
  const omega = [];
  let px = 0;
  let py = 0;
  let vxC = vx0;
  let vyC = vy0;
  let w = omega0;

  for (let t = tStart; t < tStart + duration; t += dt) {
    vyC -= g * dt;
    px += vxC * dt;
    py += vyC * dt;
    w *= 1 - 0.02 * dt;

    x.push(px);
    y.push(py);
    vx.push(vxC);
    vy.push(vyC);
    omega.push(w);
  }

  return { x, y, vx, vy, omega };
}

function buildFrames(src) {
  const frames = [];
  const cx = 260;
  const surfaceY = 260;
  const scale = 3700;
  const totalT = src.t[src.t.length - 1] + 0.12;

  for (let i = 0; i < src.t.length; i++) {
    const rPx = src.ball.radius * scale;
    const dPx = src.def[i] * scale;
    frames.push({
      phase: "contact",
      t: src.t[i],
      surfaceY,
      ballX: cx + i * 1.2,
      ballY: surfaceY - rPx + dPx,
      radius: rPx,
      def: src.def[i],
      fn: src.normal[i],
      ft: src.tang[i],
      slip: src.slip[i],
      pressure: src.pressure[i],
      patch: src.patchR[i],
      omega: src.omg[i],
      pimpleTilt: src.pimpleTilt,
      layers: src.layers,
      totalT
    });
  }

  for (let j = 0; j < src.post.x.length; j++) {
    const rPx = src.ball.radius * scale;
    const x = cx + src.t.length * 1.2 + src.post.x[j] * 180;
    const y = surfaceY - rPx - src.post.y[j] * 180;
    frames.push({
      phase: "flight",
      t: src.t[src.t.length - 1] + j * 0.0012,
      surfaceY,
      ballX: x,
      ballY: y,
      radius: rPx,
      def: 0,
      fn: 0,
      ft: 0,
      slip: 0,
      pressure: 0,
      patch: 0,
      omega: src.post.omega[j],
      pimpleTilt: 0,
      layers: src.layers,
      totalT
    });
  }
  return frames;
}

function drawFrame(frame) {
  const ctx = el.canvas.getContext("2d");
  const w = el.canvas.width;
  const h = el.canvas.height;
  ctx.clearRect(0, 0, w, h);

  const layers = frame.layers;
  drawBackground(ctx, w, h);
  drawLayers(ctx, layers, frame.surfaceY, frame.def, frame.patch, frame.pimpleTilt);
  drawBall(ctx, frame);

  if (document.getElementById("showPatch").checked && frame.patch > 0) {
    drawPatch(ctx, frame);
  }
  if (document.getElementById("showPressure").checked && frame.patch > 0) {
    drawPressureMap(ctx, frame);
  }
  if (document.getElementById("showVectors").checked) {
    drawVectors(ctx, frame);
  }

  ctx.fillStyle = "#2b2419";
  ctx.font = "13px IBM Plex Sans";
  ctx.fillText(`t = ${(frame.t * 1000).toFixed(2)} ms (${frame.phase})`, 16, 24);
}

function drawBackground(ctx, w, h) {
  const grd = ctx.createLinearGradient(0, 0, 0, h);
  grd.addColorStop(0, "#fff9ed");
  grd.addColorStop(1, "#f2e7d2");
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, w, h);
}

function drawLayers(ctx, layers, yTop, def, patch, pimpleTilt) {
  const palette = ["#d5b690", "#4f6b80", "#c9a57a", "#f0be7d", "#a7452d", "#7e4f35"];
  const width = el.canvas.width;
  let y = yTop;

  layers.forEach((lay, i) => {
    const t = lay.thicknessMm * 3.5;
    ctx.fillStyle = palette[i % palette.length];
    ctx.fillRect(0, y, width, t);

    if (i === layers.length - 1 && lay.pimples !== "none") {
      const count = Math.max(5, Math.floor(lay.pimpleDensity || 9));
      const step = 48;
      const base = y;
      for (let x = 20; x < width - 20; x += step) {
        const local = Math.exp(-((x - 260) ** 2) / Math.max(3500, patch * 1.1e8));
        const bend = pimpleTilt * local * (lay.pimples === "out" ? 48 : 32);
        const h = (lay.pimpleHeightMm || 1) * 16;
        ctx.strokeStyle = lay.pimples === "out" ? "#703220" : "#3d2418";
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x, base);
        ctx.lineTo(x + bend, base - h);
        ctx.stroke();
      }
    }

    y += t;
  });

  if (def > 0) {
    ctx.strokeStyle = "#822e1d";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let x = 0; x <= width; x += 4) {
      const g = Math.exp(-((x - 260) ** 2) / Math.max(900, patch * 9e7));
      const yy = yTop + def * 2800 * g;
      if (x === 0) ctx.moveTo(x, yy);
      else ctx.lineTo(x, yy);
    }
    ctx.stroke();
  }
}

function drawBall(ctx, frame) {
  ctx.save();
  ctx.fillStyle = "#f8f8f5";
  ctx.strokeStyle = "#4a4a4a";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(frame.ballX, frame.ballY, frame.radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  const rot = frame.omega * 0.0008;
  ctx.translate(frame.ballX, frame.ballY);
  ctx.rotate(rot);
  ctx.strokeStyle = "#ba3f1f";
  ctx.lineWidth = 1.4;
  for (let i = -2; i <= 2; i++) {
    ctx.beginPath();
    ctx.arc(0, 0, frame.radius * (0.3 + Math.abs(i) * 0.12), -0.6, 0.6);
    ctx.stroke();
  }
  ctx.restore();
}

function drawPatch(ctx, frame) {
  const r = Math.max(2, frame.patch * 3200);
  ctx.fillStyle = "rgba(140,30,20,0.25)";
  ctx.beginPath();
  ctx.ellipse(frame.ballX, frame.surfaceY + 2, r, r * 0.34, 0, 0, Math.PI * 2);
  ctx.fill();
}

function drawPressureMap(ctx, frame) {
  const r = Math.max(5, frame.patch * 3400);
  const grd = ctx.createRadialGradient(frame.ballX, frame.surfaceY, 2, frame.ballX, frame.surfaceY, r);
  grd.addColorStop(0, "rgba(186,61,32,0.38)");
  grd.addColorStop(1, "rgba(186,61,32,0.01)");
  ctx.fillStyle = grd;
  ctx.beginPath();
  ctx.arc(frame.ballX, frame.surfaceY, r, 0, Math.PI * 2);
  ctx.fill();
}

function drawVectors(ctx, frame) {
  const scale = 0.015;
  vector(ctx, frame.ballX, frame.ballY, 0, -frame.fn * scale, "#1d5f79", "Fn");
  vector(ctx, frame.ballX, frame.ballY, frame.ft * scale, 0, "#b44617", "Ft");
  vector(ctx, frame.ballX, frame.ballY, frame.slip * 36, 0, "#47702b", "v_rel");
}

function vector(ctx, x, y, dx, dy, color, label) {
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x + dx, y + dy);
  ctx.stroke();
  const ang = Math.atan2(dy, dx);
  const hx = x + dx;
  const hy = y + dy;
  ctx.beginPath();
  ctx.moveTo(hx, hy);
  ctx.lineTo(hx - 7 * Math.cos(ang - 0.4), hy - 7 * Math.sin(ang - 0.4));
  ctx.lineTo(hx - 7 * Math.cos(ang + 0.4), hy - 7 * Math.sin(ang + 0.4));
  ctx.closePath();
  ctx.fill();
  ctx.font = "11px IBM Plex Sans";
  ctx.fillText(label, hx + 4, hy - 4);
}

function renderMetrics(m) {
  const rows = [
    ["v_out, м/с", m.vOut.toFixed(3)],
    ["ω_out, рад/с", m.omegaOut.toFixed(2)],
    ["угол выхода, °", m.angleOut.toFixed(2)],
    ["контакт, мс", m.contactTimeMs.toFixed(2)],
    ["макс. прогиб, мм", m.maxDefMm.toFixed(3)],
    ["доля скольжения, %", m.slipShare.toFixed(1)],
    ["потери энергии", m.energyLoss.toFixed(3)],
    ["J_n", m.impulseN.toFixed(3)]
  ];
  el.metrics.innerHTML = rows
    .map(([k, v]) => `<div class="metric"><div class="k">${k}</div><div class="v">${v}</div></div>`)
    .join("");
}

function renderCompare() {
  if (!state.compareRuns.length) {
    el.compare.innerHTML = "<p>Сохраните до 3 прогонов для сравнения.</p>";
    return;
  }
  let html = "<table><thead><tr><th>Run</th><th>v_out</th><th>omega_out</th><th>contact ms</th><th>max def mm</th><th>slip %</th></tr></thead><tbody>";
  state.compareRuns.forEach((r) => {
    html += `<tr><td>${r.label}</td><td>${r.m.vOut.toFixed(2)}</td><td>${r.m.omegaOut.toFixed(1)}</td><td>${r.m.contactTimeMs.toFixed(2)}</td><td>${r.m.maxDefMm.toFixed(3)}</td><td>${r.m.slipShare.toFixed(1)}</td></tr>`;
  });
  html += "</tbody></table>";
  el.compare.innerHTML = html;
}

function renderCharts(res) {
  drawSeries(el.chartForces, res.t, [
    { y: res.normal, color: "#1d5f79", name: "Fn" },
    { y: res.tang, color: "#b44617", name: "Ft" }
  ], "Силы, Н");

  drawSeries(el.chartKin, res.t, [
    { y: res.def.map((x) => x * 1000), color: "#6a2f87", name: "deform mm" },
    { y: res.slip, color: "#3f6e25", name: "v_rel" },
    { y: res.omg.map((x) => x * 0.01), color: "#7e5231", name: "omega*0.01" }
  ], "Кинематика");
}

function drawSeries(canvas, tx, lines, title) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#fffdf7";
  ctx.fillRect(0, 0, w, h);

  const pad = { l: 45, r: 10, t: 22, b: 26 };
  const xMin = tx[0] || 0;
  const xMax = tx[tx.length - 1] || 1;

  let yMin = Infinity;
  let yMax = -Infinity;
  lines.forEach((ln) => {
    ln.y.forEach((v) => {
      yMin = Math.min(yMin, v);
      yMax = Math.max(yMax, v);
    });
  });
  if (!Number.isFinite(yMin) || yMin === yMax) {
    yMin = -1;
    yMax = 1;
  }

  const sx = (x) => pad.l + ((x - xMin) / Math.max(1e-8, xMax - xMin)) * (w - pad.l - pad.r);
  const sy = (y) => h - pad.b - ((y - yMin) / Math.max(1e-8, yMax - yMin)) * (h - pad.t - pad.b);

  ctx.strokeStyle = "#9d8e73";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad.l, pad.t);
  ctx.lineTo(pad.l, h - pad.b);
  ctx.lineTo(w - pad.r, h - pad.b);
  ctx.stroke();

  lines.forEach((ln) => {
    ctx.strokeStyle = ln.color;
    ctx.lineWidth = 1.8;
    ctx.beginPath();
    for (let i = 0; i < tx.length; i++) {
      const x = sx(tx[i]);
      const y = sy(ln.y[i]);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  });

  ctx.fillStyle = "#2b2419";
  ctx.font = "12px IBM Plex Sans";
  ctx.fillText(title, 8, 14);
  ctx.fillText(`${xMin.toFixed(3)}s`, pad.l - 16, h - 8);
  ctx.fillText(`${xMax.toFixed(3)}s`, w - 48, h - 8);

  let xLegend = w - 90;
  lines.forEach((ln) => {
    ctx.fillStyle = ln.color;
    ctx.fillRect(xLegend, 8, 10, 8);
    ctx.fillStyle = "#2b2419";
    ctx.fillText(ln.name, xLegend + 14, 15);
    xLegend -= 95;
  });
}

function startAnimation() {
  if (!state.result || state.anim.playing) return;
  state.anim.playing = true;
  state.anim.lastTs = 0;
  state.anim.raf = requestAnimationFrame(tick);
}

function stopAnimation() {
  state.anim.playing = false;
  if (state.anim.raf) cancelAnimationFrame(state.anim.raf);
}

function tick(ts) {
  if (!state.anim.playing || !state.result) return;
  const frames = state.result.frames;
  const speed = parseFloat(document.getElementById("animSpeed").value);

  if (!state.anim.lastTs) state.anim.lastTs = ts;
  const dt = ts - state.anim.lastTs;
  state.anim.lastTs = ts;

  const step = Math.max(1, Math.floor((dt / 14) * speed));
  state.anim.idx += step;
  if (state.anim.idx >= frames.length) state.anim.idx = 0;

  drawFrame(frames[state.anim.idx]);
  el.timeSlider.value = (state.anim.idx / Math.max(1, frames.length - 1)).toFixed(4);

  state.anim.raf = requestAnimationFrame(tick);
}

function runSelfChecks() {
  const out = [];

  const base = readInput();
  const baseRes = simulateContact(base);
  out.push(check(baseRes.metrics.contactTimeMs > 0 && Number.isFinite(baseRes.metrics.vOut), "Расчет стабилен на базовом сценарии"));

  const solid = { ...base, ball: { ...base.ball, type: "solid", mass: 0.014, inertiaFactor: 0.4 } };
  const solidRes = simulateContact(solid);
  out.push(check(Math.abs(baseRes.metrics.contactTimeMs - solidRes.metrics.contactTimeMs) > 0.02, "Полый/сплошной дают различимый контакт"));

  const stiffLayers = base.layers.map((l) => ({ ...l, stiffness: l.stiffness * 1.8 }));
  const softRes = simulateContact(base);
  const hardRes = simulateContact({ ...base, layers: stiffLayers });
  out.push(check(hardRes.metrics.maxDefMm < softRes.metrics.maxDefMm, "Рост жесткости уменьшает прогиб"));

  const highFric = base.layers.map((l) => ({ ...l, muS: l.muS * 1.35, muK: l.muK * 1.35 }));
  const fricRes = simulateContact({ ...base, layers: highFric });
  out.push(check(fricRes.metrics.slipShare <= baseRes.metrics.slipShare + 6, "Рост трения уменьшает/сдерживает скольжение"));

  const outLayer = cloneLayers(base.layers);
  if (outLayer.length) outLayer[outLayer.length - 1].pimples = "out";
  const inLayer = cloneLayers(base.layers);
  if (inLayer.length) inLayer[inLayer.length - 1].pimples = "in";
  const outRes = simulateContact({ ...base, layers: outLayer });
  const inRes = simulateContact({ ...base, layers: inLayer });
  out.push(check(Math.abs(outRes.metrics.omegaOut - inRes.metrics.omegaOut) > 0.5, "Шипы наружу/внутрь меняют итоговый spin"));

  el.checksOutput.textContent = out.join("\n");
}

function check(cond, txt) {
  return `${cond ? "OK" : "FAIL"}: ${txt}`;
}

function contactPatchRadius(radius, depth) {
  return Math.sqrt(Math.max(0, 2 * radius * depth - depth * depth));
}

function num(id, fallback) {
  const v = parseFloat(document.getElementById(id).value);
  return Number.isFinite(v) ? v : fallback;
}

function clamp(v, a, b) {
  return Math.max(a, Math.min(b, v));
}
