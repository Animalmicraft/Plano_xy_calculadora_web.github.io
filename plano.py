"""
Calculadora de Pendientes e Intersecciones
Plano Cartesiano Interactivo en Tiempo Real
Ratio 1:1 exacto entre ejes X e Y
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math


# ─── Paleta de colores ────────────────────────────────────────────────────────
BG         = "#0d1117"
PANEL_BG   = "#161b22"
BORDER     = "#30363d"
ACCENT     = "#58a6ff"
ACCENT2    = "#f78166"
ACCENT3    = "#3fb950"
ACCENT4    = "#d2a8ff"
TEXT       = "#e6edf3"
TEXT_DIM   = "#8b949e"
GRID_MAIN  = "#21262d"
GRID_SUB   = "#161b22"
AXIS_COLOR = "#484f58"
ZERO_COLOR = "#6e7681"

LINE_COLORS = ["#58a6ff", "#3fb950", "#f78166", "#d2a8ff",
               "#ffa657", "#79c0ff", "#56d364", "#ff7b72"]


# ─── Clase principal ──────────────────────────────────────────────────────────
class PlanoCartesiano(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plano Cartesiano — Calculadora de Pendientes")
        self.configure(bg=BG)
        self.resizable(True, True)

        # Estado del canvas
        self.zoom        = 50.0   # píxeles por unidad (1:1 garantizado)
        self.offset_x    = 0.0   # desplazamiento en unidades matemáticas
        self.offset_y    = 0.0
        self._drag_start = None
        self._canvas_w   = 800
        self._canvas_h   = 600

        # Lista de líneas: cada entrada es un dict con parámetros y color
        self.lineas = []

        self._build_ui()
        self._bind_events()
        self._redraw()

    # ── Construcción de la interfaz ──────────────────────────────────────────
    def _build_ui(self):
        # Panel izquierdo
        left = tk.Frame(self, bg=PANEL_BG, width=300)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(8, 0), pady=8)
        left.pack_propagate(False)

        self._build_panel(left)

        # Canvas derecho
        right = tk.Frame(self, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.canvas = tk.Canvas(right, bg=BG, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Barra de estado inferior
        self.status_var = tk.StringVar(value="Listo")
        status = tk.Label(right, textvariable=self.status_var,
                          bg=PANEL_BG, fg=TEXT_DIM, font=("Consolas", 9),
                          anchor="w", padx=8)
        status.pack(fill=tk.X, pady=(4, 0))

    def _build_panel(self, parent):
        pad = {"padx": 12, "pady": 4}

        # ── Título ──
        tk.Label(parent, text="Calculadora", bg=PANEL_BG, fg=ACCENT,
                 font=("Consolas", 13, "bold")).pack(pady=(16, 2))
        tk.Label(parent, text="Pendientes & Intersecciones", bg=PANEL_BG,
                 fg=TEXT_DIM, font=("Consolas", 9)).pack(pady=(0, 12))

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, **pad)

        # ── Modo ──
        tk.Label(parent, text="MODO", bg=PANEL_BG, fg=TEXT_DIM,
                 font=("Consolas", 8)).pack(anchor="w", **pad)

        self.modo = tk.StringVar(value="pendiente_punto")
        modos = [
            ("y = mx + b  (pendiente-intersección)", "pendiente_punto"),
            ("Dos puntos  (x₁,y₁) → (x₂,y₂)",       "dos_puntos"),
            ("Solo puntos (graficar puntos)",          "puntos"),
        ]
        for txt, val in modos:
            rb = tk.Radiobutton(parent, text=txt, variable=self.modo,
                                value=val, command=self._toggle_mode,
                                bg=PANEL_BG, fg=TEXT, selectcolor=BG,
                                activebackground=PANEL_BG,
                                font=("Consolas", 9))
            rb.pack(anchor="w", padx=16, pady=1)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, **pad)

        # ── Contenedor fijo para los frames de entrada ──
        # Todos los frames viven aquí; solo uno se muestra a la vez.
        self.input_container = tk.Frame(parent, bg=PANEL_BG)
        self.input_container.pack(fill=tk.X, padx=12, pady=4)

        # ── Entradas modo 1: m y b ──
        self.frame_mb = tk.Frame(self.input_container, bg=PANEL_BG)

        tk.Label(self.frame_mb, text="Pendiente  m",
                 bg=PANEL_BG, fg=TEXT, font=("Consolas", 9)).pack(anchor="w")
        self.ent_m = self._entry(self.frame_mb)
        self.ent_m.insert(0, "1")

        tk.Label(self.frame_mb, text="Intersección  b (eje Y)",
                 bg=PANEL_BG, fg=TEXT, font=("Consolas", 9)).pack(anchor="w", pady=(6, 0))
        self.ent_b = self._entry(self.frame_mb)
        self.ent_b.insert(0, "0")

        # ── Entradas modo 2: dos puntos ──
        self.frame_2p = tk.Frame(self.input_container, bg=PANEL_BG)

        defaults_2p = {"ent_x1": "0", "ent_y1": "0", "ent_x2": "1", "ent_y2": "1"}
        for lbl, attr in [("x₁", "ent_x1"), ("y₁", "ent_y1"),
                           ("x₂", "ent_x2"), ("y₂", "ent_y2")]:
            tk.Label(self.frame_2p, text=lbl, bg=PANEL_BG, fg=TEXT,
                     font=("Consolas", 9)).pack(anchor="w")
            e = self._entry(self.frame_2p)
            e.insert(0, defaults_2p[attr])
            setattr(self, attr, e)

        # ── Entradas modo 3: punto suelto ──
        self.frame_pt = tk.Frame(self.input_container, bg=PANEL_BG)

        for lbl, attr in [("x", "ent_px"), ("y", "ent_py")]:
            tk.Label(self.frame_pt, text=lbl, bg=PANEL_BG, fg=TEXT,
                     font=("Consolas", 9)).pack(anchor="w")
            e = self._entry(self.frame_pt)
            e.insert(0, "0")
            setattr(self, attr, e)

        # Mostrar el frame inicial (modo pendiente_punto)
        self.frame_mb.pack(fill=tk.X)

        # ── Botones ──
        btn_frame = tk.Frame(parent, bg=PANEL_BG)
        btn_frame.pack(fill=tk.X, padx=12, pady=8)

        self._btn("Agregar →", ACCENT, self._agregar, btn_frame).pack(
            fill=tk.X, pady=2)
        self._btn("Limpiar todo", ACCENT2, self._limpiar, btn_frame).pack(
            fill=tk.X, pady=2)
        self._btn("Centrar vista", ACCENT3, self._centrar, btn_frame).pack(
            fill=tk.X, pady=2)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, **pad)

        # ── Resultados ──
        tk.Label(parent, text="RESULTADOS", bg=PANEL_BG, fg=TEXT_DIM,
                 font=("Consolas", 8)).pack(anchor="w", **pad)

        self.result_frame = tk.Frame(parent, bg=PANEL_BG)
        self.result_frame.pack(fill=tk.X, padx=12)

        self.result_text = tk.Text(self.result_frame, bg=BG, fg=TEXT,
                                   font=("Consolas", 9), height=8,
                                   relief="flat", state="disabled",
                                   wrap="word")
        self.result_text.pack(fill=tk.X)

        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, **pad)

        # ── Zoom info ──
        tk.Label(parent, text="ZOOM", bg=PANEL_BG, fg=TEXT_DIM,
                 font=("Consolas", 8)).pack(anchor="w", **pad)
        self.zoom_var = tk.StringVar(value=f"1 unidad = {self.zoom:.0f} px  (1:1)")
        tk.Label(parent, textvariable=self.zoom_var, bg=PANEL_BG,
                 fg=ACCENT4, font=("Consolas", 9)).pack(anchor="w", padx=16)

        zoom_frame = tk.Frame(parent, bg=PANEL_BG)
        zoom_frame.pack(fill=tk.X, padx=12, pady=4)
        self._btn("Zoom +", ACCENT4, self._zoom_in, zoom_frame).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        self._btn("Zoom −", ACCENT4, self._zoom_out, zoom_frame).pack(
            side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # Lista de líneas
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, **pad)
        tk.Label(parent, text="LÍNEAS", bg=PANEL_BG, fg=TEXT_DIM,
                 font=("Consolas", 8)).pack(anchor="w", **pad)

        self.list_frame = tk.Frame(parent, bg=PANEL_BG)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))

    def _entry(self, parent):
        e = tk.Entry(parent, bg=BG, fg=TEXT, insertbackground=TEXT,
                     font=("Consolas", 10), relief="flat",
                     highlightthickness=1, highlightcolor=ACCENT,
                     highlightbackground=BORDER)
        e.pack(fill=tk.X, pady=2)
        e.bind("<Return>", lambda _: self._agregar())
        e.bind("<KeyRelease>", lambda _: self._preview())
        return e

    def _btn(self, text, color, cmd, parent):
        return tk.Button(parent, text=text, command=cmd,
                         bg=color, fg=BG, font=("Consolas", 9, "bold"),
                         relief="flat", padx=8, pady=5,
                         activebackground=TEXT, activeforeground=BG,
                         cursor="hand2")

    # ── Eventos ─────────────────────────────────────────────────────────────
    def _bind_events(self):
        self.canvas.bind("<Configure>",    self._on_resize)
        self.canvas.bind("<ButtonPress-1>",self._drag_start_cb)
        self.canvas.bind("<B1-Motion>",    self._drag_move_cb)
        self.canvas.bind("<ButtonRelease-1>", lambda _: setattr(self, "_drag_start", None))
        self.canvas.bind("<MouseWheel>",   self._wheel)
        self.canvas.bind("<Button-4>",     self._wheel)   # Linux scroll up
        self.canvas.bind("<Button-5>",     self._wheel)   # Linux scroll down
        self.canvas.bind("<Motion>",       self._mouse_coords)

    def _on_resize(self, event):
        self._canvas_w = event.width
        self._canvas_h = event.height
        self._redraw()

    def _drag_start_cb(self, event):
        self._drag_start = (event.x, event.y, self.offset_x, self.offset_y)

    def _drag_move_cb(self, event):
        if not self._drag_start:
            return
        sx, sy, ox, oy = self._drag_start
        dx = (event.x - sx) / self.zoom
        dy = (event.y - sy) / self.zoom
        self.offset_x = ox - dx
        self.offset_y = oy + dy
        self._redraw()

    def _wheel(self, event):
        factor = 1.12
        if event.num == 5 or event.delta < 0:
            factor = 1 / factor
        cx = self._px_to_unit_x(event.x)
        cy = self._px_to_unit_y(event.y)
        self.zoom *= factor
        self.zoom  = max(8.0, min(self.zoom, 400.0))
        # Mantener el punto bajo el cursor fijo
        self.offset_x = cx - (event.x - self._canvas_w / 2) / self.zoom
        self.offset_y = cy + (event.y - self._canvas_h / 2) / self.zoom
        self.zoom_var.set(f"1 unidad = {self.zoom:.1f} px  (1:1)")
        self._redraw()

    def _mouse_coords(self, event):
        ux = self._px_to_unit_x(event.x)
        uy = self._px_to_unit_y(event.y)
        self.status_var.set(f"x = {ux:.3f}   y = {uy:.3f}   |   zoom = {self.zoom:.1f} px/u")

    # ── Conversiones pixel ↔ unidad (1:1 EXACTO: mismo zoom en X y Y) ───────
    def _unit_to_px_x(self, ux):
        return (ux - self.offset_x) * self.zoom + self._canvas_w / 2

    def _unit_to_px_y(self, uy):
        return -(uy - self.offset_y) * self.zoom + self._canvas_h / 2

    def _px_to_unit_x(self, px):
        return (px - self._canvas_w / 2) / self.zoom + self.offset_x

    def _px_to_unit_y(self, py):
        return -((py - self._canvas_h / 2) / self.zoom) + self.offset_y

    # ── Toggle de frames según modo ──────────────────────────────────────────
    def _toggle_mode(self):
        # Ocultar todos dentro del contenedor fijo
        for f in (self.frame_mb, self.frame_2p, self.frame_pt):
            f.pack_forget()
        # Mostrar solo el frame activo (dentro de input_container, sin mover el contenedor)
        m = self.modo.get()
        if m == "pendiente_punto":
            self.frame_mb.pack(fill=tk.X)
        elif m == "dos_puntos":
            self.frame_2p.pack(fill=tk.X)
        else:
            self.frame_pt.pack(fill=tk.X)

    # ── Agregar línea / punto ────────────────────────────────────────────────
    def _agregar(self):
        color = LINE_COLORS[len(self.lineas) % len(LINE_COLORS)]
        modo  = self.modo.get()

        try:
            if modo == "pendiente_punto":
                m = float(self.ent_m.get())
                b = float(self.ent_b.get())
                self._calcular_mb(m, b)
                self.lineas.append({"tipo": "linea", "m": m, "b": b, "color": color})
                label = f"y = {m:+.3g}x {'+' if b>=0 else '−'} {abs(b):.3g}"

            elif modo == "dos_puntos":
                x1 = float(self.ent_x1.get()); y1 = float(self.ent_y1.get())
                x2 = float(self.ent_x2.get()); y2 = float(self.ent_y2.get())
                self._calcular_2p(x1, y1, x2, y2)
                if x2 == x1:
                    self.lineas.append({"tipo": "vertical", "x": x1, "color": color})
                    label = f"x = {x1}"
                else:
                    m = (y2 - y1) / (x2 - x1)
                    b = y1 - m * x1
                    self.lineas.append({"tipo": "linea", "m": m, "b": b,
                                        "color": color,
                                        "pts": [(x1,y1),(x2,y2)]})
                    label = f"y = {m:+.3g}x {'+' if b>=0 else '−'} {abs(b):.3g}"

            else:  # puntos sueltos
                px = float(self.ent_px.get())
                py = float(self.ent_py.get())
                self.lineas.append({"tipo": "punto", "x": px, "y": py, "color": color})
                label = f"({px}, {py})"

        except ValueError:
            messagebox.showerror("Error", "Verifica que los valores sean numéricos.")
            return

        self._update_list(label, color)
        self._redraw()

    def _calcular_mb(self, m, b):
        angulo = math.degrees(math.atan(m))
        txt = (
            f"Pendiente:        m = {m:.6g}\n"
            f"Intersección Y:   b = {b:.6g}\n"
            f"Intersección X:   x = {(-b/m):.6g}\n" if m != 0 else
            f"Pendiente:        m = {m:.6g}\n"
            f"Intersección Y:   b = {b:.6g}\n"
            f"Intersección X:   ninguna (recta horizontal)\n"
        ) + f"Ángulo:           θ = {angulo:.4f}°\n"
        self._show_result(txt)

    def _calcular_2p(self, x1, y1, x2, y2):
        if x2 == x1:
            txt = (
                f"Recta vertical    x = {x1}\n"
                f"Pendiente:        indefinida\n"
                f"Intersección X:   x = {x1}\n"
                f"Intersección Y:   ninguna\n"
            )
        else:
            m = (y2 - y1) / (x2 - x1)
            b = y1 - m * x1
            angulo = math.degrees(math.atan(m))
            dist   = math.hypot(x2-x1, y2-y1)
            txt = (
                f"Punto 1:          ({x1}, {y1})\n"
                f"Punto 2:          ({x2}, {y2})\n"
                f"Pendiente:        m = {m:.6g}\n"
                f"Intersección Y:   b = {b:.6g}\n"
                f"Intersección X:   x = {(-b/m):.6g}\n" if m != 0 else
                f"Punto 1:          ({x1}, {y1})\n"
                f"Punto 2:          ({x2}, {y2})\n"
                f"Pendiente:        m = {m:.6g}\n"
                f"Intersección Y:   b = {b:.6g}\n"
                f"Intersección X:   ninguna\n"
            )
            txt += (
                f"Ángulo:           θ = {angulo:.4f}°\n"
                f"Distancia:        d = {dist:.6g}\n"
            )
        self._show_result(txt)

    def _show_result(self, txt):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", txt)
        self.result_text.configure(state="disabled")

    def _preview(self):
        """Actualiza resultado en tiempo real mientras se tipea."""
        try:
            m = self.modo.get()
            if m == "pendiente_punto":
                mv = float(self.ent_m.get())
                bv = float(self.ent_b.get())
                self._calcular_mb(mv, bv)
            elif m == "dos_puntos":
                x1 = float(self.ent_x1.get()); y1 = float(self.ent_y1.get())
                x2 = float(self.ent_x2.get()); y2 = float(self.ent_y2.get())
                self._calcular_2p(x1, y1, x2, y2)
        except Exception:
            pass

    def _update_list(self, label, color):
        idx = len(self.lineas) - 1
        row = tk.Frame(self.list_frame, bg=PANEL_BG)
        row.pack(fill=tk.X, pady=1)

        dot = tk.Canvas(row, width=10, height=10, bg=PANEL_BG,
                        highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=color, outline="")
        dot.pack(side=tk.LEFT)

        tk.Label(row, text=label, bg=PANEL_BG, fg=TEXT,
                 font=("Consolas", 8)).pack(side=tk.LEFT, padx=4)

        def remove(i=idx, r=row):
            self.lineas[i] = None
            r.destroy()
            self._redraw()

        tk.Button(row, text="✕", command=remove, bg=PANEL_BG, fg=ACCENT2,
                  font=("Consolas", 8), relief="flat", padx=2,
                  cursor="hand2").pack(side=tk.RIGHT)

    def _limpiar(self):
        self.lineas = []
        for w in self.list_frame.winfo_children():
            w.destroy()
        self._show_result("")
        self._redraw()

    def _centrar(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self._redraw()

    def _zoom_in(self):
        self.zoom = min(self.zoom * 1.25, 400.0)
        self.zoom_var.set(f"1 unidad = {self.zoom:.1f} px  (1:1)")
        self._redraw()

    def _zoom_out(self):
        self.zoom = max(self.zoom / 1.25, 8.0)
        self.zoom_var.set(f"1 unidad = {self.zoom:.1f} px  (1:1)")
        self._redraw()

    # ── Dibujado del plano ───────────────────────────────────────────────────
    def _redraw(self):
        c = self.canvas
        c.delete("all")

        W, H = self._canvas_w, self._canvas_h
        if W < 2 or H < 2:
            return

        # Rango visible en unidades
        x_min = self._px_to_unit_x(0)
        x_max = self._px_to_unit_x(W)
        y_min = self._px_to_unit_y(H)
        y_max = self._px_to_unit_y(0)

        # Paso de grilla adaptativo (mismo para X y Y → 1:1)
        step = self._grid_step()

        # Fondo
        c.create_rectangle(0, 0, W, H, fill=BG, outline="")

        # ── Grilla secundaria (paso/5) ──
        sub = step / 5
        if sub * self.zoom >= 6:   # solo si son visibles
            self._draw_grid(c, x_min, x_max, y_min, y_max, sub,
                            GRID_SUB, width=1)

        # ── Grilla principal ──
        self._draw_grid(c, x_min, x_max, y_min, y_max, step,
                        GRID_MAIN, width=1)

        # ── Ejes ──
        ox = self._unit_to_px_x(0)
        oy = self._unit_to_px_y(0)

        c.create_line(0, oy, W, oy, fill=AXIS_COLOR, width=1)
        c.create_line(ox, 0, ox, H, fill=AXIS_COLOR, width=1)

        # ── Etiquetas numéricas ──
        self._draw_labels(c, x_min, x_max, y_min, y_max, step)

        # ── Líneas / puntos del usuario ──
        for lin in self.lineas:
            if lin is None:
                continue
            t = lin["tipo"]
            col = lin["color"]

            if t == "linea":
                self._draw_line(c, lin["m"], lin["b"], col,
                                x_min, x_max, y_min, y_max)
                # Destacar puntos capturados si vienen de 2 puntos
                if "pts" in lin:
                    for (px, py) in lin["pts"]:
                        self._draw_point(c, px, py, col)

            elif t == "vertical":
                px = self._unit_to_px_x(lin["x"])
                c.create_line(px, 0, px, H, fill=col, width=2)

            elif t == "punto":
                self._draw_point(c, lin["x"], lin["y"], col)

        # ── Etiquetas de origen ──
        if 0 <= ox <= W and 0 <= oy <= H:
            c.create_text(ox + 6, oy + 10, text="0", fill=ZERO_COLOR,
                          font=("Consolas", 8), anchor="nw")

    def _grid_step(self):
        """Calcula el paso de grilla para que haya entre 5 y 12 líneas visibles."""
        px_per_unit = self.zoom
        raw = 60 / px_per_unit          # queremos ~60 px entre líneas
        magnitude = 10 ** math.floor(math.log10(raw))
        for mult in (1, 2, 5, 10):
            candidate = magnitude * mult
            if candidate >= raw:
                return candidate
        return magnitude * 10

    def _draw_grid(self, c, x_min, x_max, y_min, y_max, step, color, width):
        # Líneas verticales
        ix = math.ceil(x_min / step) * step
        while ix <= x_max + step:
            px = self._unit_to_px_x(ix)
            c.create_line(px, 0, px, self._canvas_h, fill=color, width=width)
            ix += step
        # Líneas horizontales
        iy = math.ceil(y_min / step) * step
        while iy <= y_max + step:
            py = self._unit_to_px_y(iy)
            c.create_line(0, py, self._canvas_w, py, fill=color, width=width)
            iy += step

    def _draw_labels(self, c, x_min, x_max, y_min, y_max, step):
        ox = self._unit_to_px_x(0)
        oy = self._unit_to_px_y(0)

        # Formato inteligente
        def fmt(v):
            if abs(v) < 1e-9:
                return "0"
            if step >= 1 and abs(v) < 1e6:
                return str(int(round(v)))
            return f"{v:.2g}"

        # Etiquetas eje X
        ix = math.ceil(x_min / step) * step
        while ix <= x_max + step:
            if abs(ix) > 1e-9:
                px = self._unit_to_px_x(ix)
                # Posición Y del label (anclada al eje o al borde)
                ly = min(max(oy + 4, 4), self._canvas_h - 14)
                c.create_text(px, ly, text=fmt(ix), fill=TEXT_DIM,
                              font=("Consolas", 7), anchor="n")
            ix += step

        # Etiquetas eje Y
        iy = math.ceil(y_min / step) * step
        while iy <= y_max + step:
            if abs(iy) > 1e-9:
                py = self._unit_to_px_y(iy)
                lx = min(max(ox + 4, 4), self._canvas_w - 30)
                c.create_text(lx, py, text=fmt(iy), fill=TEXT_DIM,
                              font=("Consolas", 7), anchor="w")
            iy += step

    def _draw_line(self, c, m, b, color, x_min, x_max, y_min, y_max):
        """Dibuja y = mx + b recortada al viewport."""
        pts = []
        # Intersección con bordes del viewport
        for x in (x_min, x_max):
            y = m * x + b
            if y_min <= y <= y_max:
                pts.append((x, y))
        for y in (y_min, y_max):
            if m != 0:
                x = (y - b) / m
                if x_min <= x <= x_max:
                    pts.append((x, y))
        if len(pts) < 2:
            return
        pts.sort()
        p1, p2 = pts[0], pts[-1]
        x1 = self._unit_to_px_x(p1[0]); y1 = self._unit_to_px_y(p1[1])
        x2 = self._unit_to_px_x(p2[0]); y2 = self._unit_to_px_y(p2[1])
        c.create_line(x1, y1, x2, y2, fill=color, width=2, smooth=False)

        # Intersección con eje Y (punto b)
        if y_min <= b <= y_max:
            bx = self._unit_to_px_x(0)
            by = self._unit_to_px_y(b)
            c.create_oval(bx-4, by-4, bx+4, by+4, fill=color, outline=BG, width=1)
            c.create_text(bx+8, by, text=f"b={b:.3g}", fill=color,
                          font=("Consolas", 8), anchor="w")

        # Intersección con eje X (raíz)
        if m != 0:
            xi = -b / m
            if x_min <= xi <= x_max:
                xp = self._unit_to_px_x(xi)
                yp = self._unit_to_px_y(0)
                c.create_oval(xp-4, yp-4, xp+4, yp+4, fill=color,
                              outline=BG, width=1)
                c.create_text(xp, yp-10, text=f"x={xi:.3g}", fill=color,
                              font=("Consolas", 8), anchor="s")

    def _draw_point(self, c, ux, uy, color):
        px = self._unit_to_px_x(ux)
        py = self._unit_to_px_y(uy)
        r = 5
        c.create_oval(px-r, py-r, px+r, py+r, fill=color, outline=BG, width=2)
        c.create_text(px+9, py-9, text=f"({ux:.3g},{uy:.3g})", fill=color,
                      font=("Consolas", 8))


# ── Punto de entrada ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = PlanoCartesiano()
    app.geometry("1100x680")
    app.mainloop()