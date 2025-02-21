import streamlit as st
import pandas as pd
import plotly.express as px
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import streamlit_shadcn_ui as ui
from local_components import card_container

def create_pdf(fig, contribuyente, resumen, periodo):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    normal_style = styles['BodyText']

    # Título
    story.append(Paragraph(f"Análisis de Monotributo - {contribuyente}", title_style))
    story.append(Spacer(1, 12))

    # Período
    story.append(Paragraph(f"Período: {periodo}", normal_style))
    story.append(Spacer(1, 12))

    # Guardar la figura como imagen
    img_buffer = io.BytesIO()
    fig.write_image(img_buffer, format='png')
    img_buffer.seek(0)
    img = Image(img_buffer)
    img.drawHeight = 300
    img.drawWidth = 500
    story.append(img)

    # Resumen
    story.append(Spacer(1, 12))
    story.append(Paragraph("Resumen de Facturación", styles['Heading2']))
    for key, value in resumen.items():
        if isinstance(value, float):
            story.append(Paragraph(f"{key}: ${value:,.2f}", normal_style))
        else:
            story.append(Paragraph(f"{key}: {value}", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

def main():

    st.set_page_config(layout="wide", page_title="Análisis de Monotributo", page_icon=":bar_chart:")
    st.title('📊 Análisis de Monotributo')
    st.markdown("##")

    # Creamos las tres columnas
    st.subheader("Ingreso de datos: ")

    # Usamos st.columns para crear tres columnas
    col1, col2, col3 = st.columns(3)

    # 
    with col1:
        # Widget para ingresar el nombre del contribuyente
        contribuyente = st.text_input("Nombre del Contribuyente", "")

    # 
    with col2:
        # Widget para seleccionar la categoría actual
        categorias = {
            'A': 7813063.45, 'B': 11447046.44, 'C': 16050091.57, 'D': 19926340.10, 
            'E': 23439190.34, 'F': 29374695.90, 'G': 35128502.31, 'H': 53298417.30, 
            'I': 59657887.55, 'J': 68318880.36, 'K': 82370281.28
        }
        categoria_actual = st.selectbox("Selecciona tu categoría actual", options=list(categorias.keys()))

    # 
    with col3:

        # Widget para subir el archivo CSV
        uploaded_file = st.file_uploader("Sube tu archivo CSV", type="csv")



    if uploaded_file is not None and contribuyente:
        # Leer el archivo CSV
        df = pd.read_csv(uploaded_file, 
                         sep=';',
                         encoding='utf-8',
                         decimal=',',
                         thousands='.')

        # Seleccionamos solo las columnas requeridas
        columnas_requeridas = [
            'Fecha de Emisión', 
            'Punto de Venta',
            'Número Desde', 
            'Número Hasta', 
            'Nro. Doc. Receptor', 
            'Denominación Receptor', 
            'Imp. Total'
        ]
        df = df[columnas_requeridas]

        # Procesamiento de datos
        df['Fecha de Emisión'] = pd.to_datetime(df['Fecha de Emisión'], format='%Y-%m-%d')

        # Agrupamos por mes y sumamos el Imp. Total
        facturacion_mensual = df.groupby(df['Fecha de Emisión'].dt.to_period('M'))['Imp. Total'].sum().reset_index()
        facturacion_mensual['Fecha de Emisión'] = facturacion_mensual['Fecha de Emisión'].dt.to_timestamp()

        # Calculamos la facturación acumulada
        facturacion_mensual['Acumulado'] = facturacion_mensual['Imp. Total'].cumsum()

        # Obtenemos el límite de la categoría actual
        limite_categoria_actual = categorias[categoria_actual]

        # Función para calcular la variación mensual
        def calcular_variacion_mensual(facturacion_mensual):
            facturacion_mensual['Variación Mensual'] = facturacion_mensual['Imp. Total'].pct_change() * 100
            return facturacion_mensual
        
        # Calculamos los KPIs
        facturacion_total = facturacion_mensual['Imp. Total'].sum()
        facturacion_promedio_mensual = facturacion_mensual['Imp. Total'].mean()
        facturacion_mensual = calcular_variacion_mensual(facturacion_mensual)
        variacion_mensual = facturacion_mensual['Variación Mensual'].iloc[-1]  # Última variación mensual

        # Creamos las tarjetas en tres columnas
        st.subheader("KPIs de Facturación")

        # Usamos st.columns para crear tres columnas
        col1, col2, col3 = st.columns(3)

        # Tarjeta 1: Facturación Total
        with col1:
            ui.metric_card(
                title="Facturación Total",
                content=f"${facturacion_total:,.2f}",
                description="Total facturado en el período",
                key="card1"
            )

        # Tarjeta 2: Facturación Promedio Mensual
        with col2:
            ui.metric_card(
                title="Facturación Promedio Mensual",
                content=f"${facturacion_promedio_mensual:,.2f}",
                description="Promedio de facturación mensual",
                key="card2"
            )

        # Tarjeta 3: Variación Mensual de Facturación
        with col3:
            ui.metric_card(
                title="Variación Mensual",
                content=f"{variacion_mensual:.2f}%",
                description="Cambio porcentual respecto al mes anterior",
                key="card3"
            )

        # Creamos la barra horizontal para la facturación acumulada
        facturacion_acumulada = facturacion_mensual['Acumulado'].iloc[-1]
        exceso_facturacion = max(0, facturacion_acumulada - limite_categoria_actual)
        facturacion_disponible = max(0, limite_categoria_actual - facturacion_acumulada)

        # Ajustamos la altura de la barra
        bar_height = 0.3  # Puedes ajustar este valor para hacer la barra más plana

        fig_acumulado = px.bar(x=[facturacion_acumulada], 
                            y=['Facturación Acumulada'], 
                            orientation='h',
                            title=f'Facturación Acumulada vs Límite de Categoría {categoria_actual}',
                            labels={'x': 'Monto', 'y': ''},
                            text=[f"${facturacion_acumulada:,.2f}"],
                            height=300)  # Altura del gráfico

        # Ajustamos el ancho de la barra
        fig_acumulado.update_traces(marker=dict(line=dict(width=0)),  # Sin borde en la barra
                                    width=bar_height)  # Ajustamos la altura de la barra

        # Añadimos la línea vertical para el límite de categoría
        fig_acumulado.add_vline(x=limite_categoria_actual, line_dash="dash", line_color="red", 
                                annotation_text=f"Límite Categoría {categoria_actual}", 
                                annotation_position="top right")

        # Personalizamos el diseño del gráfico
        fig_acumulado.update_layout(
            showlegend=False,  # Ocultamos la leyenda
            xaxis=dict(title='Monto'),  # Título del eje X
            yaxis=dict(showticklabels=False),  # Ocultamos las etiquetas del eje Y
            plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
            margin=dict(l=20, r=20, t=40, b=20)  # Ajustamos los márgenes
        )

        # Mostramos el gráfico en Streamlit
        st.plotly_chart(fig_acumulado)

        # Verificamos si hay exceso de facturación
        if facturacion_acumulada > limite_categoria_actual:
            # Ordenamos las categorías por su límite de facturación
            categorias_ordenadas = sorted(categorias.items(), key=lambda x: x[1])
            
            # Encontramos la categoría más alta que no sea excedida por la facturación acumulada
            categoria_encuadre = None
            for cat, limite in categorias_ordenadas:
                if facturacion_acumulada <= limite:
                    categoria_encuadre = cat
                    break
            
            # Si no se encuentra una categoría válida, el contribuyente excede todas las categorías
            if categoria_encuadre:
                st.error(f"**Alerta! Exceso de facturación.** Con la facturación actual, queda encuadrado en la **Categoría {categoria_encuadre}**.")
            else:
                st.error("**Alerta! Exceso de facturación.** No hay una categoría superior disponible.")

        # Creamos el gráfico de facturación mensual con Plotly
        fig_mensual = px.bar(facturacion_mensual, x='Fecha de Emisión', y='Imp. Total', 
                             title=f'Facturación Mensual - {contribuyente}',
                             labels={'Imp. Total': 'Facturación Mensual', 'Fecha de Emisión': 'Fecha'})
        st.plotly_chart(fig_mensual)

        # Calculamos el período
        fecha_inicio = facturacion_mensual['Fecha de Emisión'].min().strftime('%Y-%m')
        fecha_fin = facturacion_mensual['Fecha de Emisión'].max().strftime('%Y-%m')
        periodo = f"{fecha_inicio} a {fecha_fin}"

        # Añadimos un resumen de la facturación
        st.subheader(f"Resumen de Facturación del período {periodo}")
        resumen = {
            "Facturación Total": facturacion_mensual['Imp. Total'].sum(),
            "Facturación Máxima Mensual": facturacion_mensual['Imp. Total'].max(),
            "Facturación Acumulada": facturacion_acumulada,
            "Límite de Categoría Actual": limite_categoria_actual,
            "Exceso de Facturación": exceso_facturacion,
            "Facturación Disponible": facturacion_disponible
        }
        for key, value in resumen.items():
            if isinstance(value, float):
                st.write(f"{key}: ${value:,.2f}")
            else:
                st.write(f"{key}: {value}")

        # Botón para exportar a PDF
        if st.button('Exportar a PDF'):
            pdf = create_pdf(fig_mensual, contribuyente, resumen, periodo)
            st.download_button(
                label="Descargar PDF",
                data=pdf,
                file_name=f"analisis_monotributo_{contribuyente}.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()