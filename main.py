from nicegui import ui
from config import *
from state import state
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib
matplotlib.use('Agg')

crear_tablas()
vistas()

def aplicar_estilos():
    ui.colors(primary='#0284c7', secondary='#0f172a', accent='#f43f5e')

@ui.page('/')
def control():
    aplicar_estilos()
    ui.query('body').style('background-color: #f8fafc')

    with ui.column().classes('w-full items-center p-8'):
        # --- CARD PRINCIPAL ---
        with ui.card().classes('w-full max-w-2xl p-8 shadow-2xl rounded-2xl bg-white border-t-4 border-primary'):

            # --- HEADER ---
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.icon('edit_note', color='primary').classes('text-4xl')
                ui.label('Estación de Captura').classes('text-2xl font-bold text-slate-800')

            ui.label('Busque una esponja para registrar mediciones.').classes('text-slate-500 mb-6')

            # --- BUSCADOR ---
            with ui.row().classes('w-full items-center gap-2'):
                input_id = ui.input('ID de Esponja').props('outlined rounded dense standout').classes('grow')
                # Botón de búsqueda
                btn_buscar = ui.button(icon='search', on_click=lambda: buscar_esponja()).props('elevated round color=primary')

            # Contenedor que se limpia/llena dinámicamente
            dynamic_content = ui.column().classes('w-full mt-6 gap-6')

            def buscar_esponja():
                dynamic_content.clear()
                if not input_id.value:
                    ui.notify('Ingrese un ID', type='warning')
                    return

                # Consulta BD si esponja existe
                row = get_esponja(input_id.value)
                if row:
                    state.esponja_id = int(row[0])   # Si existe, guarda estado global
                    ui.notify(f'Esponja {state.esponja_id} seleccionada', color='primary', icon='sync')

                    # Render dinamico
                    with dynamic_content:
                        # 1. Grid Informativo
                        ui.label('📏 Especificaciones Nominales').classes('font-bold text-slate-700 -mb-2')
                        with ui.grid(columns=3).classes('w-full gap-4'):
                            # Zip une dos listas elemento por elemento ej: zip(['a','b'],[10,20]) = ('a',10), ('b',20)
                            for label, value in zip(['Largo', 'Ancho', 'Espesor'], row[1:]):  #row posicion 1 en adelante
                                # Card para cada dato
                                with ui.card().classes('p-4 bg-slate-50 shadow-none border border-slate-200 text-center'):
                                    ui.label(label).classes('text-xs uppercase text-slate-400')
                                    ui.label(str(value)).classes('text-xl font-bold text-slate-800')

                        ui.separator()
                        ui.label('📝 Nueva Medición').classes('font-bold text-slate-700 -mb-2')

                        # 2. Formulario de entrada
                        with ui.grid(columns=3).classes('w-full gap-4'):
                            m_largo = ui.number('Largo Real').props('dense outlined rounded')
                            m_ancho = ui.number('Ancho Real').props('dense outlined rounded')
                            m_espesor = ui.number('Espesor Real').props('dense outlined rounded')

                        def guardar():
                            print(f'Intentando guardar: L={m_largo.value}, A={m_ancho.value}, E={m_espesor.value}')

                            if m_largo.value is None or m_ancho.value is None or m_espesor.value is None:
                                ui.notify('Complete todos los campos', type='negative')
                                return

                            try:
                                # Forzamos a int para que coincida con esquema de DB
                                val_l = int(m_largo.value)
                                val_a = int(m_ancho.value)
                                val_e = int(m_espesor.value)

                                # Insertamos en la DB
                                insert_medicion(state.esponja_id, val_l, val_a, val_e)
                                ui.notify(f'¡Medición registrada para ID #{state.esponja_id}', color='positive', icon='done')

                                # --- LIMPIEZA TOTAL ---
                                input_id.set_value('')  # Limpia el campo de búsqueda superior
                                dynamic_content.clear()

                            except Exception as e:
                                ui.notify(f'Error al guardar: {e}', type='negative')

                        ui.button('Guardar medición', icon='save', on_click=guardar) \
                            .props('unelevated rounded') \
                            .classes('w-full h-12 text-lg mt-2 shadow-md')
                else:
                    ui.notify('ID no encontrado', type='negative')

            # Si el usuario le da Enter dentro del input, lanza evento
            input_id.on('keydown.enter', buscar_esponja)


@ui.page('/grafica')
def grafica_page():
    aplicar_estilos()
    ui.query('body').style('background-color: #0f172a')

    # Ultimo estado de los datos dibujados en la grafica
    storage = {'last_hash': None}

    with ui.column().classes('w-full p-6 items-center'):
        header_label = ui.label('Esperando Conexión...').classes('text-white text-3xl font-light mb-6')
        grid_container = ui.column().classes('w-full items-center mb-6')    # Valores nominales
        chart_container = ui.column().classes('w-full items-center')        # Dibujo matplotlib

        # Actualiza la vista grafica y datos si hay cambios. Valida cambios mediante hash
        def update_view():
            # Obtiene ID global de la esponja seleccionada, este valor viene de ('/')
            current_id = state.esponja_id

            if not current_id:
                header_label.set_text('🔴 Sin Esponja Seleccionada')
                grid_container.clear()
                chart_container.clear()
                return

            # Consulta los datos de la bd
            limites = cargar_datos_esponja(current_id)           #limites = (largo, ancho, espesor)
            mediciones = cargar_mediciones_reales(current_id)    #mediciones = [(id, largo, ancho, espesor, fecha)]

            # Validar si no hay cambios para no re-renderizar innecesariamente
            current_hash = hash(str(mediciones) + str(current_id))   # Hash convierte estado completo en numero unico
            if current_hash == storage['last_hash']:
                return

            # Si hay cambios, significa nueva medición ó cambio de esponja. Actualiza gráfica
            storage['last_hash'] = current_hash    # Se guarda el nuevo estado como "last_hash"
            header_label.set_text(f'📊 Control Estadístico: Esponja #{current_id}')

            # --- GRID DE REFERENCIA ---
            grid_container.clear()
            if limites:
                with grid_container:
                    with ui.row().classes('gap-4'):
                        for label, value in zip(['Largo Nom.', 'Ancho Nom.', 'Espesor Nom.'], limites):
                            with ui.card().classes(
                                    'p-4 bg-slate-800 text-white border border-slate-700 min-w-[150px] text-center'):
                                ui.label(label).classes('text-xs uppercase text-slate-400')
                                ui.label(f'{value} mm').classes('text-2xl font-bold text-primary')

            # --- ACTUALIZAR GRÁFICA ---
            chart_container.clear()
            with chart_container:
                if not mediciones:
                    with ui.card().classes('w-full max-w-6xl p-10 bg-white items-center'):
                        ui.label('Sincronizado. Esperando datos de medición...').classes('text-slate-500 italic')
                else:
                    with ui.card().classes('w-full max-w-6xl p-4 bg-white rounded-xl shadow-lg'):
                        # Extrae el ID de cada medicion
                        ids_x = [str(m[0]) for m in mediciones]

                        # Extraer datos
                        m_largo = [m[1] for m in mediciones]
                        m_ancho = [m[2] for m in mediciones]
                        m_espesor = [m[3] for m in mediciones]
                        nom_largo, nom_ancho, nom_espesor = limites    # Desempaqueta limites nominales

                        # Usamos ui.pyplot con un contexto claro
                        with ui.pyplot(figsize=(10, 8)) as plot:
                            plt.clf()    # Limpieza de figura

                            # Crear subgraficas. 3 filas, 1 columna, sharex -> todos los graficos comparten el eje X
                            fig, axes = plt.subplots(3, 1, sharex=True, num=1)  # num=1 evita crear múltiples figuras en memoria
                            fig.set_size_inches(10, 8)    # tamaño de la figura
                            ax1, ax2, ax3 = axes   # Desempaqueta la lista -> axes=3 -> ax1 = axes[0], ax2 = axes[1], ax3 = axes[2]

                            # Lista de tuplas (ax grafico dibujado, dato medido, valor nominal, titulo, color linea)
                            configuracion = [
                                (ax1, m_largo, nom_largo, 'Largo', '#0284c7'),
                                (ax2, m_ancho, nom_ancho, 'Ancho', '#f59e0b'),
                                (ax3, m_espesor, nom_espesor, 'Espesor', '#f43f5e')
                            ]

                            # Bucle principal
                            for ax, datos, nominal, titulo, color in configuracion:

                                ax.plot(ids_x, datos, marker='o', color=color, linewidth=2, label='Medido',
                                        markersize=6)
                                ax.axhline(y=nominal, color='black', linestyle='--', alpha=0.7,
                                        label=f'Nominal ({nominal})')

                                # --- AJUSTE DE RANGO (ZOOM DINÁMICO) ---
                                # Definimos un margen de +/- 5 unidades (o el 10% del valor)
                                margen = max(5, nominal * 0.1)
                                ax.set_ylim(nominal - margen, nominal + margen)

                                # Sombreado de zona de tolerancia (ejemplo +/- 2)
                                ax.fill_between(ids_x, nominal - 2, nominal + 2, color=color, alpha=0.1)
                                #ax.set_xlim(left=0)

                                ax.set_ylabel('mm')
                                ax.set_title(f'Eje: {titulo}', loc='left', fontsize=10, fontweight='bold')
                                ax.legend(loc='upper right', fontsize='7')
                                ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))        # Fuerza a mostrar numeros enteros
                                ax.grid(True, linestyle=':', alpha=0.6)

                            plt.xlabel('ID de Medición (Historial)')
                            fig.tight_layout()

        # Cada segundo revisa si existen cambios
        ui.timer(1.0, update_view)

ui.run(title='Sponge QA System')