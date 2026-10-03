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


def _parameters_dict(action):
    """
    Convierte los parámetros de Aidy a un dict normal de Python.
    Compatible con:
      parameters: list[AidyParameter]
    y con:
      parameters: dict
    """

    parameters = action.parameters

    if isinstance(parameters, dict):
        return parameters

    result = {}

    for parameter in parameters or []:
        if hasattr(parameter, "clave"):
            result[parameter.clave] = parameter.valor
        elif isinstance(parameter, dict):
            result[parameter.get("clave", "")] = parameter.get("valor", "")

    return result


def _find_product_for_budget(product_data):
    """
    Busca un producto real de NexoRetail a partir del nombre/código
    recibido desde Aidy.
    """

    nombre = (
        product_data.get("nombre")
        or product_data.get("producto")
        or product_data.get("name")
        or ""
    ).strip()

    codigo = (
        product_data.get("codigo")
        or product_data.get("codigo_barras")
        or ""
    ).strip()

    query = codigo or nombre

    if not query:
        return None

    productos = buscar_productos(query)

    if not productos:
        return None

    return productos[0]


def execute_action(request, action, products=None):

    action_type = action.type
    parameters = _parameters_dict(action)

    if action_type not in ALLOWED_ACTIONS:
        return {
            "ok": False,
            "message": "Aidy intentó ejecutar una acción no permitida.",
        }

    # =========================================================
    # NONE
    # =========================================================

    if action_type == "none":
        return {
            "ok": True,
            "message": parameters.get(
                "message",
                "¿En qué puedo ayudarte?"
            ),
        }

    # =========================================================
    # BUSCAR PRODUCTO
    # =========================================================

    if action_type == "buscar_producto":

        query = parameters.get("producto", "")

        productos = buscar_productos(query)

        return {
            "ok": True,
            "message": (
                f"Encontré {len(productos)} producto(s) "
                f"para «{query}»."
            ),
            "data": [
                producto_data(p)
                for p in productos
            ],
        }

    # =========================================================
    # CONSULTAR STOCK
    # =========================================================

    if action_type == "consultar_stock":

        query = parameters.get("producto", "")

        productos = buscar_productos(query)

        if not productos:
            return {
                "ok": True,
                "message": (
                    f"No encontré productos relacionados "
                    f"con «{query}»."
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

    # =========================================================
    # CONSULTAR PRECIO
    # =========================================================

    if action_type == "consultar_precio":

        query = parameters.get("producto", "")

        productos = buscar_productos(query)

        if not productos:
            return {
                "ok": True,
                "message": f"No encontré «{query}».",
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

    # =========================================================
    # CREAR PRESUPUESTO
    # =========================================================

    if action_type == "crear_presupuesto":

        productos_importados = []

        for item in products or []:

            if hasattr(item, "model_dump"):
                item = item.model_dump()

            producto = _find_product_for_budget(item)

            if not producto:
                continue

            cantidad = (
                item.get("cantidad")
                or item.get("quantity")
                or 1
            )

            try:
                cantidad = float(cantidad)
            except (TypeError, ValueError):
                cantidad = 1

            data = producto_data(producto)

            productos_importados.append({
                "producto_id": producto.id,
                "id": producto.id,
                "nombre": producto.nombre,
                "cantidad": cantidad,
                "precio": data.get("precio", data.get("venta", 0)),
                "precio_unitario": data.get(
                    "precio",
                    data.get("venta", 0)
                ),
            })

        if not productos_importados:

            return {
                "ok": False,
                "message": (
                    "No pude encontrar los productos "
                    "para preparar el presupuesto."
                ),
            }

        cliente_nombre = (
            parameters.get("cliente")
            or parameters.get("cliente_nombre")
            or ""
        ).strip()

        try:
            url = reverse("pos_presupuesto")
        except Exception:
            url = "/presupuestos/nuevo/"

        return {
            "ok": True,
            "message": (
                f"Preparé el presupuesto para "
                f"{cliente_nombre or 'el cliente'}. "
                f"Te llevo al presupuesto con los "
                f"productos cargados."
            ),
            "action": {
                "type": "navegar",
                "url": url,
            },
            "data": {
                "url": url,
                "cliente": cliente_nombre,
                "cliente_nombre": cliente_nombre,
                "products": productos_importados,
                "productos": productos_importados,
            },
        }

    # =========================================================
    # ABRIR PRESUPUESTO
    # =========================================================

    if action_type == "abrir_presupuesto":

        presupuesto_id = (
            parameters.get("id")
            or parameters.get("presupuesto_id")
        )

        if not presupuesto_id:
            return {
                "ok": False,
                "message": "Necesito el número del presupuesto.",
            }

        try:
            url = reverse(
                "presupuesto_detalle",
                kwargs={"pk": presupuesto_id},
            )
        except Exception:
            url = f"/presupuestos/{presupuesto_id}/"

        return {
            "ok": True,
            "message": "Abriendo el presupuesto...",
            "data": {
                "url": url,
            },
            "action": {
                "type": "navegar",
                "url": url,
            },
        }

    # =========================================================
    # NAVEGAR
    # =========================================================

    if action_type == "navegar":

        url = parameters.get("url", "")

        if not url:
            return {
                "ok": False,
                "message": "No se especificó una página de destino.",
            }

        return {
            "ok": True,
            "message": parameters.get(
                "message",
                "Te llevo a esa sección."
            ),
            "data": {
                "url": url,
            },
            "action": {
                "type": "navegar",
                "url": url,
            },
        }

    # =========================================================
    # ACCIONES TODAVÍA NO IMPLEMENTADAS
    # =========================================================

    if action_type == "preparar_ingreso_stock":
        return {
            "ok": True,
            "message": "Preparando el ingreso de stock...",
        }

    if action_type == "procesar_archivo":
        return {
            "ok": True,
            "message": "Procesando el archivo...",
        }

    if action_type == "crear_ticket_soporte":
        return {
            "ok": True,
            "message": "Preparando el ticket de soporte...",
        }

    if action_type in {
        "ver_producto",
        "buscar_venta",
        "abrir_venta",
    }:
        return {
            "ok": True,
            "message": "Acción reconocida.",
        }

    return {
        "ok": True,
        "message": "Acción reconocida.",
    }