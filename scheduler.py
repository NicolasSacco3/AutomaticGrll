from collections import defaultdict
from datetime import date
import random

TODOS = [
    "Dario", "Abigail", "Elizabeth", "Nicolás", "Mery", "Juan",
    "Laura", "Guillermo", "Gadiel", "Fernando", "Mariano",
    "Mabel", "Liliana", "Marcela", "Rodrigo"
]

ROLES = {
    "domingo": [
        ("voz", 2),
        ("guitarra", 1),
        ("teclado", 1),
        ("bajo", 1),
        ("bateria", 1),
        ("sonido", 1),
        ("proyector", 1)
    ],
    "jueves": [
        ("voz", 1),
        ("guitarra", 1),
        ("teclado", 1),
        ("bateria", 1)
    ]
}

RESTRICCIONES = {
    "min": 3,
    "max": 4,
    "no_juntos": [("Juan", "Laura")],
    "no_multimedia": ["Mabel", "Liliana", "Elizabeth", "Dario", "Fernando", "Marcela"],
    "roles": {
        "sonido": ["Fernando", "Guillermo", "Mariano"],
        "bajo": ["Fernando", "Dario", "Rodrigo"],
        "voz": ["Liliana", "Mabel", "Mery", "Laura", "Guillermo", "Marcela", "Elizabeth"],
        "guitarra": ["Nicolás", "Guillermo", "Abigail"],
        "bateria": ["Juan", "Mariano"],
        "teclado": ["Elizabeth", "Mery", "Marcela"]
    }
}


def generar_dias(year, month):
    dias = []
    for d in range(1, 29):
        fecha = date(year, month, d)
        if fecha.weekday() == 6:
            dias.append({"fecha": fecha, "tipo": "domingo"})
        elif fecha.weekday() == 3:
            dias.append({"fecha": fecha, "tipo": "jueves"})
    return dias


def generar_grilla(year, month, faltas):
    dias = generar_dias(year, month)

    mejor_grilla = None
    mejor_score = -1

    for intento in range(200):  # 🔥 cantidad de intentos (podés subirlo a 500)

        grilla = {}
        conteo = defaultdict(int)
        domingos_mabel_lili = defaultdict(int)
        score = 0

        for dia in dias:
            fecha = dia["fecha"]
            tipo = dia["tipo"]

            grilla[fecha] = {}
            usados = set()

            orden_roles = ["bateria", "teclado", "bajo", "guitarra", "voz", "sonido", "proyector"]

            roles_ordenados = sorted(
                ROLES[tipo],
                key=lambda x: orden_roles.index(x[0]) if x[0] in orden_roles else 99
            )

            for rol, cantidad in roles_ordenados:
                asignados = []

                candidatos = TODOS.copy()
                random.shuffle(candidatos)

                for usuario in candidatos:

                    if len(asignados) >= cantidad:
                        break

                    # reglas
                    if usuario in usados and usuario != "Guillermo":
                        continue

                    if conteo[usuario] >= RESTRICCIONES["max"]:
                        continue

                    if fecha in faltas.get(usuario, []):
                        continue

                    if rol in RESTRICCIONES["roles"]:
                        if usuario not in RESTRICCIONES["roles"][rol]:
                            continue

                    if rol == "proyector" and usuario in RESTRICCIONES["no_multimedia"]:
                        continue

                    # ❌ Juan y Laura no pueden estar el mismo día
                    if usuario in ["Juan", "Laura"]:
                         if "Juan" in usados or "Laura" in usados:
                            continue

                    if usuario == "Marcela" and rol == "voz" and tipo == "domingo":
                        continue

                    if usuario in ["Mabel", "Liliana"] and tipo == "domingo":
                        if domingos_mabel_lili[usuario] >= 2:
                            continue

                    # asignar
                    asignados.append(usuario)
                    usados.add(usuario)
                    conteo[usuario] += 1

                    if usuario in ["Mabel", "Liliana"] and tipo == "domingo":
                        domingos_mabel_lili[usuario] += 1

                grilla[fecha][rol] = asignados

                # 🔥 SCORING
                if len(asignados) == cantidad:
                    score += 10   # rol completo
                else:
                    score -= (cantidad - len(asignados)) * 5  # penalización

        # 🔥 BONUS por distribución
        for u in TODOS:
            if 3 <= conteo[u] <= 4:
                score += 2
            else:
                score -= 2

        # guardar mejor
        if score > mejor_score:
            mejor_score = score
            mejor_grilla = grilla

    return mejor_grilla