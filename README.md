# HT1 — Balanceador de carga con AWS EC2 y ELB

Implementación de la Hoja de Trabajo #1 de Seminario de Sistemas 1. Se despliegan dos APIs equivalentes en dos instancias EC2, usando lenguajes diferentes, y un Application Load Balancer (ALB) para distribuir las solicitudes.

## 1. Requisitos de la hoja de trabajo

El PDF solicita:

- Dos APIs web en lenguajes distintos.
- En ambas APIs:
  - `GET /check`: comprobación de estado y respuesta HTTP `200 OK`.
  - `GET /`: objeto JSON con la estructura indicada en el enunciado.
- Dos instancias EC2 llamadas exactamente `Instancia-1` e `Instancia-2`.
- API #1 en `Instancia-1` y API #2 en `Instancia-2`.
- Un balanceador llamado `elb-semi1-ht1-#carné`.
- Health check del balanceador y ambas instancias registradas como destinos.
- Video de máximo 10 minutos con pruebas directas, balanceadas y de tolerancia a fallos.

## 2. Estructura del proyecto

```text
.
├── api-1-python/
│   ├── app.py
│   ├── requirements.txt
│   └── systemd/api-1-python.service
└── api-2-node/
    ├── package.json
    ├── server.js
    └── systemd/api-2-node.service
```

La API #1 está implementada en Python/Flask y la API #2 en JavaScript/Node.js/Express. Las dos escuchan en el mismo puerto (`8080`) para que puedan pertenecer al mismo Target Group del ALB.

## 3. Ejecutar localmente

### API #1 — Python/Flask

```bash
cd api-1-python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export CARNET="123456789"
export PORT=8080
python3 app.py
```

Pruebas:

```bash
curl -i http://localhost:8080/check
curl http://localhost:8080/
```

### API #2 — Node.js/Express

```bash
cd api-2-node
npm install

export CARNET="123456789"
export PORT=8080
npm start
```

Pruebas:

```bash
curl -i http://localhost:8080/check
curl http://localhost:8080/
```

Para que el JSON final cumpla con la evidencia, sustituye `123456789` por tu carné real. Si no se define la variable, se utiliza el marcador `Estudiante - <#Carnet>`.

Respuestas esperadas en `/`:

```json
{
  "Instancia": "Instancia #1 - API #1",
  "Curso": "Seminario de Sistemas 1",
  "Estudiante": "Estudiante - <123456789>"
}
```

La API #2 devuelve el mismo formato cambiando `Instancia #1 - API #1` por `Instancia #2 - API #2`.

## 4. Configuración de AWS

### 4.1 Crear las instancias EC2

Usa la misma VPC y elige dos subredes públicas en distintas zonas de disponibilidad cuando estén disponibles.

Valores recomendados para la práctica:

| Configuración | Valor |
|---|---|
| AMI | Ubuntu Server LTS 64-bit |
| Tipo | `t2.micro` o `t3.micro`, según la capa gratuita disponible |
| Nombre exacto | `Instancia-1` y `Instancia-2` |
| Almacenamiento | 8 GiB gp3 es suficiente |
| Puerto de la API | TCP `8080` |
| API en Instancia-1 | `api-1-python` |
| API en Instancia-2 | `api-2-node` |

Asocia una IPv4 pública o Elastic IP a cada instancia. Anota ambas direcciones porque se mostrarán en el video. La IPv4 pública puede cambiar si la instancia se detiene; por eso debe anotarse nuevamente antes de grabar.

### 4.2 Grupo de seguridad de EC2

Crea un grupo, por ejemplo `sg-ht1-ec2`, con estas reglas de entrada:

| Tipo | Puerto | Origen | Motivo |
|---|---:|---|---|
| SSH | 22 | Solo tu IPv4 pública `/32` | Administración |
| Custom TCP | 8080 | Grupo de seguridad del ALB | Tráfico del balanceador |
| Custom TCP | 8080 | Solo tu IPv4 pública `/32` | Prueba directa exigida por la tarea |

Para una demostración rápida, puede usarse temporalmente `0.0.0.0/0` en el puerto 8080, pero es menos seguro. El acceso SSH no debe quedar abierto a todo Internet. El grupo de seguridad del ALB no se puede referenciar como origen hasta que exista; se agrega después de crearlo.

Reglas de salida: deja la salida predeterminada habilitada para permitir actualizaciones y respuestas HTTP.

### 4.3 Instalar dependencias y desplegar

Conéctate por SSH a cada instancia. Copia este repositorio con SFTP/Termius o clónalo desde un repositorio público. Los servicios incluidos están preparados para la carpeta fija `/home/ubuntu/HT1_SEMI1_2S2026`, que coincide con el nombre de este repositorio.

En `Instancia-1`:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git
git clone <URL_DEL_REPOSITORIO> /home/ubuntu/HT1_SEMI1_2S2026
cd /home/ubuntu/HT1_SEMI1_2S2026/api-1-python
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

En `Instancia-2`:

```bash
sudo apt update
sudo apt install -y nodejs npm git
git clone <URL_DEL_REPOSITORIO> /home/ubuntu/HT1_SEMI1_2S2026
cd /home/ubuntu/HT1_SEMI1_2S2026/api-2-node
npm install --omit=dev
```

Reemplaza el valor de `CARNET` por tu carné real. Se recomienda usar el archivo de servicio incluido para que cada API se inicie automáticamente y pueda detenerse de forma controlada durante la prueba de tolerancia a fallos.

> Si clonas el repositorio con otro nombre, cambia `/home/ubuntu/HT1_SEMI1_2S2026` por la ruta real en las dos instrucciones `WorkingDirectory` y `ExecStart` de los archivos `.service` antes de copiarlos a `/etc/systemd/system/`. La ruta debe contener directamente las carpetas `api-1-python` y `api-2-node`.

En `Instancia-1`:

```bash
sudo cp systemd/api-1-python.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now api-1-python
sudo systemctl status api-1-python --no-pager
```

En `Instancia-2`:

```bash
sudo cp systemd/api-2-node.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now api-2-node
sudo systemctl status api-2-node --no-pager
```

Antes de crear el ALB, prueba desde tu computadora:

```bash
curl -i http://<IP_PUBLICA_INSTANCIA_1>:8080/check
curl http://<IP_PUBLICA_INSTANCIA_1>:8080/
curl -i http://<IP_PUBLICA_INSTANCIA_2>:8080/check
curl http://<IP_PUBLICA_INSTANCIA_2>:8080/
```

Cada `/check` debe devolver `HTTP/1.1 200` y cada `/` debe devolver el identificador de su API.

### 4.4 Crear el Target Group

En EC2 → Load Balancers → Target Groups:

1. Tipo de destino: `Instances`.
2. Nombre sugerido: `tg-semi1-ht1-<carné>`.
3. Protocolo: `HTTP`.
4. Puerto: `8080`.
5. VPC: la misma de las instancias.
6. Health check protocol: `HTTP`.
7. Health check path: `/check`.
8. Health check port: `Traffic port`.
9. Healthy threshold: 2; unhealthy threshold: 2; timeout: 5 s; interval: 10 s.
10. Registra `Instancia-1` e `Instancia-2` en el puerto `8080`.

Espera a que ambos destinos aparezcan como `Healthy`. Si alguno queda `Unhealthy`, revisa que el servicio esté escuchando en `0.0.0.0:8080`, que `/check` responda 200 y que la regla del grupo de seguridad permita tráfico desde el SG del ALB.

### 4.5 Crear el Application Load Balancer (ELB)

En EC2 → Load Balancers → Create Application Load Balancer:

1. Nombre exacto: `elb-semi1-ht1-<TU_CARNÉ>`; reemplaza `<TU_CARNÉ>` por tu carné sin los símbolos `< >`. Ejemplo: `elb-semi1-ht1-202012345`.
2. Scheme: `Internet-facing`.
3. IP address type: `IPv4`.
4. Selecciona la misma VPC y por lo menos dos subredes públicas, idealmente en distintas zonas.
5. Crea o selecciona un SG llamado `sg-ht1-alb`.
6. Regla de entrada del SG del ALB: HTTP TCP `80` desde `0.0.0.0/0`.
7. Listener: `HTTP :80` → Forward to `tg-semi1-ht1-<carné>`.
8. Finaliza la creación y copia el DNS asignado al balanceador.

Después de crear el ALB, vuelve a `sg-ht1-ec2` y agrega TCP `8080` con origen `sg-ht1-alb`. Conserva también la regla temporal para tu IPv4 si necesitas repetir la prueba directa.

Valida el balanceador con:

```bash
export ALB_DNS="<DNS_DEL_ALB>"
curl -i "http://${ALB_DNS}/check"
curl "http://${ALB_DNS}/"
```

Actualiza varias veces `http://${ALB_DNS}/` o ejecuta:

```bash
for i in $(seq 1 10); do curl -s "http://${ALB_DNS}/"; echo; done
```

Deberás observar respuestas de `Instancia #1 - API #1` y `Instancia #2 - API #2`. La distribución no necesariamente alterna en cada solicitud debido al balanceo y a las conexiones persistentes; para evidenciar ambas respuestas, usa solicitudes separadas y actualiza la página.

### 4.6 Comprobar el ALB desde la interfaz de AWS

La consola no tiene un botón de “ejecutar” para el ALB. Se verifica que quedó funcionando revisando su estado, el estado de sus destinos y la respuesta de su DNS:

1. Abre la consola de AWS, entra a **EC2** y confirma que estás en la misma región donde creaste las instancias.
2. En el menú izquierdo entra a **Load Balancing → Load Balancers**.
3. Busca `elb-semi1-ht1-<carné>` y confirma:
   - **Type:** `Application`.
   - **State:** `Active`.
   - En la pestaña **Details**, copia el valor **DNS name**.
4. Abre la pestaña **Listeners and rules** del ALB y confirma que exista un listener `HTTP :80` cuya acción predeterminada sea **Forward to** tu Target Group.
5. En el menú izquierdo entra a **Load Balancing → Target Groups**, abre el Target Group y selecciona la pestaña **Targets**. Deben aparecer `Instancia-1` e `Instancia-2`, ambas en el puerto `8080` y con estado **Healthy**. El estado **Healthy** confirma que el ALB puede comunicarse con `/check`; si no es saludable, la consola muestra el motivo en los detalles del destino.
6. En una pestaña nueva del navegador abre `http://<DNS_NAME_DEL_ALB>` sin agregar `:8080`. Debe aparecer el JSON de una de las APIs. Actualiza varias veces o abre URLs como `http://<DNS_NAME_DEL_ALB>/?prueba=1` y `http://<DNS_NAME_DEL_ALB>/?prueba=2` para evidenciar ambas respuestas.

Para el video, muestra en este orden la lista del ALB con estado `Active`, el listener `HTTP:80`, el Target Group con sus dos destinos `Healthy`, el DNS y finalmente el JSON que aparece en el navegador.

Si el ALB está `Active` pero un destino aparece `Unhealthy`, todavía no pruebes el DNS: verifica primero en la instancia `curl -i http://127.0.0.1:8080/check`, que la API escuche en `0.0.0.0:8080` y que el grupo de seguridad de EC2 permita TCP `8080` desde el grupo de seguridad del ALB. Si el estado está `Provisioning`, espera unos minutos y actualiza la consola.

#### Error `Unused: Target is in an Availability Zone that is not enabled for the load balancer`

Este error significa que la instancia está en una zona de disponibilidad que no fue seleccionada para el ALB. Por ejemplo, si ambas instancias están en `us-east-1c`, el ALB también debe tener habilitada esa zona:

1. En **EC2 → Load Balancing → Load Balancers**, selecciona el ALB.
2. Abre la pestaña **Network mapping** y elige **Edit subnets**.
3. Marca `us-east-1c` y selecciona una subred pública de la misma VPC.
4. Elige **Save changes**.
5. Regresa a **Target Groups → tu grupo → Targets/Destinos** y actualiza la página.

Después de unos minutos, ambos destinos deben pasar de `Unused` a `Healthy`. Para un ALB público, la subred seleccionada debe tener salida hacia un Internet Gateway. Debes mantener al menos dos zonas habilitadas en el ALB y seleccionar las zonas donde realmente están registradas las instancias. AWS indica que los destinos ubicados en una zona no habilitada permanecen registrados, pero no reciben tráfico del balanceador.

Si no existe una subred pública disponible en `us-east-1c`, crea una subred pública en la misma VPC o lanza una nueva instancia en una zona que ya esté habilitada en el ALB. No es necesario modificar el código de las APIs.

## 5. Prueba de tolerancia a fallos

1. Confirma en Target Groups que ambos destinos estén `Healthy`.
2. Consume el DNS del ALB y muestra respuestas de ambas APIs.
3. En la instancia que elijas, detén únicamente su aplicación:

   ```bash
   sudo systemctl stop api-1-python   # si detienes Instancia-1
   # o
   sudo systemctl stop api-2-node      # si detienes Instancia-2
   ```

4. Espera a que el destino cambie a `Unhealthy` (normalmente después de los health checks configurados).
5. Consume nuevamente el DNS. Todas las respuestas deben provenir de la instancia que sigue saludable.
6. Inicia otra vez el servicio detenido:

   ```bash
   sudo systemctl start api-1-python
   # o
   sudo systemctl start api-2-node
   ```

7. Espera a que vuelva a `Healthy` y repite la prueba del DNS para mostrar nuevamente ambas APIs.

No detengas la instancia EC2 completa: la consigna pide detener la aplicación de una API, y hacerlo mediante `systemctl` deja clara la tolerancia a fallos del servicio.

## 6. Guión del video — máximo 10 minutos

Graba pantalla completa, aumenta el tamaño de la terminal y evita mostrar credenciales, claves privadas o información personal innecesaria. Antes de grabar, deja abiertas las pestañas de EC2, Target Groups y Load Balancers, y prepara las URLs.

### 0:00–0:40 — Introducción

Di: “Esta es la Hoja de Trabajo #1 de Seminario de Sistemas 1. Implementé dos APIs en lenguajes distintos: Python para API #1 y JavaScript/Node.js para API #2. Las desplegué en dos instancias EC2 y configuré un Application Load Balancer para demostrar distribución de tráfico y tolerancia a fallos.”

Muestra brevemente el repositorio y los archivos `api-1-python/app.py` y `api-2-node/server.js`, resaltando `/check` y `/`.

### 0:40–2:00 — Evidencia de las APIs y los lenguajes

Ejecuta y muestra:

```bash
curl -i http://localhost:8080/check
curl http://localhost:8080/
```

Explica que `/check` devuelve 200 y que `/` devuelve el JSON solicitado. Si haces la prueba local, aclara que el despliegue final está en EC2.

### 2:00–3:30 — Instancias EC2

En la consola muestra:

- `Instancia-1` con su IPv4 pública y API #1.
- `Instancia-2` con su IPv4 pública y API #2.
- Que ambas están en ejecución.

No muestres la clave `.pem`.

### 3:30–4:40 — Prueba directa por IPv4

Desde una terminal ejecuta:

```bash
curl -i http://<IP_1>:8080/check
curl http://<IP_1>:8080/
curl -i http://<IP_2>:8080/check
curl http://<IP_2>:8080/
```

Señala en pantalla el `200` y la diferencia entre `Instancia #1 - API #1` e `Instancia #2 - API #2`.

### 4:40–6:10 — Configuración y funcionamiento del ELB

Muestra:

- Nombre del ALB: `elb-semi1-ht1-<carné>`.
- DNS del ALB.
- Listener `HTTP:80`.
- Target Group con puerto `8080` y health check `/check`.
- Las dos instancias en estado `Healthy`.

Luego abre el DNS del ALB y actualiza varias veces. Muestra en el JSON que aparecen las dos instancias.

### 6:10–7:50 — Detención de una API

Di: “Ahora detendré solamente la aplicación de la API #1; la instancia EC2 continuará encendida.” Ejecuta:

```bash
sudo systemctl stop api-1-python
```

Muestra el destino como `Unhealthy` y consume el DNS del ALB varias veces. Explica que el balanceador deja de enviar tráfico al destino no saludable y que responde la instancia restante.

### 7:50–9:20 — Recuperación

Ejecuta:

```bash
sudo systemctl start api-1-python
```

Muestra que el destino vuelve a `Healthy`. Actualiza nuevamente el DNS del ALB hasta evidenciar las respuestas de ambas APIs.

### 9:20–10:00 — Cierre

Di: “Se verificaron los dos endpoints, las dos instancias con sus APIs, el listener y health check del ALB, la distribución hacia ambos destinos y la continuidad del servicio cuando una API se detiene. Finalmente se restauró la API y ambos destinos quedaron saludables.”

## 7. Checklist antes de entregar

- [ ] API #1 usa Python y API #2 usa JavaScript/Node.js.
- [ ] Ambas tienen `/check` con HTTP 200.
- [ ] Ambas tienen `/` y devuelven las tres claves exactas: `Instancia`, `Curso`, `Estudiante`.
- [ ] `CARNET` y nombre real reemplazados.
- [ ] EC2 se llaman exactamente `Instancia-1` e `Instancia-2`.
- [ ] Cada API está en la instancia correcta y responde por IPv4 pública.
- [ ] ALB se llama `elb-semi1-ht1-<carné>`.
- [ ] Listener HTTP `80` y Target Group HTTP `8080` configurados.
- [ ] Health check configurado en `/check`.
- [ ] Ambos destinos aparecen `Healthy` antes y después de la prueba.
- [ ] Se mostró el failover deteniendo solo una aplicación.
- [ ] Se reinició la aplicación y se evidenciaron otra vez ambas respuestas.
- [ ] Video ordenado y de 10 minutos o menos.
- [ ] URL de la grabación lista para entregar en UEDI.

## 8. Limpieza posterior

Para evitar cargos, al terminar la evidencia detén o termina las instancias según las indicaciones del curso y elimina el ALB, Target Group, Elastic IP y grupos de seguridad si ya no los necesitas. Verifica antes que no existan otros recursos que dependan de ellos.
