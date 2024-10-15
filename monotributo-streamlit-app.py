import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

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
    fig.savefig(img_buffer, format='png')
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
    st.title('Análisis de Monotributo')

    # Widget para subir el archivo CSV
    uploaded_file = st.file_uploader("Sube tu archivo CSV", type="csv")

    # Widget para ingresar el nombre del contribuyente
    contribuyente = st.text_input("Nombre del Contribuyente", "")

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

        # Definimos las categorías de monotributo
        categorias = {
            'A': 6450000, 'B': 9450000, 'C': 13250000, 'D': 16450000, 
            'E': 19350000, 'F': 24250000, 'G': 29000000, 'H': 44000000, 
            'I': 49250000, 'J': 56400000, 'K': 68000000
        }

        # Función para obtener las categorías relevantes
        def obtener_categorias_relevantes(facturacion_max):
            cat_relevantes = {}
            categorias_ordenadas = sorted(categorias.items(), key=lambda x: x[1])
            categoria_actual = next((cat for cat, valor in categorias_ordenadas if valor > facturacion_max), 'K')
            indice_actual = next(i for i, (cat, _) in enumerate(categorias_ordenadas) if cat == categoria_actual)
            
            # Incluimos todas las categorías por debajo de la actual
            for cat, valor in categorias_ordenadas[:indice_actual]:
                cat_relevantes[cat] = valor
            
            # Incluimos la categoría actual y la siguiente (si existe)
            for i in range(indice_actual, min(indice_actual + 2, len(categorias_ordenadas))):
                cat, valor = categorias_ordenadas[i]
                cat_relevantes[cat] = valor
            
            return cat_relevantes

        # Obtenemos la facturación máxima acumulada
        facturacion_max = facturacion_mensual['Acumulado'].max()

        # Obtenemos las categorías relevantes
        categorias_relevantes = obtener_categorias_relevantes(facturacion_max)

        # Creamos el gráfico
        fig, ax = plt.subplots(figsize=(14, 8))

        # Configuramos el ancho de las barras y la posición
        width = 10  # Ancho de cada barra en días
        x = facturacion_mensual['Fecha de Emisión']

        # Barras para facturación mensual
        ax.bar(x - pd.Timedelta(days=width/2), facturacion_mensual['Imp. Total'], 
               width=width, label='Facturación Mensual', color='skyblue')

        # Barras para facturación acumulada
        ax.bar(x + pd.Timedelta(days=width/2), facturacion_mensual['Acumulado'], 
               width=width, label='Facturación Acumulada', color='orange')

        # Añadimos las líneas horizontales para cada categoría relevante
        for categoria, valor in categorias_relevantes.items():
            ax.axhline(y=valor, color='red', linestyle='--', alpha=0.5)
            ax.text(ax.get_xlim()[1], valor, f' Cat. {categoria}: ${valor:,}', 
                    verticalalignment='bottom', horizontalalignment='right')

        # Configuración del gráfico
        ax.set_xlabel('Fecha')
        ax.set_ylabel('Importe')
        ax.set_title(f'Contribuyente: {contribuyente}')
        ax.legend()

        # Rotamos las etiquetas del eje x para mejor legibilidad
        plt.xticks(rotation=45)

        # Ajustamos el límite superior del eje y para dar espacio a todas las categorías relevantes
        ax.set_ylim(top=max(categorias_relevantes.values()) * 1.1)

        # Ajustamos el diseño
        plt.tight_layout()

        # Mostramos el gráfico en Streamlit
        st.pyplot(fig)

        # Calculamos el período
        fecha_inicio = facturacion_mensual['Fecha de Emisión'].min().strftime('%Y-%m')
        fecha_fin = facturacion_mensual['Fecha de Emisión'].max().strftime('%Y-%m')
        periodo = f"{fecha_inicio} a {fecha_fin}"

        # Calculamos la categoría actual y la siguiente
        categorias_ordenadas = sorted(categorias.items(), key=lambda x: x[1])
        categoria_actual = next((cat for cat, valor in categorias_ordenadas if valor > facturacion_max), 'K')
        indice_actual = next(i for i, (cat, _) in enumerate(categorias_ordenadas) if cat == categoria_actual)
        
        if indice_actual > 0:
            categoria_anterior = categorias_ordenadas[indice_actual - 1][0]
            categoria_actual_info = f"{categoria_anterior} (límite: ${categorias[categoria_anterior]:,.2f})"
        else:
            categoria_actual_info = f"{categoria_actual} (primera categoría)"

        if indice_actual < len(categorias_ordenadas) - 1:
            siguiente_categoria = categorias_ordenadas[indice_actual][0]
            siguiente_categoria_info = f"{siguiente_categoria} (límite: ${categorias[siguiente_categoria]:,.2f})"
            facturacion_disponible = categorias[siguiente_categoria] - facturacion_max
        else:
            siguiente_categoria_info = "No hay categoría superior"
            facturacion_disponible = 0

        # Añadimos un resumen de la facturación
        st.subheader(f"Resumen de Facturación del período {periodo}")
        resumen = {
            "Facturación Total": facturacion_mensual['Imp. Total'].sum(),
            "Facturación Máxima Mensual": facturacion_mensual['Imp. Total'].max(),
            "Facturación Acumulada": facturacion_max,
            "Categoría Actual": categoria_actual_info,
            "Siguiente Categoría": siguiente_categoria_info,
            "Facturación Disponible": facturacion_disponible
        }
        for key, value in resumen.items():
            if isinstance(value, float):
                st.write(f"{key}: ${value:,.2f}")
            else:
                st.write(f"{key}: {value}")

        # Botón para exportar a PDF
        if st.button('Exportar a PDF'):
            pdf = create_pdf(fig, contribuyente, resumen, periodo)
            st.download_button(
                label="Descargar PDF",
                data=pdf,
                file_name=f"analisis_monotributo_{contribuyente}.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()

# streamlit run monotributo-streamlit-app.py