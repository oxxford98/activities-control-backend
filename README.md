# Activities Control API

## Requisitos previos

- Python 3.10 o superior
- pip
- PostgreSQL 14 o superior

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd activities-control-backend
```

2. Crear y activar entorno virtual:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
# Linux/Mac
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```
Editar el archivo `.env`:
```env
SECRET_KEY=tu_secret_key
DEBUG=True
ALLOWED_HOSTS=*
POSTGRES_DB=activities_db
POSTGRES_USER=activities_user
POSTGRES_PASSWORD=activities_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

5. Aplicar migraciones:
```bash
python manage.py migrate
```

6. Crear superusuario:
```bash
python manage.py createsuperuser
```

## Iniciar en desarrollo

```bash
python manage.py runserver
```

## CI (Fase 1)

El proyecto incluye un pipeline de CI con GitHub Actions en `.github/workflows/ci.yml` que se ejecuta en `pull_request` y en `push` a `main`.

Validaciones incluidas:

- Instalacion de dependencias
- Ejecucion de migraciones
- Verificacion de modelos pendientes (`makemigrations --check --dry-run`)
- Validacion de Django (`check --deploy`)
- Ejecucion de tests (`manage.py test`)

## CD a servidor Ubuntu (Fase 2)

Se agrego el workflow `.github/workflows/deploy-ubuntu.yml` para desplegar automaticamente cuando:

- CI termina en estado exitoso
- El branch es `main`

El deploy se realiza por SSH sobre tu servidor Ubuntu y ejecuta:

- `git pull origin main`
- `docker compose up -d --build --remove-orphans`

### Secretos requeridos en GitHub

Configuralos en: `Settings > Secrets and variables > Actions`

- `VPS_HOST`: IP o dominio del servidor
- `VPS_USER`: usuario SSH (ejemplo: ubuntu)
- `VPS_SSH_KEY`: clave privada SSH en formato PEM
- `VPS_SSH_PORT`: puerto SSH (normalmente 22)
- `VPS_APP_PATH`: ruta absoluta del proyecto en el servidor (ejemplo: /opt/activities-control-backend)

### Preparacion inicial en servidor (solo una vez)

1. Instalar Docker y Docker Compose plugin.
2. Clonar el repositorio en la ruta de `VPS_APP_PATH`.
3. Crear y completar archivo `.env` con valores de produccion.
4. Ejecutar una primera subida manual:

```bash
docker compose up -d --build
```

Desde ese momento, cada merge/push a `main` (con CI exitoso) actualiza automaticamente el servidor.