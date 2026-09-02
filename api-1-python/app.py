"""API #1 para la instancia EC2 llamada Instancia-1."""

import os

from flask import Flask, jsonify


app = Flask(__name__)
app.json.sort_keys = False


def student_value() -> str:
    nombre = os.getenv("ESTUDIANTE", "Isaac Mahanaim Loarca Bautista")
    carnet = os.getenv("CARNET", "20307546")
    return f"{nombre} - {carnet}"


@app.get("/check")
def check():
    """Health check del Application Load Balancer."""
    return "OK", 200


@app.get("/")
def root():
    return jsonify(
        {
            "Instancia": "Instancia #1 - API #1",
            "Curso": "Seminario de Sistemas 1",
            "Estudiante": student_value(),
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
