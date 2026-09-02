const express = require("express");

const app = express();
const port = Number.parseInt(process.env.PORT || "8080", 10);

function studentValue() {
  const carnet = process.env.CARNET || "#Carnet";
  return `Isaac Mahanaim Loarca Bautista - ${carnet}`;
}

app.get("/check", (_request, response) => {
  response.status(200).send("OK");
});

app.get("/", (_request, response) => {
  response.json({
    Instancia: "Instancia #2 - API #2",
    Curso: "Seminario de Sistemas 1",
    Estudiante: studentValue(),
  });
});

app.listen(port, "0.0.0.0", () => {
  console.log(`API #2 escuchando en http://0.0.0.0:${port}`);
});
