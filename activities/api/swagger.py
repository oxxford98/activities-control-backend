from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


today_query_params = [
    openapi.Parameter(
        'estimated_time',
        openapi.IN_QUERY,
        description='Filtra subtareas por tiempo estimado exacto (en horas). Ejemplo: 2',
        type=openapi.TYPE_INTEGER,
        required=False,
    ),
    openapi.Parameter(
        'type_activity',
        openapi.IN_QUERY,
        description=(
            'Filtra por tipo de actividad padre. '
            'Valores válidos: Examen, Quiz, Taller, Proyecto, Otro'
        ),
        type=openapi.TYPE_STRING,
        required=False,
        enum=['Examen', 'Quiz', 'Taller', 'Proyecto', 'Otro'],
    ),
    openapi.Parameter(
        'subject',
        openapi.IN_QUERY,
        description='Filtra por materia de la actividad padre (case-insensitive, búsqueda parcial). Ejemplo: matematicas',
        type=openapi.TYPE_STRING,
        required=False,
    ),
]

sub_activity_object = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id':             openapi.Schema(type=openapi.TYPE_INTEGER,  description='ID de la subtarea'),
        'name':           openapi.Schema(type=openapi.TYPE_STRING,   description='Nombre de la subtarea'),
        'description':    openapi.Schema(type=openapi.TYPE_STRING,   description='Descripción de la subtarea', nullable=True),
        'activity':       openapi.Schema(type=openapi.TYPE_INTEGER,  description='ID de la actividad padre'),
        'activity_name':  openapi.Schema(type=openapi.TYPE_STRING,   description='Título de la actividad padre'),
        'target_date':    openapi.Schema(type=openapi.TYPE_STRING,   format=openapi.FORMAT_DATETIME, description='Fecha y hora objetivo de la subtarea'),
        'estimated_time': openapi.Schema(type=openapi.TYPE_INTEGER,  description='Tiempo estimado en horas'),
        'status_expired': openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Estado calculado al momento del request',
            enum=['expired', 'today', 'upcoming'],
        ),
        'created_at':     openapi.Schema(type=openapi.TYPE_STRING,   format=openapi.FORMAT_DATETIME),
        'updated_at':     openapi.Schema(type=openapi.TYPE_STRING,   format=openapi.FORMAT_DATETIME),
        'deleted_at':     openapi.Schema(type=openapi.TYPE_STRING,   format=openapi.FORMAT_DATETIME, nullable=True),
    },
)

sub_activities_today_decorator = swagger_auto_schema(
    method='GET',
    operation_id='today',
    operation_description=(
        'Devuelve las subtareas del usuario autenticado agrupadas en tres categorías:\n\n'
        '- **expired**: `target_date` anterior al instante exacto del request. '
        'Ordenadas de la más antigua a la más reciente.\n'
        '- **today**: `target_date` mayor o igual al instante actual pero dentro del mismo día calendario. '
        'Ordenadas de la que antes vence a la que después vence.\n'
        '- **upcoming**: `target_date` en un día futuro. '
        'Ordenadas de la más cercana a la más lejana.\n\n'
        'En caso de empate en `target_date`, se desempata por `estimated_time` ascendente.\n\n'
        'Todos los filtros son opcionales y se pueden combinar entre sí.'
    ),
    manual_parameters=today_query_params,
    responses={
        200: openapi.Response(
            description='Subtareas clasificadas correctamente',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'now': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        format=openapi.FORMAT_DATETIME,
                        description='Fecha y hora exacta del servidor al momento del request',
                    ),
                    'expired':  openapi.Schema(type=openapi.TYPE_ARRAY, items=sub_activity_object, description='Subtareas vencidas'),
                    'today':    openapi.Schema(type=openapi.TYPE_ARRAY, items=sub_activity_object, description='Subtareas para hoy'),
                    'upcoming': openapi.Schema(type=openapi.TYPE_ARRAY, items=sub_activity_object, description='Subtareas próximas'),
                },
            ),
        ),
        400: openapi.Response(description='estimated_time no es un entero válido'),
        401: openapi.Response(description='Token no proporcionado o inválido'),
    },
    tags=['today'],
)