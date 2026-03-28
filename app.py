import calendar
from datetime import date
from scheduler import generar_grilla
from collections import defaultdict
from flask import Flask, render_template, request, redirect, session
from models import db, Usuario, Falta, USUARIOS

app = Flask(__name__)
import os

db_url = os.environ.get('DATABASE_URL')

if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://")

app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///alabanza.db'
app.config['SECRET_KEY'] = 'secret'
db.init_app(app)  # ✅ AGREGAR

# 👉 Crear DB y usuarios
with app.app_context():
    db.create_all()
    for nombre in USUARIOS:
        if not Usuario.query.filter_by(nombre=nombre).first():
            db.session.add(Usuario(nombre=nombre))
    db.session.commit()


# ========================
# LOGIN
# ========================
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['usuario']
        user = Usuario.query.filter_by(nombre=nombre).first()

        if user:
            session['user_id'] = user.id
            return redirect('/dashboard')

    return render_template('login.html', usuarios=USUARIOS)


# ========================
# DASHBOARD
# ========================
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    user = db.session.get(Usuario, session['user_id'])

    # 👉 próximo mes
    hoy = date.today()
    year = hoy.year
    month = hoy.month + 1

    if month == 13:
        month = 1
        year += 1

    # 👉 generar jueves y domingos
    dias_validos = []
    cal = calendar.Calendar()

    for dia in cal.itermonthdates(year, month):
        if dia.month == month and dia.weekday() in [3, 6]:
            dias_validos.append(dia)

    # 👉 guardar faltas
    if request.method == 'POST':
        fechas = request.form.getlist('fechas')

        for f in fechas:
            fecha_obj = date.fromisoformat(f)

            falta = Falta(usuario_id=user.id, fecha=fecha_obj)
            db.session.add(falta)

        user.cargo_faltas = True
        db.session.commit()

    return render_template(
        'dashboard.html',
        user=user,
        dias=dias_validos,
        todos=todos_cargaron()
    )


# ========================
# LOGOUT
# ========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ========================
# GRILLA
# ========================
@app.route('/grilla')
def ver_grilla():
    if 'user_id' not in session:
        return redirect('/')

    user = db.session.get(Usuario, session['user_id'])

    # ❌ Si no todos cargaron
    if not todos_cargaron():
        return render_template('esperando.html')

    # ❌ Solo Nicolás puede verla
    if user.nombre != "Nicolás":
        return render_template('esperando.html')

    # 👉 faltas
    faltas = Falta.query.all()
    faltas_dict = defaultdict(list)

    for f in faltas:
        usuario = db.session.get(Usuario, f.usuario_id)
        faltas_dict[usuario.nombre].append(f.fecha)

    # 👉 próximo mes
    hoy = date.today()
    year = hoy.year
    month = hoy.month + 1

    if month == 13:
        month = 1
        year += 1

    # 👉 generar grilla
    grilla = generar_grilla(year, month, faltas_dict)

    # 👉 transformar
    fechas, tabla = transformar_grilla(grilla)
    observaciones = generar_observaciones(fechas, tabla)

    return render_template(
    'grilla.html',
    fechas=fechas,
    tabla=tabla,
    observaciones=observaciones
)

import pandas as pd
from flask import send_file
import io

@app.route('/reset_mes')
def reset_mes():
    limpiar_mes()
    return "Mes reiniciado"

@app.route('/exportar_excel')
def exportar_excel():
    if 'user_id' not in session:
        return redirect('/')

    faltas = Falta.query.all()
    faltas_dict = defaultdict(list)

    for f in faltas:
        usuario = Usuario.query.get(f.usuario_id)
        faltas_dict[usuario.nombre].append(f.fecha)

    hoy = date.today()
    year = hoy.year
    month = hoy.month + 1

    if month == 13:
        month = 1
        year += 1

    grilla = generar_grilla(year, month, faltas_dict)
    fechas, tabla = transformar_grilla(grilla)

    # 👉 armar DataFrame
    data = []
    for rol, valores in tabla.items():
        fila = [rol] + valores
        data.append(fila)

    columnas = ["Rol"] + [f.strftime("%d/%m") for f in fechas]

    df = pd.DataFrame(data, columns=columnas)

    # 👉 guardar en memoria
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        download_name="grilla.xlsx",
        as_attachment=True
    )

# ========================
# FUNCIONES AUXILIARES
# ========================
def transformar_grilla(grilla):
    roles_fijos = ["voz", "guitarra", "teclado", "bajo", "bateria", "sonido", "proyector"]

    fechas = sorted(grilla.keys())
    tabla = {rol: [] for rol in roles_fijos}

    for fecha in fechas:
        for rol in roles_fijos:
            personas = grilla.get(fecha, {}).get(rol, [])
            texto = ", ".join(personas)
            tabla[rol].append(texto)

    return fechas, tabla

def limpiar_mes():
    Falta.query.delete()
    for u in Usuario.query.all():
        u.cargo_faltas = False
    db.session.commit()


def todos_cargaron():
    total = Usuario.query.count()
    cargados = Usuario.query.filter_by(cargo_faltas=True).count()
    return total == cargados

def generar_observaciones(fechas, tabla):
    observaciones = []

    for i, fecha in enumerate(fechas):
        for rol, valores in tabla.items():
            if valores[i] == "":
                observaciones.append(f"{fecha} → falta cubrir: {rol}")

    return observaciones


# ========================
# RUN
# ========================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)