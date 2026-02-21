# Activities Control API

## Requisitos previos

- Python 3.10 o superior
- pip

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd activities-control-api
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
cp .env.example .env
```
Editar el archivo `.env`:
```env
SECRET_KEY=tu_secret_key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=*
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