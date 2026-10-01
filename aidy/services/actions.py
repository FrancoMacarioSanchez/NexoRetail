# aidy/services/actions.py

from django.urls import reverse

from .products import buscar_productos, producto_data


ALLOWED_ACTIONS = {
    "buscar_producto",
    "ver_producto",
    "consultar_stock",
    "consultar_precio",
    "crear_presupuesto",
    "abrir_presupuesto",
    "buscar_venta",
    "abrir_venta",
    "procesar_archivo",
    "preparar_ingreso_stock",
    "crear_ticket_soporte",
    "navegar",
    "none",
}


def execute_action(request, action):

    action_type = action.type

    if action_type not in ALLOWED_ACTIONS:
        return {
            "ok": False,
            "message": "Aidy intentó ejecutar una acción no permitida.",
        }

    if action_type == "none":

        return {
            "ok": True,
            "message": action.parameters.get(
                "message",
                "¿En qué puedo ayudarte?"
            ),
        }

    if action_type == "buscar_producto":

        query = action.parameters.get(
            "producto",
            ""
        )

        productos = buscar_productos(query)

        return {
            "ok": True,
            "message": (
                f"Encontré {len(productos)} "
                f"producto(s) para «{query}»."
            ),
            "data": [
                producto_data(p)
                for p in productos
            ],
        }

    if action_type == "consultar_stock":

        query = action.parameters.get(
            "producto",
            ""
        )

        productos = buscar_productos(query)

        if not productos:
            return {
                "ok": True,
                "message": (
                    f"No encontré productos "
                    f"relacionados con «{query}»."
                ),
            }

        producto = productos[0]

        return {
            "ok": True,
            "message": (
                f"{producto.nombre} tiene "
                f"{producto.stock_actual} "
                f"{producto.get_unidad_medida_display()} "
                f"en stock."
            ),
            "data": producto_data(producto),
        }

    if action_type == "consultar_precio":

        query = action.parameters.get(
            "producto",
            ""
        )

        productos = buscar_productos(query)

        if not productos:
            return {
                "ok": True,
                "message": (
                    f"No encontré «{query}»."
                ),
            }

        producto = productos[0]

        return {
            "ok": True,
            "message": (
                f"{producto.nombre} cuesta "
                f"${producto.precio} sin IVA."
            ),
            "data": producto_data(producto),
        }

    return {
        "ok": True,
        "message": "Acción reconocida.",
    }