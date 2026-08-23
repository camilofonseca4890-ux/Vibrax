import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, g, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "vibrax.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

# Usuario y contraseña para entrar al panel de pedidos.
# En producción (Render), estos se pueden sobreescribir con variables de entorno
# PANEL_USUARIO y PANEL_PASSWORD, para no dejar la contraseña fija en el código.
PANEL_USUARIO = os.environ.get("PANEL_USUARIO", "Vibrax_23")
PANEL_PASSWORD_HASH = generate_password_hash(os.environ.get("PANEL_PASSWORD", "230623"))

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB por archivo

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------- Base de datos ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            email TEXT,
            descripcion_diseno TEXT NOT NULL,
            imagen_referencia TEXT,
            talla TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            color_tela TEXT NOT NULL,
            tipo_estampado TEXT NOT NULL,
            fecha_entrega TEXT NOT NULL,
            comentarios TEXT,
            estado TEXT NOT NULL DEFAULT 'Nuevo',
            fecha_creacion TEXT NOT NULL
        )
        """
    )
    db.commit()
    db.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def fotos_en_carpeta(nombre_carpeta):
    """Lee automáticamente todas las fotos que haya en static/img/<nombre_carpeta>."""
    carpeta = os.path.join(BASE_DIR, "static", "img", nombre_carpeta)
    if not os.path.isdir(carpeta):
        return []
    archivos = [f for f in os.listdir(carpeta) if allowed_file(f)]
    archivos.sort()
    return archivos


def login_requerido(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if not session.get("autenticado"):
            return redirect(url_for("login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltorio


# ---------- Rutas públicas ----------

@app.route("/")
def index():
    return render_template("index.html", fotos=fotos_en_carpeta("clientes"))


@app.route("/catalogo")
def catalogo():
    return render_template("catalogo.html")


@app.route("/inspiraciones")
def inspiraciones():
    return render_template("inspiraciones.html", fotos=fotos_en_carpeta("inspiraciones"))


@app.route("/preguntas-frecuentes")
def preguntas_frecuentes():
    return render_template("preguntas_frecuentes.html")


@app.route("/pedido", methods=["GET", "POST"])
def pedido():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        descripcion_diseno = request.form.get("descripcion_diseno", "").strip()
        talla = request.form.get("talla", "").strip()
        cantidad = request.form.get("cantidad", "").strip()
        color_tela = request.form.get("color_tela", "").strip()
        tipo_estampado = request.form.get("tipo_estampado", "").strip()
        fecha_entrega = request.form.get("fecha_entrega", "").strip()
        comentarios = request.form.get("comentarios", "").strip()

        errores = []
        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not telefono:
            errores.append("El teléfono es obligatorio.")
        if not descripcion_diseno:
            errores.append("Describe el diseño que quieres.")
        if not talla:
            errores.append("Selecciona una talla.")
        if not cantidad.isdigit() or int(cantidad) < 1:
            errores.append("La cantidad debe ser un número mayor a 0.")
        if not color_tela:
            errores.append("Indica el color de tela.")
        if not tipo_estampado:
            errores.append("Selecciona el tipo de estampado.")
        if not fecha_entrega:
            errores.append("Indica la fecha de entrega deseada.")

        imagen_filename = None
        archivo = request.files.get("imagen_referencia")
        if archivo and archivo.filename:
            if allowed_file(archivo.filename):
                nombre_seguro = secure_filename(archivo.filename)
                marca_tiempo = datetime.now().strftime("%Y%m%d%H%M%S")
                imagen_filename = f"{marca_tiempo}_{nombre_seguro}"
                archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], imagen_filename))
            else:
                errores.append("La imagen debe ser PNG, JPG, JPEG, WEBP o GIF.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template(
                "pedido.html",
                form=request.form,
            )

        db = get_db()
        db.execute(
            """
            INSERT INTO pedidos (
                nombre, telefono, email, descripcion_diseno, imagen_referencia,
                talla, cantidad, color_tela, tipo_estampado, fecha_entrega,
                comentarios, estado, fecha_creacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nombre, telefono, email, descripcion_diseno, imagen_filename,
                talla, int(cantidad), color_tela, tipo_estampado, fecha_entrega,
                comentarios, "Nuevo", datetime.now().strftime("%Y-%m-%d %H:%M"),
            ),
        )
        db.commit()

        return redirect(url_for("confirmacion"))

    return render_template("pedido.html", form={})


@app.route("/confirmacion")
def confirmacion():
    return render_template("confirmacion.html")


# ---------- Manejo de errores ----------

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return render_template("404.html"), 404


# ---------- Panel de pedidos (uso interno) ----------

@app.route("/panel/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "")

        if usuario == PANEL_USUARIO and check_password_hash(PANEL_PASSWORD_HASH, contrasena):
            session["autenticado"] = True
            siguiente = request.args.get("siguiente") or url_for("panel")
            return redirect(siguiente)

        flash("Usuario o contraseña incorrectos.", "error")

    return render_template("login.html")


@app.route("/panel/logout")
def logout():
    session.pop("autenticado", None)
    return redirect(url_for("login"))


@app.route("/panel")
@login_requerido
def panel():
    db = get_db()
    pedidos = db.execute(
        "SELECT * FROM pedidos ORDER BY id DESC"
    ).fetchall()
    return render_template("panel.html", pedidos=pedidos)


@app.route("/panel/pedido/<int:pedido_id>/estado", methods=["POST"])
@login_requerido
def actualizar_estado(pedido_id):
    nuevo_estado = request.form.get("estado", "Nuevo")
    db = get_db()
    db.execute("UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id))
    db.commit()
    return redirect(url_for("panel"))


if __name__ == "__main__":
    init_db()
    puerto = int(os.environ.get("PORT", 5000))
    modo_debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(debug=modo_debug, host="0.0.0.0", port=puerto)
else:
    # Cuando gunicorn importa la app (en Render), igual hay que crear la tabla.
    init_db()
