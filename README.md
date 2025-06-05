# Anders Dashboard

Este proyecto incluye un dashboard administrativo con sistema de roles y gestión de analistas.

## Estructura del Proyecto

```
proyectotp1/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
└── src/
    └── Components/
        ├── Dashboard/
        └── LoginRegister/
```

## Configuración del Backend

1. Crear un entorno virtual e instalar dependencias:
```bash
python -m venv venv
.\venv\Scripts\activate  # En Windows
source venv/bin/activate  # En Unix/MacOS
pip install -r backend/requirements.txt
```

2. Configurar variables de entorno:
```bash
cd backend
cp .env.example .env
```
Editar el archivo `.env` con tus credenciales de correo.

3. Iniciar el servidor:
```bash
uvicorn main:app --reload
```

## Configuración del Frontend

1. Instalar dependencias:
```bash
npm install
```

2. Iniciar el servidor de desarrollo:
```bash
npm start
```

## Credenciales de Acceso

### Administrador
- Email: admin@anders.com
- Contraseña: contra123

### Usuario
- Email: user@anders.com
- Contraseña: contra456

## Funcionalidades

### Administrador
- Acceso a todas las secciones del dashboard
- Gestión de analistas en la sección de Configuración
- Puede agregar correos de analistas (solo dominio @anders.com)

### Usuario
- Acceso a Inicio, Clientes, Productos y Análisis
- Sin acceso a la sección de Configuración

### Registro de Nuevos Usuarios
1. El administrador debe agregar el correo del analista en la sección de Configuración
2. El analista puede registrarse usando el correo autorizado
3. Se enviará un correo de confirmación
4. Tras confirmar, el usuario puede iniciar sesión
