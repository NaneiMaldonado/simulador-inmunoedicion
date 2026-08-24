# simulador-inmunoedicion
============================================================
   SIMULADOR DE INMUNOEDICIÓN – MODELO CON HAMILTONIANO
   Repositorio: https://github.com/NaneiMaldonado/simulador-inmunoedicion
============================================================

1. DESCRIPCIÓN DEL MODELO
--------------------------
Este simulador interactivo en tiempo real modela la interacción entre el sistema inmunitario y las células tumorales en el cáncer de mama, incorporando:

- Células tumorales (CC) con crecimiento tipo Gompertz.
- Células inmunes: NK, M1, N1, CD8+, CD4+, Treg, M2, N2.
- Factores externos: CO2 atmosférico (estrés oxidativo) y ciclo hormonal (estradiol/progesterona).
- Un Hamiltoniano de tipo Ising que resume el balance entre fuerzas antitumorales y protumorales, permitiendo identificar las fases de Eliminación, Equilibrio y Escape.

La interfaz gráfica (Tkinter) permite ajustar en tiempo real los parámetros clave (CO2, hormonal, reparación de ADN y tasa de crecimiento) mediante sliders, y la gráfica se actualiza cada 3 segundos mostrando la evolución del Hamiltoniano.

2. REQUISITOS
-------------
- Sistema operativo: Windows, macOS o Linux (con entorno gráfico).
- Python 3.6 o superior.
- Bibliotecas: numpy, matplotlib, tkinter (tkinter suele venir incluido con Python en Windows/Linux; en macOS puede necesitar instalación adicional).

3. EJECUCIÓN LOCAL (DESCARGA Y EJECUCIÓN EN TU COMPUTADORA)
------------------------------------------------------------
Paso 1: Clonar el repositorio
   Abre una terminal y ejecuta:
   git clone https://github.com/NaneiMaldonado/simulador-inmunoedicion.git
   cd simulador-inmunoedicion

Paso 2: Instalar dependencias (opcional pero recomendado)
   Si tienes pip, ejecuta:
   pip install numpy matplotlib
   (Si no tienes pip, instálalo primero o usa el gestor de paquetes de tu sistema)

Paso 3: Ejecutar el simulador
   En la terminal, escribe:
   python simulador_interactivo.py

Notas para macOS:
   Si aparece un error sobre tkinter, instala Python desde python.org (que incluye tkinter) o usa:
   brew install python-tk
   Luego vuelve a intentar.

Notas para Windows:
   Asegúrate de que Python esté en el PATH. Puedes ejecutar desde la línea de comandos o desde el PowerShell.

4. EJECUCIÓN EN LÍNEA (ONLINE)
-------------------------------
El simulador es una aplicación de escritorio con interfaz Tkinter, por lo que no se puede ejecutar directamente en un navegador web. Sin embargo, ofrecemos dos alternativas para probarlo sin instalar localmente:

Alternativa A: Usar Binder (entorno Jupyter con escritorio virtual)
   Haz clic en el siguiente enlace (o cópialo en tu navegador):
   https://mybinder.org/v2/gh/NaneiMaldonado/simulador-inmunoedicion/HEAD?urlpath=lab
   Una vez que se abra el entorno, abre una terminal y ejecuta:
   python simulador_interactivo.py
   (Ten en cuenta que Binder puede ser lento y el escritorio virtual es limitado)

Alternativa B: Google Colab + X11 forwarding (avanzado)
   No se recomienda para usuarios sin experiencia. Es mejor optar por la ejecución local o Binder.

5. JUSTIFICACIÓN DEL HAMILTONIANO
-----------------------------------------------------------------------------
El modelo utiliza un Hamiltoniano de Ising para caracterizar el estado del microambiente tumoral (TME). Aunque tradicionalmente el Hamiltoniano de Ising se usa para sistemas de espines (por ejemplo, átomos con momento magnético), aquí lo adaptamos a dos "clusters" o grupos celulares:

- Cluster A (fuerzas antitumorales): NK + M1 + N1 + CD8 + CD4.
- Cluster P (fuerzas protumorales): CC + M2 + N2 + Treg.

Cada cluster se comporta como un "espín" colectivo. La energía asociada a cada cluster se calcula como:

   Energía antitumoral (HA) = -0.5 * (NA / (NA + NP + 1))^2
   Energía protumoral (HP) = +0.5 * (NP / (NA + NP + 1))^2

El Hamiltoniano total del TME es la suma: HTME = HA + HP.

Interpretación:
- Si HTME < 0, domina la contribución antitumoral → Fase de Eliminación.
- Si HTME ≈ 0, hay equilibrio dinámico → Fase de Equilibrio.
- Si HTME > 0, dominan las fuerzas protumorales → Fase de Escape.

Los factores externos (CO2 y ciclo hormonal) actúan como un "campo magnético" que modifica las probabilidades de transición y, por tanto, las poblaciones celulares, afectando el balance NA/NP y, en consecuencia, el Hamiltoniano. De esta manera, el modelo es formalmente análogo a un sistema de Ising de dos espines acoplados con un campo externo.

6. ESTRUCTURA DEL CÓDIGO
------------------------
El archivo principal es simulador_interactivo.py y contiene:

- Clase Parametros: almacena los valores de CO2, hormonal, reparación de ADN y tasa de crecimiento.
- Funciones auxiliares: rand_double (generador aleatorio), clamp (acotar valores), calcular_fase_hormonal.
- Clase EstadoSimulacion: contiene las poblaciones celulares y variables de estado (estrés oxidativo, daño al ADN, actividad HSP, etc.).
- Función simular_paso: ejecuta un paso de simulación actualizando todas las variables según las reglas probabilísticas.
- Clase SimuladorApp: construye la interfaz gráfica con Tkinter, los sliders, el botón de pausa/reinicio y la figura de Matplotlib.
- Bucle principal: inicia la aplicación.

El código está comentado en español para facilitar su comprensión.

7. RESULTADOS ESPERADOS
-----------------------
Al ejecutar el simulador, verás una ventana con:

- Un panel de control a la derecha con cuatro sliders (CO2, Hormonal, Reparación ADN, Tasa de crecimiento).
- Botones para pausar/reanudar y reiniciar la simulación.
- Una gráfica a la izquierda que muestra la evolución del Hamiltoniano HTME en una ventana deslizante de 200 pasos.

Puedes modificar los parámetros en tiempo real y observar cómo cambia la dinámica del sistema (por ejemplo, si el Hamiltoniano cruza el umbral cero, indica un cambio de fase).

8. CONTACTO Y AGRADECIMIENTOS
-----------------------------
Autor: Nanei Mazatl Maldonado Fiesco
Profesor: Dr. Matías Alvarado-Mentado
Institución: CINVESTAV-IPN, Departamento de Computación

Agradecimientos especiales a todas las personas que contribuyeron con sugerencias y apoyo durante el desarrollo de este proyecto.

9. LICENCIA
-----------
Este proyecto es de uso académico. Si utilizas el código, por favor cita el repositorio.

============================================================
¡Gracias por tu interés! Cualquier duda, abre un issue en GitHub.
