# Monotributo App 📊

Una aplicación web para analizar y controlar la facturación de monotributistas en Argentina.

## 🎯 Descripción

Monotributo App es una herramienta que permite a los monotributistas llevar un control preciso de su facturación mensual y acumulada. La aplicación analiza los datos de facturación extraídos de AFIP y proporciona un resumen detallado que incluye:

- Facturación total del período
- Facturación máxima mensual
- Estado actual de la categoría
- Límites de facturación
- Facturación disponible antes de cambio de categoría

## 🚀 Demo

Puedes probar la aplicación en vivo aquí: [Monotributo App](https://monotributo-app.streamlit.app/)

## 💡 Cómo Usar

1. Descarga tu archivo de facturación en formato CSV desde la página de AFIP, servicio Mis Comprobantes -> Emitidos
2. Ingresa a [Monotributo App](https://monotributo-app.streamlit.app/)
3. Sube el archivo CSV
4. Obtén instantáneamente un análisis detallado de tu situación fiscal

## 📊 Ejemplo de Resultado

```
Análisis de Monotributo
Período: 2024-01 a 2024-09

Resumen de Facturación
- Facturación Total: $10,394,634.49
- Facturación Máxima Mensual: $1,835,201.80
- Categoría Actual: B (límite: $9,450,000.00)
- Siguiente Categoría: C (límite: $13,250,000.00)
- Facturación Disponible: $2,855,365.51
```

## 🛠️ Tecnologías Utilizadas

- Python
- Streamlit
- Pandas
- NumPy

## 🔒 Privacidad

La aplicación procesa los datos localmente y no almacena ninguna información personal ni de facturación.

## 👥 Contribuciones

Las contribuciones son bienvenidas. Si encuentras un bug o tienes una sugerencia, no dudes en abrir un issue o enviar un pull request.

## 📝 Licencia

Este proyecto está bajo la Licencia MIT.
