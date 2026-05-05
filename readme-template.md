# Nombre del Proyecto

Breve descripción de lo que hace tu proyecto y por qué es útil.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

## Tabla de contenidos

- [Arquitectura del sistema](#arquitectura_del_sistema)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Configuración](#configuración)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Arquitectura del sistema

Workflow de agentes

## Requisitos

- Node.js >= 18.0
- npm >= 9.0

## Instalación

Clona el repositorio e instala las dependencias:

\```bash
git clone https://github.com/usuario/proyecto.git
cd proyecto
npm install
\```

## Uso

\```bash
npm start
\```

## Configuración

Crea un archivo `.env` basado en el ejemplo:

\```bash
cp .env.example .env
\```

| Variable | Descripción | Default |
|---|---|---|
| `PORT` | Puerto del servidor | `3000` |
| `DATABASE_URL` | URL de la base de datos | - |

## Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit (`git commit -m 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Distribuido bajo la licencia MIT. Ver `LICENSE` para más información.