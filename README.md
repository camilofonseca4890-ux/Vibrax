# Vibrax — Página web de pedidos de camisetas estampadas

## ¿Qué incluye?

- Inicio, Precios (con fichas técnicas), Inspiraciones y Preguntas Frecuentes.
- Formulario de pedido con imagen de referencia, talla, cantidad, color de tela,
  tipo de estampado, fecha de entrega y comentarios.
- Cada pedido se guarda en una base de datos SQLite (vibrax.db).
- Panel interno en /panel (protegido con usuario y contraseña) para ver los
  pedidos y cambiar su estado.
- Botón flotante de WhatsApp y vista previa bonita al compartir el link.
- Página de error 404 con el estilo de la marca.

## Cómo correrla en tu computador

1. Instala Flask:  pip install -r requirements.txt
2. Corre la app:   python app.py
3. Abre:           http://localhost:5000

## Usuario y contraseña del panel

Por defecto:
- Usuario: Vibrax_23
- Contraseña: 230623

Para cambiarlos sin tocar el código, usa variables de entorno:
PANEL_USUARIO y PANEL_PASSWORD (ver sección de Render más abajo).

## Cómo publicarla en internet (Render, gratis)

1. Sube este proyecto a un repositorio de GitHub (puede ser privado).
2. Crea una cuenta en render.com (puedes entrar con tu cuenta de GitHub).
3. Click en "New" → "Web Service" y selecciona tu repositorio.
4. Configura:
   - Build Command:  pip install -r requirements.txt
   - Start Command:  gunicorn app:app
5. En la sección "Environment", agrega estas variables (botón "Add Environment Variable"):
   - SECRET_KEY       → cualquier texto largo y aleatorio, solo tú lo sabes
   - PANEL_USUARIO    → el usuario que quieras para entrar al panel
   - PANEL_PASSWORD   → la contraseña que quieras para entrar al panel
6. Click en "Create Web Service". Render instala todo y en unos minutos
   te da una URL pública como https://vibrax.onrender.com

## Cosas a tener en cuenta en el plan gratuito de Render

- **La base de datos se borra en cada despliegue nuevo.** El almacenamiento
  del plan gratuito no es permanente. Sirve perfecto para probar y mostrar
  la página, pero si el negocio empieza a recibir pedidos reales de forma
  constante, conviene pasar a una base de datos como PostgreSQL (Render
  también la ofrece gratis) para no perder información. Podemos hacer ese
  cambio cuando llegue el momento.
- **La página "duerme" si nadie la visita por un rato** y tarda unos segundos
  en despertar cuando alguien entra de nuevo. Para un negocio pequeño está
  bien; si se vuelve molesto, hay planes pagos económicos (desde ~$7 USD/mes)
  que evitan esto.

## Estructura del proyecto

vibrax/
├── app.py                        → lógica del servidor (rutas, base de datos, login)
├── Procfile                      → le dice a Render cómo arrancar la app
├── requirements.txt              → paquetes de Python necesarios
├── vibrax.db                     → base de datos (se genera automáticamente)
├── static/
│   ├── css/style.css             → estilos de toda la página
│   ├── img/
│   │   ├── logo.png              → logo de Vibrax
│   │   ├── favicon.png           → ícono de la pestaña del navegador
│   │   ├── clientes/             → fotos de "Así lucen nuestras prendas" (inicio)
│   │   └── inspiraciones/        → fotos de la página Inspiraciones
│   └── uploads/                  → imágenes de referencia que suben los clientes
└── templates/
    ├── base.html                  → header, footer, meta-etiquetas
    ├── index.html                 → inicio
    ├── catalogo.html              → precios y fichas técnicas
    ├── inspiraciones.html         → estampados ya hechos
    ├── preguntas_frecuentes.html  → FAQ y medios de pago
    ├── pedido.html                → formulario de pedido
    ├── confirmacion.html          → tras enviar el pedido
    ├── login.html                 → inicio de sesión del panel
    ├── panel.html                 → panel interno de pedidos
    └── 404.html                   → página de error personalizada
