from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

USUARIOS = [
    "Dario", "Abigail", "Elizabeth", "Nicolás", "Mery", "Juan",
    "Laura", "Guillermo", "Gadiel", "Fernando", "Mariano",
    "Mabel", "Liliana", "Marcela", "Rodrigo"
]

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    cargo_faltas = db.Column(db.Boolean, default=False)  # 👈 NUEVO

class Falta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha = db.Column(db.Date, nullable=False)
    
class Configuracion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(50), unique=True)
    valor = db.Column(db.String(50))