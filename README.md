# ClarityDesk Pro

Gestor de archivos moderno con interfaz profesional desarrollado con PySide6 (Qt). Sistema de tabs (Focus) para organización eficiente de archivos y carpetas.

## 🚀 Características

- **Sistema de Tabs (Focus)**: Organiza tus archivos en tabs para un acceso rápido
- **Vista de Escritorio**: Interfaz moderna con diseño glass-morphism
- **Vista de Cuadrícula y Lista**: Múltiples formas de visualizar tus archivos
- **Preview Rápido**: Vista previa de PDFs, imágenes y documentos
- **Gestión de Estados**: Sistema de seguimiento de estado de archivos
- **Drag & Drop**: Arrastra y suelta archivos entre carpetas
- **Renombrado Masivo**: Renombra múltiples archivos a la vez
- **Papelera Integrada**: Sistema de papelera con límites configurables
- **Monitoreo en Tiempo Real**: Sincronización automática de cambios en el sistema de archivos

## 📋 Requisitos

- Python 3.10 o superior
- Windows 10/11
- Poppler (para renderizado de PDFs)

### Instalación de Poppler

Poppler es necesario para la visualización de PDFs. Puedes descargarlo desde:
- [Poppler para Windows](https://github.com/oschwartz10612/poppler-windows/releases/)

Extrae los binarios y colócalos en `assets/poppler/bin/` o añade la ruta al PATH del sistema.

## 🔧 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/Pirrikos/ClarityDesk---Gestor-de-archivos-con-interfaz-moderna.git
cd ClarityDesk---Gestor-de-archivos-con-interfaz-moderna
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la aplicación:
```bash
python main.py
```

O usa el script batch:
```bash
run.bat
```

## 📁 Estructura del Proyecto

```
ClarityDesk_29-11-25/
├── main.py                 # Punto de entrada principal
├── app/                    # Paquete principal
│   ├── managers/          # Gestores de alto nivel
│   │   ├── tab_manager.py
│   │   ├── focus_manager.py
│   │   └── file_state_manager.py
│   ├── services/          # Servicios de lógica de negocio
│   │   ├── tab_*.py      # Gestión de tabs
│   │   ├── file_*.py     # Operaciones de archivos
│   │   ├── icon_*.py     # Renderizado de iconos
│   │   └── preview_*.py  # Vista previa de archivos
│   ├── models/           # Modelos de datos
│   └── ui/               # Componentes de interfaz
│       ├── widgets/     # Widgets personalizados
│       └── windows/     # Ventanas principales
├── assets/               # Recursos (iconos, binarios)
├── storage/             # Datos de la aplicación (no versionado)
├── tests/               # Tests unitarios
└── requirements.txt     # Dependencias Python
```

## 🎯 Uso

### Ventana de Escritorio
La aplicación inicia automáticamente con la ventana de escritorio (DesktopWindow), que proporciona acceso rápido a tus archivos.

### Ventana Principal
Abre la ventana principal desde la ventana de escritorio para acceder a:
- Sistema de tabs (Focus)
- Vista de archivos en cuadrícula o lista
- Árbol de carpetas
- Herramientas de gestión

### Operaciones Básicas
- **Navegar**: Usa el árbol de carpetas o los botones de navegación
- **Abrir archivo**: Doble clic en cualquier archivo
- **Seleccionar múltiples**: Ctrl + Click
- **Arrastrar archivos**: Drag & Drop entre carpetas
- **Renombrar masivo**: Selecciona múltiples archivos y usa la opción de renombrar

## 🛠️ Desarrollo

### Ejecutar Tests
```bash
python -m pytest tests/
```

### Compilar Ejecutable
```bash
pyinstaller main.spec
```

## 📦 Dependencias Principales

- **PySide6**: Framework Qt para Python
- **python-docx**: Procesamiento de documentos Word
- **pdf2image**: Conversión de PDFs a imágenes
- **Pillow**: Procesamiento de imágenes
- **pywin32**: Integración con Windows

Ver `requirements.txt` para la lista completa.

## 🤖 Reglas de interacción con la IA

- No mostrar código en pantalla salvo que el usuario lo solicite explícitamente.
- Mantener respuestas en español y cumplir los estándares de claridad y profesionalidad.

## 📝 Notas

- Los datos de la aplicación se almacenan en `storage/` (no versionado)
- La base de datos SQLite se crea automáticamente en `storage/claritydesk.db`
- Los tabs se guardan en `storage/tabs.json`
- La papelera se encuentra en `storage/trash/`

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver el archivo LICENSE para más detalles.

## 👤 Autor

**Pirrikos**

- GitHub: [@Pirrikos](https://github.com/Pirrikos)

## 🙏 Agradecimientos

- PySide6 por el framework Qt
- Comunidad de Python por las excelentes librerías

