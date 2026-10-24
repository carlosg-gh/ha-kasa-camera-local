/* Kasa Camera (local): motion zone editor.
 * Defines <kasa-camera-zones> (dashboard card, type: custom:kasa-camera-zones) and
 * <kasa-camera-panel> (the editor panel linked from the device page). Plain web components, no build step. */

const STYLE = `
  :host { display: block; }
  .wrap { position: relative; line-height: 0; background: #000; border-radius: 8px; overflow: hidden; touch-action: none; user-select: none; }
  img { width: 100%; display: block; min-height: 180px; background: #111; }
  svg { position: absolute; inset: 0; width: 100%; height: 100%; }
  .zone { fill: rgba(3, 169, 244, 0.25); stroke: #03a9f4; stroke-width: 0.4; vector-effect: non-scaling-stroke; cursor: move; }
  .zone.sel { fill: rgba(255, 193, 7, 0.3); stroke: #ffc107; }
  .zone, .h { stroke-width: 2; }
  .h { fill: #fff; stroke: #03a9f4; cursor: grab; vector-effect: non-scaling-stroke; }
  .sel-h { stroke: #ffc107; }
  .bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 12px 0 0; line-height: normal; }
  button { font: inherit; padding: 6px 14px; border-radius: 6px; border: 1px solid var(--divider-color, #888);
           background: var(--card-background-color, #fff); color: var(--primary-text-color, #000); cursor: pointer; }
  button.primary { background: var(--primary-color, #03a9f4); color: var(--text-primary-color, #fff); border-color: transparent; }
  button:disabled { opacity: 0.5; cursor: default; }
  .msg { color: var(--secondary-text-color, #666); font-size: 0.9em; flex: 1 1 100%; }
  .err { color: var(--error-color, #db4437); }
`;

class KasaZoneEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._zones = []; // [{x:[4], y:[4]}] in percent
    this._max = 5;
    this._sel = -1;
    this._drag = null;
    this._loadedFor = null;
    this._dirty = false;
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>
      <div class="wrap"><img alt="camera snapshot"><svg viewBox="0 0 100 100" preserveAspectRatio="none"></svg></div>
      <div class="bar">
        <button id="add">Add zone</button><button id="del">Delete zone</button>
        <button id="reload">Reload from camera</button>
        <button id="save" class="primary">Save to camera</button>
        <div class="msg" id="msg"></div>
      </div>`;
    const $ = (id) => this.shadowRoot.getElementById(id);
    this._svg = this.shadowRoot.querySelector("svg");
    this._img = this.shadowRoot.querySelector("img");
    this._img.onload = () => { this._timer = setTimeout(() => this._image(), 500); };
    this._img.onerror = () => { this._timer = setTimeout(() => this._image(), 3000); };
    $("add").onclick = () => this._add();
    $("del").onclick = () => this._delete();
        $("reload").onclick = () => this._load();
    $("save").onclick = () => this._save();
    this._svg.addEventListener("pointerdown", (e) => this._down(e));
    this._svg.addEventListener("pointermove", (e) => this._move(e));
    this._svg.addEventListener("pointerup", (e) => this._up(e));
    this._svg.addEventListener("pointercancel", (e) => this._up(e));
  }

  set hass(hass) {
    this._hass = hass;
    this._start();
  }

  set entity(entity) {
    this._entity = entity;
    this._start();
  }

  _start() {
    if (!this._hass || !this._entity || this._loadedFor === this._entity) return;
    this._loadedFor = this._entity;
    this._image();
    this._load();
  }

  _say(text, error = false) {
    const msg = this.shadowRoot.getElementById("msg");
    msg.textContent = text;
    msg.classList.toggle("err", error);
  }

  connectedCallback() { this._live = true; if (this._loadedFor) this._image(); }
  disconnectedCallback() { this._live = false; clearTimeout(this._timer); }

  // Pseudo-live view: keep fetching snapshots, the next one only after the previous has loaded.
  _image() {
    clearTimeout(this._timer);
    if (this._live === false) return;
    const state = this._hass.states[this._entity];
    const pic = state && state.attributes.entity_picture;
    if (pic) this._img.src = pic + (pic.includes("?") ? "&" : "?") + "t=" + Date.now();
    else this._timer = setTimeout(() => this._image(), 3000);
  }

  async _load() {
    try {
      const res = await this._hass.callWS({ type: "kasa_camera/get_zones", entity_id: this._entity });
      this._zones = res.area || [];
      this._max = res.max || 5;
      this._sel = -1;
      this._dirty = false;
      this._say(this._zones.length ? `${this._zones.length} of ${this._max} zones. Drag corners to reshape, drag inside a zone to move it.` : "No zones set: the whole view is monitored. Add a zone to restrict detection.");
    } catch (err) {
      this._say(`Could not read zones: ${err.message || err.code}`, true);
    }
    this._draw();
  }

  async _save() {
    try {
      await this._hass.callWS({ type: "kasa_camera/set_zones", entity_id: this._entity, area: this._zones });
      this._dirty = false;
      this._say("Saved to the camera.");
    } catch (err) {
      this._say(`Save failed: ${err.message || err.code}`, true);
    }
  }

  _add() {
    if (this._zones.length >= this._max) return this._say(`The camera supports at most ${this._max} zones.`, true);
    const o = this._zones.length * 4;
    this._zones.push({ x: [20 + o, 80 - o, 80 - o, 20 + o], y: [20 + o, 20 + o, 80 - o, 80 - o] });
    this._sel = this._zones.length - 1;
    this._changed();
  }

  _delete() {
    if (this._sel < 0) return this._say("Select a zone first.", true);
    this._zones.splice(this._sel, 1);
    this._sel = -1;
    this._changed();
  }

  _changed() {
    this._dirty = true;
    this._say("Unsaved changes.");
    this._draw();
  }

  _draw() {
    let out = "";
    this._zones.forEach((z, i) => {
      const pts = z.x.map((x, k) => `${x},${z.y[k]}`).join(" ");
      const sel = i === this._sel;
      out += `<polygon class="zone${sel ? " sel" : ""}" data-z="${i}" points="${pts}"/>`;
    });
    this._zones.forEach((z, i) => {
      z.x.forEach((x, k) => {
        out += `<circle class="h${i === this._sel ? " sel-h" : ""}" data-z="${i}" data-p="${k}" cx="${x}" cy="${z.y[k]}" r="1.6"/>`;
      });
    });
    this._svg.innerHTML = out;
  }

  _pt(e) {
    const r = this._svg.getBoundingClientRect();
    return [
      Math.max(0, Math.min(99, ((e.clientX - r.left) / r.width) * 100)),
      Math.max(0, Math.min(99, ((e.clientY - r.top) / r.height) * 100)),
    ];
  }

  _down(e) {
    const t = e.target;
    if (t.dataset.z === undefined) {
      this._sel = -1;
      return this._draw();
    }
    this._sel = Number(t.dataset.z);
    const [px, py] = this._pt(e);
    this._drag = {
      z: this._sel,
      p: t.dataset.p === undefined ? null : Number(t.dataset.p),
      start: [px, py],
      orig: { x: [...this._zones[this._sel].x], y: [...this._zones[this._sel].y] },
    };
    this._svg.setPointerCapture(e.pointerId);
    this._draw();
  }

  _move(e) {
    const d = this._drag;
    if (!d) return;
    const [px, py] = this._pt(e);
    const z = this._zones[d.z];
    if (d.p !== null) {
      z.x[d.p] = Math.round(px);
      z.y[d.p] = Math.round(py);
    } else {
      // Move the whole zone, clamped so no corner leaves the image.
      const dx = Math.max(-Math.min(...d.orig.x), Math.min(99 - Math.max(...d.orig.x), px - d.start[0]));
      const dy = Math.max(-Math.min(...d.orig.y), Math.min(99 - Math.max(...d.orig.y), py - d.start[1]));
      z.x = d.orig.x.map((v) => Math.round(v + dx));
      z.y = d.orig.y.map((v) => Math.round(v + dy));
    }
    this._dirty = true;
    this._draw();
  }

  _up(e) {
    if (!this._drag) return;
    this._drag = null;
    try { this._svg.releasePointerCapture(e.pointerId); } catch (_) { /* already released */ }
    this._changed();
  }
}
customElements.define("kasa-zone-editor", KasaZoneEditor);

class KasaCameraZonesCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("Set `entity` to the Kasa camera entity");
    this._config = config;
    if (!this._editor) {
      this.attachShadow({ mode: "open" });
      this.shadowRoot.innerHTML = `<ha-card><div style="padding:16px"></div></ha-card>`;
      this._editor = document.createElement("kasa-zone-editor");
      this.shadowRoot.querySelector("div").appendChild(this._editor);
    }
    if (config.title) this.shadowRoot.querySelector("ha-card").header = config.title;
    this._editor.entity = config.entity;
  }

  set hass(hass) {
    if (this._editor) this._editor.hass = hass;
  }

  getCardSize() {
    return 6;
  }

  static getStubConfig(hass) {
    const entity = Object.keys(hass.states).find((e) => e.startsWith("camera.") && /kasa/i.test(e));
    return { entity: entity || "camera.kasa_camera", title: "Motion zones" };
  }
}
customElements.define("kasa-camera-zones", KasaCameraZonesCard);

class KasaCameraPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this.shadowRoot.innerHTML = `<style>
      :host { display: block; width: 100%; box-sizing: border-box; background: var(--primary-background-color); color: var(--primary-text-color); min-height: 100vh; }
      header { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--app-header-background-color, var(--primary-color));
               color: var(--app-header-text-color, #fff); font-size: 20px; }
      main { width: 100%; box-sizing: border-box; max-width: 1100px; margin: 0 auto; padding: 16px; }
      select { font: inherit; margin-bottom: 12px; }
    </style>
    <header><span id="menu" style="cursor:pointer">&#9776;</span><span>Kasa camera: motion zones</span></header>
    <main><div id="pick"></div></main>`;
    this.shadowRoot.getElementById("menu").onclick = () =>
      this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
  }

  set hass(hass) {
    this._hass = hass;
    if (this._editor) this._editor.hass = hass;
    if (!this._init) {
      this._init = true;
      this._setup();
    }
  }

  async _setup() {
    const pick = this.shadowRoot.getElementById("pick");
    const cams = await this._hass.callWS({ type: "kasa_camera/cameras" });
    if (!cams.length) {
      pick.textContent = "No Kasa camera is configured.";
      return;
    }
    this._editor = document.createElement("kasa-zone-editor");
    this._editor.hass = this._hass;
    if (cams.length > 1) {
      const sel = document.createElement("select");
      cams.forEach((c) => sel.add(new Option(this._hass.states[c]?.attributes.friendly_name || c, c)));
      sel.onchange = () => (this._editor.entity = sel.value);
      pick.appendChild(sel);
    }
    pick.appendChild(this._editor);
    this._editor.entity = cams[0];
  }
}
customElements.define("kasa-camera-panel", KasaCameraPanel);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "kasa-camera-zones",
  name: "Kasa camera motion zones",
  description: "Draw and edit the motion detection zones of a local Kasa camera.",
});
