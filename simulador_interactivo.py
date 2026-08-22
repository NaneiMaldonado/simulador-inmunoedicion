#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulador interactivo en tiempo real del modelo de inmunoedición
con CO2, ciclo hormonal y Hamiltoniano de Ising.
Permite modificar parámetros en tiempo real con sliders.
La gráfica se actualiza cada 3 segundos (ventana deslizante de 200 pasos).

MODIFICACIONES PARA ATENDER OBSERVACIONES DEL PROFESOR:
1. Condiciones iniciales variables: ahora pueden ser aleatorias dentro de rangos biológicos,
   con opción para el usuario de activar/desactivar esta aleatoriedad (checkbox).
2. Todas las probabilidades están acotadas en [0,1] mediante clamp.
3. El sistema es dinámico: cada paso actualiza poblaciones y probabilidades.
4. El Hamiltoniano refleja el estado actual del sistema.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import tkinter as tk
from tkinter import ttk
import threading
import time
from collections import deque

# ================================
# PARÁMETROS GLOBALES (modificables en tiempo real)
# ================================
class Parametros:
    def __init__(self):
        self.CO2_factor = 0.20          # 0.20 (bajo) o 0.85 (alto)
        self.hormonal_factor = 0.10     # 0.10 (bajo) o 0.75 (alto)
        self.dna_repair_factor = 0.50   # 0.50 (normal) o 0.60 (baja reparación)
        self.growth_rate = 0.08         # Tasa de crecimiento de CC
        self.sim_running = True
        self.random_init = True         # Nueva opción: condiciones iniciales aleatorias

# ================================
# FUNCIONES DEL MODELO
# ================================
def rand_double(seed):
    """Genera número aleatorio uniforme [0,1]."""
    return (seed[0] * 1103515245 + 12345) / 2**31

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

def calcular_fase_hormonal(t, factor_hormonal):
    """Calcula la fase hormonal normalizada [0, factor_hormonal]."""
    return factor_hormonal * (0.5 + 0.5 * np.sin(2.0 * np.pi * t / 672.0))

def generar_condiciones_iniciales_aleatorias():
    """Genera condiciones iniciales aleatorias dentro de rangos biológicos."""
    # Rangos: CC (5-20), NK (2-10), M1 (2-10), N1 (1-6), CD8 (1-6), CD4 (1-5), Treg (0.5-2.5)
    CC = np.random.uniform(5.0, 20.0)
    NK = np.random.uniform(2.0, 10.0)
    M1 = np.random.uniform(2.0, 10.0)
    N1 = np.random.uniform(1.0, 6.0)
    CD8 = np.random.uniform(1.0, 6.0)
    CD4 = np.random.uniform(1.0, 5.0)
    Treg = np.random.uniform(0.5, 2.5)
    M2 = 0.0
    N2 = 0.0
    return CC, NK, M1, N1, CD8, CD4, Treg, M2, N2

# ================================
# ESTADO DE LA SIMULACIÓN
# ================================
class EstadoSimulacion:
    def __init__(self, random_init=True):
        if random_init:
            # Usar condiciones iniciales aleatorias
            (self.CC, self.NK, self.M1, self.N1, self.CD8, self.CD4,
             self.Treg, self.M2, self.N2) = generar_condiciones_iniciales_aleatorias()
        else:
            # Valores fijos (los originales)
            self.CC = 10.0
            self.NK = 5.0
            self.M1 = 5.0
            self.N1 = 3.0
            self.CD8 = 2.0
            self.CD4 = 2.0
            self.Treg = 1.0
            self.M2 = 0.0
            self.N2 = 0.0

        self.oxidative_stress = 0.10
        self.dna_damage = 0.10
        self.hsp_activity = 0.10
        self.delta_CC = 0.0
        self.step = 0
        self.H_TME = 0.0

    def reset(self, random_init=True):
        """Reinicia el estado con opción de aleatoriedad."""
        self.__init__(random_init)

# ================================
# FUNCIÓN DE SIMULACIÓN (un paso)
# ================================
def simular_paso(estado, params, seed):
    """Ejecuta un paso de simulación y actualiza el estado."""
    t = estado.step
    co2_factor = params.CO2_factor
    hormonal_factor = params.hormonal_factor
    dna_repair_factor = params.dna_repair_factor
    growth_rate = params.growth_rate

    # 1. CO2 y fase hormonal
    co2_actual = 0.5 + 0.15 * np.random.randn()
    co2_actual = clamp(co2_actual, 0.0, 1.0)
    co2_efectivo = co2_actual * co2_factor
    hormonal_phase = calcular_fase_hormonal(t, hormonal_factor)

    # 2. Estrés oxidativo
    estado.oxidative_stress = clamp(0.10 + 0.40 * co2_efectivo + 0.15 * hormonal_phase, 0.0, 1.0)

    # 3. HSP
    estado.hsp_activity = clamp(0.10 + 0.30 * estado.oxidative_stress + 0.20 * hormonal_phase, 0.0, 1.0)

    # 4. Capacidad de reparación del ADN
    dna_repair_cap = clamp(dna_repair_factor - 0.40 * hormonal_phase, 0.05, 0.95)

    # 5. Daño al ADN (probabilidad en [0,1] asegurada)
    prob_dano = clamp(0.05 + 0.30 * estado.oxidative_stress + 0.20 * hormonal_phase
                      - 0.30 * dna_repair_cap + 0.10 * (estado.M2 / (estado.M1 + estado.M2 + 1.0)),
                      0.01, 0.95)
    if rand_double(seed) < prob_dano:
        estado.dna_damage += 0.05
    if rand_double(seed) < dna_repair_cap:
        estado.dna_damage -= 0.03
    estado.dna_damage = clamp(estado.dna_damage, 0.0, 1.0)

    # 6. Crecimiento de CC (Gompertz)
    if estado.CC > 0.1:
        crecimiento = growth_rate * (1.0 - np.log(estado.CC) / np.log(500.0))
        crecimiento = clamp(crecimiento, -0.5, 0.5)
        estado.CC *= np.exp(crecimiento)
    else:
        estado.CC = 0.1

    # 7. Ataque de NK (probabilidad en [0,1] asegurada)
    prob_nk = clamp(0.15 * (estado.NK / (estado.NK + 5.0)), 0.0, 0.15)
    if rand_double(seed) < prob_nk:
        muertes = 0.5 + 1.5 * rand_double(seed)
        muertes = min(muertes, estado.CC)
        estado.CC -= muertes
        estado.delta_CC += muertes

    # 8. Ataque de CD8+ (probabilidad en [0,1] asegurada)
    prob_cd8 = clamp(0.20 * (estado.CD8 / (estado.CD8 + 5.0)), 0.0, 0.20)
    if rand_double(seed) < prob_cd8:
        muertes = 0.5 + 2.0 * rand_double(seed)
        muertes = min(muertes, estado.CC)
        estado.CC -= muertes
        estado.delta_CC += muertes

    estado.CC = max(estado.CC, 0.0)

    # 9. Reclutamiento de CD8+ (Michaelis-Menten)
    Rmax = np.log10(25.0)
    tau = 1.0
    r_cd8 = (estado.delta_CC * Rmax) / (tau + estado.delta_CC)
    r_cd8 = min(r_cd8, 2.0)
    estado.CD8 += r_cd8
    estado.CD8 *= 0.98

    # 10. Reclutamiento de otras células
    estado.NK += 0.5 * (1.0 + 0.2 * estado.oxidative_stress)
    estado.NK *= 0.97

    estado.M1 += 0.3 * (1.0 - 0.3 * hormonal_phase)
    estado.M1 *= 0.98

    estado.N1 += 0.2 * (1.0 - 0.2 * hormonal_phase)
    estado.N1 *= 0.97

    estado.CD4 += 0.3 * (1.0 + 0.1 * estado.oxidative_stress)
    estado.CD4 *= 0.98

    treg_rec = 0.1 + 0.30 * hormonal_phase
    estado.Treg += treg_rec
    estado.Treg *= 0.97

    # 11. Polarización M1→M2 y N1→N2 (promovida por progesterona)
    prob_m1_m2 = clamp(0.03 + 0.07 * hormonal_phase, 0.0, 0.10)
    if estado.M1 > 0.1 and rand_double(seed) < prob_m1_m2:
        conversion = min(0.3 + 0.7 * rand_double(seed), estado.M1)
        estado.M1 -= conversion
        estado.M2 += conversion

    prob_n1_n2 = clamp(0.03 + 0.06 * hormonal_phase, 0.0, 0.09)
    if estado.N1 > 0.1 and rand_double(seed) < prob_n1_n2:
        conversion = min(0.3 + 0.7 * rand_double(seed), estado.N1)
        estado.N1 -= conversion
        estado.N2 += conversion

    estado.M2 *= 0.98
    estado.N2 *= 0.97

    # 12. Agotamiento de CD8+ por Tregs (probabilidad en [0,1] asegurada)
    if estado.Treg > 5.0:
        agotamiento = clamp(0.02 * (estado.Treg / (estado.Treg + 5.0)), 0.0, 0.02)
        estado.CD8 *= (1.0 - agotamiento)

    # 13. Hamiltoniano (dinámico)
    NA = estado.NK + estado.M1 + estado.N1 + estado.CD8 + estado.CD4
    NP = estado.CC + estado.M2 + estado.N2 + estado.Treg
    if NA < 0.1 and NP < 0.1:
        NA = 0.1
        NP = 0.1
    H_A = -0.5 * (NA / (NA + NP + 1.0))**2
    H_P = 0.5 * (NP / (NA + NP + 1.0))**2
    estado.H_TME = H_A + H_P

    # 14. Decaimiento de delta_CC
    estado.delta_CC = min(estado.delta_CC, 100.0) * 0.99

    estado.step += 1
    return estado


# ================================
# APLICACIÓN TKINTER CON GRÁFICA EN TIEMPO REAL
# ================================
class SimuladorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧬 Simulador de Inmunoedición - Tiempo Real")
        self.root.geometry("1050x720")

        # Parámetros globales
        self.params = Parametros()
        self.estado = EstadoSimulacion(random_init=self.params.random_init)

        # Datos para la gráfica (ventana deslizante)
        self.historial_H = deque(maxlen=200)
        self.historial_step = deque(maxlen=200)

        # Semilla
        self.seed = [42]

        # Variable para controlar si la simulación está activa
        self.sim_running = True

        # ---------- Panel de control (derecha) ----------
        panel = ttk.Frame(root, padding=10)
        panel.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(panel, text="⚙️ Controles", font=('Arial', 14, 'bold')).pack(pady=10)

        # Slider CO2
        ttk.Label(panel, text="CO₂ (factor)").pack(anchor=tk.W, pady=(10,0))
        self.slider_co2 = ttk.Scale(panel, from_=0.0, to=1.0, value=self.params.CO2_factor,
                                    orient=tk.HORIZONTAL, length=200)
        self.slider_co2.pack()
        self.label_co2 = ttk.Label(panel, text=f"{self.params.CO2_factor:.2f}")
        self.label_co2.pack()
        self.slider_co2.bind('<Motion>', self.actualizar_etiquetas)

        # Slider Hormonal
        ttk.Label(panel, text="Hormonal (factor)").pack(anchor=tk.W, pady=(10,0))
        self.slider_horm = ttk.Scale(panel, from_=0.0, to=1.0, value=self.params.hormonal_factor,
                                     orient=tk.HORIZONTAL, length=200)
        self.slider_horm.pack()
        self.label_horm = ttk.Label(panel, text=f"{self.params.hormonal_factor:.2f}")
        self.label_horm.pack()
        self.slider_horm.bind('<Motion>', self.actualizar_etiquetas)

        # Slider Reparación ADN
        ttk.Label(panel, text="Reparación ADN (factor)").pack(anchor=tk.W, pady=(10,0))
        self.slider_repair = ttk.Scale(panel, from_=0.1, to=0.9, value=self.params.dna_repair_factor,
                                       orient=tk.HORIZONTAL, length=200)
        self.slider_repair.pack()
        self.label_repair = ttk.Label(panel, text=f"{self.params.dna_repair_factor:.2f}")
        self.label_repair.pack()
        self.slider_repair.bind('<Motion>', self.actualizar_etiquetas)

        # Slider Tasa de crecimiento
        ttk.Label(panel, text="Tasa crecimiento CC").pack(anchor=tk.W, pady=(10,0))
        self.slider_growth = ttk.Scale(panel, from_=0.01, to=0.20, value=self.params.growth_rate,
                                       orient=tk.HORIZONTAL, length=200)
        self.slider_growth.pack()
        self.label_growth = ttk.Label(panel, text=f"{self.params.growth_rate:.3f}")
        self.label_growth.pack()
        self.slider_growth.bind('<Motion>', self.actualizar_etiquetas)

        # --- Checkbox para inicialización aleatoria ---
        self.var_random = tk.BooleanVar(value=self.params.random_init)
        chk_random = ttk.Checkbutton(panel, text="Inicializar aleatorio",
                                     variable=self.var_random,
                                     command=self.cambiar_modo_inicializacion)
        chk_random.pack(pady=10)

        # Botón Reiniciar
        ttk.Button(panel, text="🔄 Reiniciar simulación", command=self.reiniciar).pack(pady=5)

        # Botón Pausa/Continuar
        self.btn_pausa = ttk.Button(panel, text="⏸️ Pausa", command=self.toggle_pausa)
        self.btn_pausa.pack(pady=5)

        # Indicador de estado
        self.label_estado = ttk.Label(panel, text="▶️ Corriendo", font=('Arial', 12))
        self.label_estado.pack(pady=10)

        # H_TME actual
        self.label_H = ttk.Label(panel, text="H_TME: 0.000", font=('Arial', 12, 'bold'))
        self.label_H.pack(pady=10)

        # ---------- Figura de Matplotlib ----------
        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.ax.set_xlabel('Pasos')
        self.ax.set_ylabel('H_TME')
        self.ax.set_title('Hamiltoniano del TME (ventana deslizante)')
        self.ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='Umbral')
        self.ax.legend(loc='upper right')
        self.ax.grid(alpha=0.3)

        self.canvas = FigureCanvasTkAgg(self.fig, root)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # ---------- Iniciar animación ----------
        self.anim = FuncAnimation(self.fig, self.actualizar_grafica,
                                  interval=3000, cache_frame_data=False)
        self.canvas.draw()

        # Actualizar parámetros cada 0.5 segundos
        self.root.after(500, self.actualizar_parametros)

    # ================================
    # MÉTODOS DE CONTROL
    # ================================
    def actualizar_etiquetas(self, event=None):
        """Actualiza las etiquetas de los sliders."""
        self.label_co2.config(text=f"{self.slider_co2.get():.2f}")
        self.label_horm.config(text=f"{self.slider_horm.get():.2f}")
        self.label_repair.config(text=f"{self.slider_repair.get():.2f}")
        self.label_growth.config(text=f"{self.slider_growth.get():.3f}")

    def cambiar_modo_inicializacion(self):
        """Cambia el modo de inicialización y reinicia la simulación."""
        self.params.random_init = self.var_random.get()
        self.reiniciar()

    def actualizar_parametros(self):
        """Lee los valores de los sliders y actualiza los parámetros."""
        if self.sim_running:
            self.params.CO2_factor = self.slider_co2.get()
            self.params.hormonal_factor = self.slider_horm.get()
            self.params.dna_repair_factor = self.slider_repair.get()
            self.params.growth_rate = self.slider_growth.get()
        self.root.after(500, self.actualizar_parametros)

    def reiniciar(self):
        """Reinicia el estado de la simulación."""
        self.estado = EstadoSimulacion(random_init=self.params.random_init)
        self.historial_H.clear()
        self.historial_step.clear()
        self.seed = [42]
        self.label_H.config(text="H_TME: 0.000")
        print("🔄 Simulación reiniciada" + (" con condiciones iniciales aleatorias" if self.params.random_init else " con valores fijos"))

    def toggle_pausa(self):
        """Alterna entre pausa y reanudación."""
        self.sim_running = not self.sim_running
        if self.sim_running:
            self.btn_pausa.config(text="⏸️ Pausa")
            self.label_estado.config(text="▶️ Corriendo")
        else:
            self.btn_pausa.config(text="▶️ Continuar")
            self.label_estado.config(text="⏸️ Pausado")

    # ================================
    # ACTUALIZACIÓN DE LA GRÁFICA (cada 3 segundos)
    # ================================
    def actualizar_grafica(self, frame):
        """Ejecuta varios pasos de simulación y actualiza la gráfica."""
        if not self.sim_running:
            return

        # Ejecutar 30 pasos por llamada (para velocidad)
        for _ in range(30):
            self.estado = simular_paso(self.estado, self.params, self.seed)

        # Añadir al historial
        self.historial_H.append(self.estado.H_TME)
        self.historial_step.append(self.estado.step)

        # Actualizar la etiqueta H_TME
        self.label_H.config(text=f"H_TME: {self.estado.H_TME:.4f}")

        # Limpiar el gráfico
        self.ax.clear()
        self.ax.set_xlabel('Pasos')
        self.ax.set_ylabel('H_TME')
        self.ax.set_title(f'Hamiltoniano del TME (ventana deslizante) - Paso {self.estado.step}')
        self.ax.axhline(y=0, color='red', linestyle='--', alpha=0.7, label='Umbral')
        self.ax.grid(alpha=0.3)

        # Graficar los datos
        if len(self.historial_H) > 1:
            steps = list(self.historial_step)
            h_vals = list(self.historial_H)
            self.ax.plot(steps, h_vals, 'b-', linewidth=1.5, label='H_TME')
            self.ax.legend(loc='upper right')

        # Ajustar límites dinámicamente
        if self.historial_H:
            h_min = min(self.historial_H)
            h_max = max(self.historial_H)
            margin = (h_max - h_min) * 0.1 + 0.1
            self.ax.set_ylim(h_min - margin, h_max + margin)
            self.ax.set_xlim(max(0, self.estado.step - 250), self.estado.step + 10)

        # Dibujar
        self.canvas.draw()


# ================================
# MAIN
# ================================
if __name__ == "__main__":
    root = tk.Tk()
    app = SimuladorApp(root)
    root.mainloop()