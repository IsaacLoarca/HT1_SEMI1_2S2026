"""API #1 para la instancia EC2 llamada Instancia-1."""

import os

from flask import Flask, jsonify


app = Flask(__name__)


def student_value() -> str:
    carnet = os.getenv("CARNET", "#Carnet")
    return f"Estudiante - {carnet}"


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
