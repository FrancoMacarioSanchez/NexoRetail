(() => {


"use strict";


/* =====================================================
   ROOT
===================================================== */

const root =
    document.getElementById("aidy-root");

if (!root) {
    return;
}


const shell =
    root.querySelector(".aidy-shell");

const notch =
    root.querySelector(".aidy-state-notch");

const island =
    root.querySelector(".aidy-state-island");

const panel =
    root.querySelector(".aidy-state-panel");

const closeButton =
    root.querySelector(".aidy-panel-close");

const input =
    root.querySelector(".aidy-input");

const sendButton =
    root.querySelector(".aidy-send");

const chat =
    root.querySelector(".aidy-panel-content");

const toast =
    root.querySelector(".aidy-toast");

const processingMessage =
    root.querySelector(
        ".aidy-processing-message"
    );


/* =====================================================
   CONFIGURACIÓN
===================================================== */

const chatUrl =
    root.dataset.chatUrl ||
    "/api/aidy/chat/";

const fileUrl =
    root.dataset.fileUrl ||
    "/api/aidy/file/";


/* =====================================================
   ESTADO
===================================================== */

let currentState =
    root.dataset.state ||
    "notch";

let conversationId =
    sessionStorage.getItem(
        "aidy_conversation_id"
    );

let sending = false;

let blinkTimeout = null;


/* =====================================================
   CSRF
===================================================== */

function getCsrfToken() {

    const name =
        "csrftoken=";

    const cookies =
        document.cookie.split(";");

    for (
        let cookie of cookies
    ) {

        cookie =
            cookie.trim();

        if (
            cookie.startsWith(name)
        ) {

            return decodeURIComponent(
                cookie.substring(
                    name.length
                )
            );
        }
    }

    return "";
}


/* =====================================================
   CAMBIO DE ESTADO
===================================================== */

function setState(state) {

    if (
        ![
            "notch",
            "island",
            "panel"
        ].includes(state)
    ) {
        return;
    }


    currentState =
        state;

    root.dataset.state =
        state;


    /*
     * Actualizamos aria-hidden.
     */

    if (panel) {

        panel.setAttribute(
            "aria-hidden",
            state === "panel"
                ? "false"
                : "true"
        );
    }


    /*
     * Al volver al notch
     * limpiamos expresiones temporales.
     */

    if (state === "notch") {

        clearExpression();
    }
}


/* =====================================================
   EXPRESIONES
===================================================== */

function clearExpression() {

    root.classList.remove(
        "aidy-blink",
        "aidy-thinking",
        "aidy-processing",
        "aidy-success",
        "aidy-dragging",
        "aidy-typing",
        "aidy-mouth-open"
    );
}


function expression(name) {

    clearExpression();

    if (!name) {
        return;
    }

    root.classList.add(
        `aidy-${name}`
    );
}


/* =====================================================
   NOTCH
===================================================== */

function showNotch() {

    setState("notch");

    expression(null);
}


/* =====================================================
   ISLAND
===================================================== */

function showIsland(
    message = "¿En qué puedo ayudarte?"
) {

    const subtitle =
        root.querySelector(
            ".aidy-island-subtitle"
        );

    if (subtitle) {
        subtitle.textContent =
            message;
    }


    setState("island");

    expression(null);
}


/* =====================================================
   PANEL
===================================================== */

function openPanel() {

    setState("panel");

    expression("happy");


    setTimeout(() => {

        input?.focus();

    }, 500);
}


function closePanel() {

    setState("notch");

    expression(null);
}


/* =====================================================
   TOAST
===================================================== */

let toastTimer = null;


function showToast(message) {

    if (!toast) {
        return;
    }


    toast.textContent =
        message;


    toast.classList.add(
        "show"
    );


    clearTimeout(
        toastTimer
    );


    toastTimer =
        setTimeout(() => {

            toast.classList.remove(
                "show"
            );

        }, 2200);
}


/* =====================================================
   CHAT
===================================================== */

function scrollChat() {

    requestAnimationFrame(() => {

        chat.scrollTop =
            chat.scrollHeight;

    });
}


function addUserMessage(
    message
) {

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "aidy-chat-message";


    const avatar =
        document.createElement(
            "div"
        );

    avatar.className =
        "aidy-chat-avatar";

    avatar.textContent =
        "T";


    const body =
        document.createElement(
            "div"
        );

    body.className =
        "aidy-chat-body";


    const name =
        document.createElement(
            "div"
        );

    name.className =
        "aidy-chat-name";

    name.textContent =
        "Vos";


    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        "aidy-chat-bubble";

    bubble.textContent =
        message;


    body.appendChild(name);
    body.appendChild(bubble);

    wrapper.appendChild(avatar);
    wrapper.appendChild(body);

    chat.appendChild(wrapper);

    scrollChat();
}


function addAssistantMessage(
    message
) {

    const wrapper =
        document.createElement(
            "div"
        );

    wrapper.className =
        "aidy-chat-message";


    const avatar =
        document.createElement(
            "div"
        );

    avatar.className =
        "aidy-chat-avatar";

    avatar.textContent =
        "A";


    const body =
        document.createElement(
            "div"
        );

    body.className =
        "aidy-chat-body";


    const name =
        document.createElement(
            "div"
        );

    name.className =
        "aidy-chat-name";

    name.textContent =
        "Aidy";


    const bubble =
        document.createElement(
            "div"
        );

    bubble.className =
        "aidy-chat-bubble";

    bubble.textContent =
        message;


    body.appendChild(name);
    body.appendChild(bubble);

    wrapper.appendChild(avatar);
    wrapper.appendChild(body);

    chat.appendChild(wrapper);

    scrollChat();
}


/* =====================================================
   PROCESSING
===================================================== */

function showProcessing() {

    if (!processingMessage) {
        return;
    }

    processingMessage.hidden =
        false;

    scrollChat();
}


function hideProcessing() {

    if (!processingMessage) {
        return;
    }

    processingMessage.hidden =
        true;
}


/* =====================================================
   ENVIAR MENSAJE
===================================================== */

async function sendMessage() {

    if (!input) {
        return;
    }


    const message =
        input.value.trim();


    if (
        !message ||
        sending
    ) {
        return;
    }


    sending = true;

    sendButton.disabled =
        true;


    addUserMessage(
        message
    );


    input.value = "";


    expression(
        "thinking"
    );


    showProcessing();


    try {

        const payload = {
            message
        };


        if (conversationId) {

            payload.conversation_id =
                conversationId;
        }


        const response =
            await fetch(
                chatUrl,
                {
                    method: "POST",

                    credentials:
                        "same-origin",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "X-CSRFToken":
                            getCsrfToken(),

                        "X-Requested-With":
                            "XMLHttpRequest"
                    },

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        let data;


        try {

            data =
                await response.json();

        } catch {

            throw new Error(
                "El servidor devolvió una respuesta inválida."
            );
        }


        if (
            !response.ok ||
            !data.ok
        ) {

            throw new Error(
                data.message ||
                "Aidy no pudo procesar el mensaje."
            );
        }


        /* -----------------------------------------
           CONVERSACIÓN
        ----------------------------------------- */

        if (
            data.conversation_id
        ) {

            conversationId =
                data.conversation_id;


            sessionStorage.setItem(
                "aidy_conversation_id",
                conversationId
            );
        }


        hideProcessing();


        /* -----------------------------------------
           RESPUESTA
        ----------------------------------------- */

        if (data.message) {

            addAssistantMessage(
                data.message
            );
        }


        /* -----------------------------------------
           EXPRESIÓN
        ----------------------------------------- */

        if (
            data.state
        ) {

            expression(
                data.state
            );

        } else {

            expression(
                "happy"
            );
        }


        /* -----------------------------------------
           ACCIÓN
        ----------------------------------------- */

        await handleAction(
            data.action,
            data.data,
            data
        );


    } catch (error) {

        console.error(
            "[Aidy]",
            error
        );


        hideProcessing();


        expression(
            "surprised"
        );


        addAssistantMessage(
            "No pude comunicarme con el servicio de Aidy."
        );


        showToast(
            "Error de conexión con Aidy"
        );


    } finally {

        sending = false;

        sendButton.disabled =
            false;


        setTimeout(() => {

            if (!sending) {

                expression(
                    null
                );
            }

        }, 1200);
    }
}


/* =====================================================
   ACTION ROUTER
===================================================== */

async function handleAction(
    action,
    data,
    response
) {

    if (!action) {
        return;
    }


    const type =
        action.type;


    switch (type) {


        /* -----------------------------------------
           NADA
        ----------------------------------------- */

        case "none":

            break;


        /* -----------------------------------------
           PRODUCTOS
        ----------------------------------------- */

        case "buscar_producto":

            expression(
                "happy"
            );

            break;


        case "ver_producto":

            if (
                data?.url
            ) {

                navigate(
                    data.url
                );
            }

            break;


        case "consultar_stock":

            expression(
                "happy"
            );

            break;


        case "consultar_precio":

            expression(
                "happy"
            );

            break;


        /* -----------------------------------------
           PRESUPUESTOS
        ----------------------------------------- */

        case "crear_presupuesto":

            expression(
                "success"
            );


            setTimeout(() => {

                navigate(
                    "/presupuestos/nuevo/"
                );

            }, 500);

            break;


        case "abrir_presupuesto":

            if (
                data?.url
            ) {

                navigate(
                    data.url
                );

            } else if (
                data?.id
            ) {

                navigate(
                    `/presupuestos/${data.id}/`
                );
            }

            break;


        /* -----------------------------------------
           VENTAS
        ----------------------------------------- */

        case "buscar_venta":

            expression(
                "happy"
            );

            break;


        case "abrir_venta":

            if (
                data?.url
            ) {

                navigate(
                    data.url
                );

            } else if (
                data?.id
            ) {

                navigate(
                    `/ventas/${data.id}/`
                );
            }

            break;


        /* -----------------------------------------
           STOCK
        ----------------------------------------- */

        case "preparar_ingreso_stock":

            expression(
                "success"
            );


            if (
                data?.url
            ) {

                navigate(
                    data.url
                );

            } else {

                setTimeout(() => {

                    navigate(
                        "/stock/ingreso/"
                    );

                }, 500);
            }

            break;


        /* -----------------------------------------
           ARCHIVO
        ----------------------------------------- */

        case "procesar_archivo":

            expression(
                "processing"
            );

            break;


        /* -----------------------------------------
           SOPORTE
        ----------------------------------------- */

        case "crear_ticket_soporte":

            expression(
                "success"
            );

            break;


        /* -----------------------------------------
           NAVEGACIÓN
        ----------------------------------------- */

        case "navegar":

            if (
                action.parameters?.url
            ) {

                navigate(
                    action.parameters.url
                );
            }

            break;


        default:

            console.warn(
                "[Aidy] Acción no reconocida:",
                type
            );

            break;
    }
}


/* =====================================================
   NAVEGACIÓN SEGURA
===================================================== */

function navigate(url) {

    if (!url) {
        return;
    }


    try {

        const target =
            new URL(
                url,
                window.location.origin
            );


        /*
         * Aidy no puede navegar
         * a dominios externos.
         */

        if (
            target.origin !==
            window.location.origin
        ) {

            console.warn(
                "[Aidy] Navegación externa bloqueada."
            );

            return;
        }


        expression(
            "success"
        );


        setTimeout(() => {

            window.location.href =
                target.href;

        }, 500);

    } catch (error) {

        console.error(
            "[Aidy] URL inválida:",
            error
        );
    }
}


/* =====================================================
   ENTER
===================================================== */

input?.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            sendMessage();
        }
    }
);


sendButton?.addEventListener(
    "click",
    sendMessage
);


/* =====================================================
   NOTCH
===================================================== */

notch?.addEventListener(
    "click",
    event => {

        if (
            event.target.closest(
                "button"
            )
        ) {
            return;
        }

        showIsland();
    }
);


notch?.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Enter" ||
            event.key === " "
        ) {

            event.preventDefault();

            showIsland();
        }
    }
);


/* =====================================================
   ISLAND
===================================================== */

island?.addEventListener(
    "click",
    event => {

        const actionButton =
            event.target.closest(
                "[data-aidy-action]"
            );


        if (!actionButton) {

            openPanel();

            return;
        }


        const action =
            actionButton.dataset.aidyAction;


        switch (action) {

            case "open":

                openPanel();

                break;


            case "stock":

                openPanel();

                input.value =
                    "Quiero consultar el stock";

                sendMessage();

                break;


            case "budget":

                openPanel();

                input.value =
                    "Quiero crear un presupuesto";

                sendMessage();

                break;
        }
    }
);


/* =====================================================
   CERRAR
===================================================== */

closeButton?.addEventListener(
    "click",
    closePanel
);


/* =====================================================
   ESC
===================================================== */

document.addEventListener(
    "keydown",
    event => {

        if (
            event.key === "Escape" &&
            currentState !== "notch"
        ) {

            closePanel();
        }
    }
);


/* =====================================================
   CURSOR
===================================================== */

document.addEventListener(
    "mousemove",
    event => {

        const faces =
            root.querySelectorAll(
                ".aidy-face"
            );


        faces.forEach(
            face => {

                const rect =
                    face.getBoundingClientRect();


                const centerX =
                    rect.left +
                    rect.width / 2;


                const centerY =
                    rect.top +
                    rect.height / 2;


                const dx =
                    event.clientX -
                    centerX;


                const dy =
                    event.clientY -
                    centerY;


                const distance =
                    Math.sqrt(
                        dx * dx +
                        dy * dy
                    );


                const maxMovement =
                    3;


                const factor =
                    distance > 0
                        ? Math.min(
                            maxMovement /
                            distance,
                            1
                        )
                        : 0;


                face.style.transform =
                    `translate(
                        ${dx * factor}px,
                        ${dy * factor}px
                    )`;
            }
        );
    }
);


/* =====================================================
   PARPADEO
===================================================== */

function scheduleBlink() {

    clearTimeout(
        blinkTimeout
    );


    blinkTimeout =
        setTimeout(
            () => {

                if (
                    !document.hidden
                ) {

                    root.classList.add(
                        "aidy-blink"
                    );


                    setTimeout(
                        () => {

                            root.classList.remove(
                                "aidy-blink"
                            );

                        },
                        130
                    );
                }


                scheduleBlink();

            },

            2500 +
            Math.random() * 4000
        );
}


scheduleBlink();


/* =====================================================
   COPY
===================================================== */

document.addEventListener(
    "copy",
    () => {

        const selection =
            window
                .getSelection()
                ?.toString()
                .trim();


        if (!selection) {
            return;
        }


        expression(
            "happy"
        );


        showIsland(
            "Información copiada"
        );


        setTimeout(() => {

            if (
                currentState ===
                "island"
            ) {

                showNotch();
            }

        }, 1500);
    }
);


/* =====================================================
   DRAG & DROP
===================================================== */

let dragCounter = 0;


document.addEventListener(
    "dragenter",
    event => {

        if (
            event.dataTransfer?.types
                ?.includes("Files")
        ) {

            dragCounter++;

            expression(
                "dragging"
            );


            showIsland(
                "Soltá el archivo sobre Aidy"
            );
        }
    }
);


document.addEventListener(
    "dragleave",
    event => {

        if (
            event.dataTransfer?.types
                ?.includes("Files")
        ) {

            dragCounter--;


            if (
                dragCounter <= 0
            ) {

                dragCounter = 0;

                expression(null);
            }
        }
    }
);


document.addEventListener(
    "drop",
    async event => {

        const files =
            event.dataTransfer?.files;


        if (
            !files ||
            !files.length
        ) {
            return;
        }


        event.preventDefault();

        dragCounter = 0;


        const file =
            files[0];


        openPanel();


        expression(
            "processing"
        );


        addAssistantMessage(
            `Recibí "${file.name}".`
        );


        /*
         * Cuando implementemos el endpoint
         * /api/aidy/file/, este bloque
         * enviará el archivo directamente
         * al backend.
         */

        await uploadFile(
            file
        );
    }
);


/* =====================================================
   SUBIR ARCHIVO
===================================================== */

async function uploadFile(file) {

    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    try {

        const response =
            await fetch(
                fileUrl,
                {
                    method: "POST",

                    credentials:
                        "same-origin",

                    headers: {
                        "X-CSRFToken":
                            getCsrfToken()
                    },

                    body:
                        formData
                }
            );


        const data =
            await response.json();


        if (
            !response.ok ||
            !data.ok
        ) {

            throw new Error(
                data.message ||
                "No se pudo procesar el archivo."
            );
        }


        expression(
            data.state ||
            "happy"
        );


        if (data.message) {

            addAssistantMessage(
                data.message
            );
        }


        if (data.action) {

            await handleAction(
                data.action,
                data.data,
                data
            );
        }


    } catch (error) {

        console.error(
            "[Aidy] Archivo:",
            error
        );


        expression(
            "surprised"
        );


        addAssistantMessage(
            "No pude procesar el archivo."
        );
    }
}


/* =====================================================
   API GLOBAL
===================================================== */

window.Aidy = {

    open() {
        openPanel();
    },


    close() {
        closePanel();
    },


    island(message) {
        showIsland(
            message
        );
    },


    notch() {
        showNotch();
    },


    send(message) {

        openPanel();

        input.value =
            message;

        sendMessage();
    },


    say(message) {

        openPanel();

        addAssistantMessage(
            message
        );
    },


    thinking() {
        expression(
            "thinking"
        );
    },


    typing() {
        expression(
            "typing"
        );
    },


    processing() {
        expression(
            "processing"
        );
    },


    success() {
        expression(
            "success"
        );
    },


    happy() {
        expression(
            "happy"
        );
    },


    surprised() {
        expression(
            "surprised"
        );
    },


    dragging() {
        expression(
            "dragging"
        );
    },


    normal() {
        expression(null);
    },


    state() {

        return {
            state:
                currentState,

            conversationId,

            sending
        };
    },


    resetConversation() {

        conversationId =
            null;

        sessionStorage.removeItem(
            "aidy_conversation_id"
        );
    }

};


/* =====================================================
   INIT
===================================================== */

setState(
    "notch"
);

scheduleBlink();


})();
