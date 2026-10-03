/* =========================================================
   AIDY
   NexoRetail AI Assistant

   NOTCH
      ↓
   DYNAMIC ISLAND
      ↓
   PANEL
========================================================= */

(() => {
    "use strict";

    /* =====================================================
       ROOT
    ===================================================== */

    const root = document.getElementById("aidy-root");

    if (!root) {
        console.warn("[AIDY] #aidy-root no encontrado.");
        return;
    }

    /* =====================================================
       CONFIG
    ===================================================== */

    const CHAT_URL =
        root.dataset.chatUrl || "/api/aidy/chat/";

    const FILE_URL =
        root.dataset.fileUrl || "/api/aidy/file/";

    let conversationId = null;
    let isProcessing = false;

    /* =====================================================
       ELEMENTOS
    ===================================================== */

    const notch =
        root.querySelector(".aidy-state-notch");

    const dynamicIsland =
        root.querySelector(".aidy-state-island");

    const panel =
        root.querySelector(".aidy-state-panel");

    const chatInput =
        root.querySelector("#aidy-input") ||
        root.querySelector("#aidy-message") ||
        root.querySelector("#aidy-chat-input") ||
        root.querySelector(".aidy-input") ||
        root.querySelector(".aidy-chat-input") ||
        root.querySelector("textarea") ||
        root.querySelector('input[type="text"]');

    const sendButton =
        root.querySelector("#aidy-send") ||
        root.querySelector("#aidy-submit") ||
        root.querySelector(".aidy-send") ||
        root.querySelector(".aidy-submit") ||
        root.querySelector("[data-aidy-send]");

    const messagesContainer =
        root.querySelector("#aidy-messages") ||
        root.querySelector("#aidy-chat-messages") ||
        root.querySelector("#aidy-message-list") ||
        root.querySelector(".aidy-messages") ||
        root.querySelector(".aidy-chat-messages") ||
        root.querySelector(".aidy-message-list") ||
        root.querySelector("[data-aidy-messages]") ||
        root.querySelector(".aidy-panel-content");

    const fileInput =
        root.querySelector("#aidy-file") ||
        root.querySelector('input[type="file"]');

    const fileButton =
        root.querySelector("#aidy-file-button") ||
        root.querySelector(".aidy-file-button") ||
        root.querySelector("[data-aidy-file]");

    /* =====================================================
       CARAS DE AIDY
    ===================================================== */

    const avatars =
        Array.from(
            root.querySelectorAll(".aidy-avatar-element")
        );

    /*
     * Todas las caras.
     * Las usamos para animar simultáneamente
     * notch + island + panel.
     */

    const faces =
        Array.from(
            root.querySelectorAll(".aidy-face")
        );

    /* =====================================================
       DEBUG
    ===================================================== */

    console.log("[AIDY] Elementos encontrados:", {
        root: !!root,
        notch: !!notch,
        dynamicIsland: !!dynamicIsland,
        panel: !!panel,
        chatInput: !!chatInput,
        sendButton: !!sendButton,
        messagesContainer: !!messagesContainer,
        fileInput: !!fileInput,
        fileButton: !!fileButton,
        avatars: avatars.length,
        faces: faces.length,
    });

    /* =====================================================
       CSRF
    ===================================================== */

    function getCookie(name) {

        const cookies = document.cookie
            ? document.cookie.split(";")
            : [];

        for (const cookie of cookies) {

            const trimmed = cookie.trim();

            if (trimmed.startsWith(`${name}=`)) {

                return decodeURIComponent(
                    trimmed.substring(name.length + 1)
                );
            }
        }

        return null;
    }

    function getCSRFToken() {

        const cookieToken =
            getCookie("csrftoken");

        if (cookieToken) {
            return cookieToken;
        }

        const input =
            root.querySelector(
                'input[name="csrfmiddlewaretoken"]'
            );

        if (input) {
            return input.value;
        }

        const globalInput =
            document.querySelector(
                'input[name="csrfmiddlewaretoken"]'
            );

        if (globalInput) {
            return globalInput.value;
        }

        return "";
    }

    /* =====================================================
       AIDY FACE ENGINE
    ===================================================== */

    let blinkTimeout = null;
    let typingTimeout = null;
    let successTimeout = null;

    /*
     * Limpia estados visuales de la cara.
     */

    function clearFaceState() {

        root.classList.remove(
            "aidy-blink",
            "aidy-thinking",
            "aidy-processing",
            "aidy-success",
            "aidy-typing"
        );
    }

    /*
     * Parpadeo.
     */

    function blink() {

        if (!root.isConnected) {
            return;
        }

        if (
            root.classList.contains("aidy-processing") ||
            root.classList.contains("aidy-thinking")
        ) {
            scheduleBlink();
            return;
        }

        root.classList.add("aidy-blink");

        setTimeout(() => {

            root.classList.remove("aidy-blink");

        }, 120);

        scheduleBlink();
    }

    function scheduleBlink() {

        clearTimeout(blinkTimeout);

        const delay =
            2500 +
            Math.random() * 3500;

        blinkTimeout =
            setTimeout(
                blink,
                delay
            );
    }

    /*
     * Estado normal.
     */

    function faceNormal() {

        clearFaceState();

        if (chatInput === document.activeElement) {
            root.classList.add("aidy-typing");
        }
    }

    /*
     * Aidy está pensando.
     */

    function faceThinking() {

        clearFaceState();

        root.classList.add(
            "aidy-thinking"
        );
    }

    /*
     * Aidy está procesando.
     */

    function faceProcessing() {

        clearFaceState();

        root.classList.add(
            "aidy-processing"
        );
    }

    /*
     * Aidy terminó correctamente.
     */

    function faceSuccess() {

        clearFaceState();

        root.classList.add(
            "aidy-success"
        );

        clearTimeout(successTimeout);

        successTimeout =
            setTimeout(() => {

                faceNormal();

            }, 650);
    }

    /*
     * Aidy está escribiendo.
     */

    function faceTyping() {

        clearTimeout(typingTimeout);

        clearFaceState();

        root.classList.add(
            "aidy-typing"
        );

        typingTimeout =
            setTimeout(() => {

                if (
                    document.activeElement !== chatInput
                ) {
                    faceNormal();
                }

            }, 500);
    }

    /*
     * Seguimiento del mouse.
     *
     * La cara gira levemente hacia
     * donde está el cursor.
     */

    document.addEventListener(
        "mousemove",
        event => {

            if (!faces.length) {
                return;
            }

            if (
                root.classList.contains(
                    "aidy-processing"
                ) ||
                root.classList.contains(
                    "aidy-thinking"
                )
            ) {
                return;
            }

            faces.forEach(face => {

                const rect =
                    face.getBoundingClientRect();

                if (
                    rect.width === 0 ||
                    rect.height === 0
                ) {
                    return;
                }

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

                const maxDistance = 180;

                const moveX =
                    Math.max(
                        -3,
                        Math.min(
                            3,
                            dx / maxDistance * 3
                        )
                    );

                const moveY =
                    Math.max(
                        -2,
                        Math.min(
                            2,
                            dy / maxDistance * 2
                        )
                    );

                face.style.transform =
                    `translate(${moveX}px, ${moveY}px)`;
            });
        }
    );

    /*
     * Cuando el mouse sale de la ventana,
     * devolvemos la cara al centro.
     */

    document.addEventListener(
        "mouseleave",
        () => {

            faces.forEach(face => {

                face.style.transform =
                    "translate(0, 0)";

            });
        }
    );

    /*
     * Cuando el usuario escribe,
     * Aidy reacciona.
     */

    if (chatInput) {

        chatInput.addEventListener(
            "input",
            () => {

                if (isProcessing) {
                    return;
                }

                if (chatInput.value.trim()) {

                    faceTyping();

                } else {

                    faceNormal();

                }
            }
        );

        chatInput.addEventListener(
            "focus",
            () => {

                if (!isProcessing) {
                    faceTyping();
                }
            }
        );

        chatInput.addEventListener(
            "blur",
            () => {

                if (!isProcessing) {
                    faceNormal();
                }
            }
        );
    }

    /* =====================================================
       UI
    ===================================================== */

    function openPanel() {

        root.dataset.state = "panel";

        if (notch) {
            notch.classList.remove("active");
        }

        if (dynamicIsland) {
            dynamicIsland.classList.remove("active");
        }

        if (panel) {
            panel.classList.add("active");
        }

        setTimeout(() => {

            if (chatInput) {
                chatInput.focus();
            }

        }, 250);
    }

    function openIsland() {

        root.dataset.state = "island";

        if (notch) {
            notch.classList.remove("active");
        }

        if (dynamicIsland) {
            dynamicIsland.classList.add("active");
        }

        if (panel) {
            panel.classList.remove("active");
        }

        faceNormal();
    }

    function closeAidy() {

        root.dataset.state = "notch";

        if (notch) {
            notch.classList.add("active");
        }

        if (dynamicIsland) {
            dynamicIsland.classList.remove("active");
        }

        if (panel) {
            panel.classList.remove("active");
        }

        faceNormal();
    }

    /* =====================================================
       SCROLL
    ===================================================== */

    function scrollMessages() {

        if (!messagesContainer) {
            return;
        }

        messagesContainer.scrollTop =
            messagesContainer.scrollHeight;
    }

    /* =====================================================
       ESCAPE HTML
    ===================================================== */

    function escapeHTML(value) {

        const div =
            document.createElement("div");

        div.textContent =
            value === null ||
            value === undefined
                ? ""
                : String(value);

        return div.innerHTML;
    }

    /* =====================================================
       ADD MESSAGE
    ===================================================== */

    function addMessage(role, message) {

        const container =
            root.querySelector("#aidy-messages") ||
            root.querySelector(".aidy-messages") ||
            root.querySelector(".aidy-panel-content");

        if (!container) {

            console.error(
                "[AIDY] No encontré el contenedor de mensajes."
            );

            return;
        }

        const isUser =
            role === "user";

        const element =
            document.createElement("div");

        element.className = [
            "aidy-chat-message",
            "aidy-message",
            isUser
                ? "aidy-user-message"
                : "aidy-message-assistant"
        ].join(" ");

        const avatar =
            document.createElement("div");

        avatar.className =
            "aidy-chat-avatar";

        avatar.textContent =
            isUser
                ? "Tú"
                : "A";

        const body =
            document.createElement("div");

        body.className =
            "aidy-chat-body";

        const name =
            document.createElement("div");

        name.className =
            "aidy-chat-name";

        name.textContent =
            isUser
                ? "Vos"
                : "Aidy";

        const bubble =
            document.createElement("div");

        bubble.className =
            "aidy-chat-bubble";

        bubble.textContent =
            message || "";

        body.appendChild(name);
        body.appendChild(bubble);

        element.appendChild(avatar);
        element.appendChild(body);

        container.appendChild(element);

        scrollMessages();

        console.log(
            "[AIDY] Mensaje agregado:",
            {
                role,
                message
            }
        );
    }

    /* =====================================================
       LOADING
    ===================================================== */

    function showLoading() {

        if (!messagesContainer) {
            return;
        }

        const existing =
            messagesContainer.querySelector(
                ".aidy-loading"
            );

        if (existing) {
            return;
        }

        const element =
            document.createElement("div");

        element.className =
            "aidy-chat-message aidy-loading";

        element.innerHTML = `
            <div class="aidy-chat-avatar">
                A
            </div>

            <div class="aidy-chat-body">

                <div class="aidy-chat-name">
                    Aidy
                </div>

                <div class="aidy-chat-bubble">

                    <span class="aidy-processing-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </span>

                </div>

            </div>
        `;

        messagesContainer.appendChild(
            element
        );

        scrollMessages();

        faceProcessing();
    }

    function hideLoading() {

        if (!messagesContainer) {
            return;
        }

        const loading =
            messagesContainer.querySelector(
                ".aidy-loading"
            );

        if (loading) {
            loading.remove();
        }
    }

    /* =====================================================
       ERROR
    ===================================================== */

    function showError(message) {

        faceNormal();

        addMessage(
            "assistant",
            message ||
            "No pude procesar tu solicitud."
        );
    }

    /* =====================================================
       JSON
    ===================================================== */

    async function parseJSONResponse(response) {

        const text =
            await response.text();

        console.log(
            "[AIDY] HTTP:",
            response.status
        );

        console.log(
            "[AIDY] Respuesta raw:",
            text
        );

        try {

            return JSON.parse(text);

        } catch (error) {

            console.error(
                "[AIDY] Respuesta no JSON:",
                text
            );

            throw new Error(
                "El servidor devolvió una respuesta inválida."
            );
        }
    }

    /* =====================================================
       SEND MESSAGE
    ===================================================== */

    async function sendMessage(message) {

        if (!message || !message.trim()) {
            return;
        }

        if (isProcessing) {

            console.log(
                "[AIDY] Ya hay una solicitud en proceso."
            );

            return;
        }

        const cleanMessage =
            message.trim();

        addMessage(
            "user",
            cleanMessage
        );

        if (chatInput) {
            chatInput.value = "";
        }

        isProcessing = true;

        faceThinking();

        showLoading();

        try {

            console.log(
                "[AIDY] Enviando:",
                cleanMessage
            );

            const response =
                await fetch(
                    CHAT_URL,
                    {
                        method: "POST",

                        credentials:
                            "same-origin",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "X-CSRFToken":
                                getCSRFToken(),

                            "X-Requested-With":
                                "XMLHttpRequest",
                        },

                        body:
                            JSON.stringify({
                                message:
                                    cleanMessage,

                                conversation_id:
                                    conversationId,
                            }),
                    }
                );

            const data =
                await parseJSONResponse(
                    response
                );

            hideLoading();

            if (
                !response.ok ||
                !data.ok
            ) {

                throw new Error(
                    data.message ||
                    `Error HTTP ${response.status}`
                );
            }

            console.log(
                "[AIDY] JSON recibido:",
                data
            );

            if (data.conversation_id) {

                conversationId =
                    data.conversation_id;
            }

            addMessage(
                "assistant",
                data.message ||
                "Solicitud procesada."
            );

            isProcessing = false;

            faceSuccess();

            await handleAction(
                data.action,
                data.data
            );

        } catch (error) {

            hideLoading();

            isProcessing = false;

            console.error(
                "[AIDY] Error:",
                error
            );

            faceNormal();

            showError(
                error.message ||
                "No pude procesar tu solicitud."
            );

        } finally {

            isProcessing = false;

            if (chatInput) {
                chatInput.focus();
            }
        }
    }

    /* =====================================================
       PARAMETERS
    ===================================================== */

    function getParameter(
        parameters,
        key
    ) {

        if (!parameters) {
            return null;
        }

        if (
            typeof parameters === "object" &&
            !Array.isArray(parameters)
        ) {

            return (
                parameters[key] ??
                null
            );
        }

        if (Array.isArray(parameters)) {

            const parameter =
                parameters.find(
                    item =>
                        item &&
                        (
                            item.clave === key ||
                            item.key === key
                        )
                );

            if (parameter) {

                return (
                    parameter.valor ??
                    parameter.value ??
                    null
                );
            }
        }

        return null;
    }

    /* =====================================================
       ACTION HANDLER
    ===================================================== */

    async function handleAction(
        action,
        data
    ) {

        if (!action) {

            console.log(
                "[AIDY] Sin acción."
            );

            return;
        }

        let actionType =
            typeof action === "string"
                ? action
                : action.type;

        if (
            !actionType &&
            action.action
        ) {

            actionType =
                action.action;
        }

        console.log(
            "[AIDY] Acción:",
            actionType
        );

        console.log(
            "[AIDY] Action:",
            action
        );

        console.log(
            "[AIDY] Data:",
            data
        );

        if (
            actionType ===
            "navegar"
        ) {

            const url =
                action.url ||
                getParameter(
                    action.parameters,
                    "url"
                ) ||
                data?.url;

            if (!url) {

                console.error(
                    "[AIDY] navegar sin URL."
                );

                return;
            }

            console.log(
                "[AIDY] Navegando:",
                url
            );

            window.location.assign(
                url
            );

            return;
        }

        if (
            actionType ===
            "crear_presupuesto"
        ) {

            if (data) {

                const budgetData = {
                    ...data,

                    products:
                        data.products ||
                        data.productos ||
                        [],

                    productos:
                        data.productos ||
                        data.products ||
                        [],

                    cliente:
                        data.cliente ||
                        data.cliente_nombre ||
                        "",

                    cliente_nombre:
                        data.cliente_nombre ||
                        data.cliente ||
                        "",
                };

                sessionStorage.setItem(
                    "aidy_budget_import",
                    JSON.stringify(
                        budgetData
                    )
                );

                console.log(
                    "[AIDY] Presupuesto guardado:",
                    budgetData
                );
            }

            const url =
                action.url ||
                data?.url ||
                "/presupuestos/nuevo/";

            console.log(
                "[AIDY] Redirigiendo:",
                url
            );

            window.location.assign(
                url
            );

            return;
        }

        if (
            actionType ===
            "abrir_presupuesto"
        ) {

            const url =
                action.url ||
                getParameter(
                    action.parameters,
                    "url"
                ) ||
                data?.url;

            if (!url) {
                return;
            }

            window.location.assign(
                url
            );

            return;
        }

        if (
            actionType ===
            "preparar_ingreso_stock"
        ) {

            if (data) {

                sessionStorage.setItem(
                    "aidy_stock_import",
                    JSON.stringify(data)
                );
            }

            const url =
                action.url ||
                data?.url ||
                "/inventario/ingreso/";

            window.location.assign(
                url
            );

            return;
        }

        if (
            actionType ===
            "procesar_archivo"
        ) {

            if (data?.url) {

                window.location.assign(
                    data.url
                );
            }

            return;
        }

        if (
            actionType ===
            "crear_ticket_soporte"
        ) {

            if (data?.url) {

                window.location.assign(
                    data.url
                );
            }

            return;
        }

        console.log(
            "[AIDY] Acción sin handler:",
            actionType
        );
    }

    /* =====================================================
       FILE UPLOAD
    ===================================================== */

    async function uploadFile(file) {

        if (!file) {
            return;
        }

        if (isProcessing) {
            return;
        }

        isProcessing = true;

        faceThinking();

        addMessage(
            "user",
            `Archivo enviado: ${file.name}`
        );

        showLoading();

        try {

            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );

            const response =
                await fetch(
                    FILE_URL,
                    {
                        method: "POST",

                        credentials:
                            "same-origin",

                        headers: {
                            "X-CSRFToken":
                                getCSRFToken(),

                            "X-Requested-With":
                                "XMLHttpRequest",
                        },

                        body: formData,
                    }
                );

            const data =
                await parseJSONResponse(
                    response
                );

            hideLoading();

            if (
                !response.ok ||
                !data.ok
            ) {

                throw new Error(
                    data.message ||
                    "No pude procesar el archivo."
                );
            }

            addMessage(
                "assistant",
                data.message ||
                "Archivo procesado correctamente."
            );

            faceSuccess();

            if (data.action) {

                await handleAction(
                    data.action,
                    data.data
                );
            }

        } catch (error) {

            hideLoading();

            console.error(
                "[AIDY] Error archivo:",
                error
            );

            faceNormal();

            showError(
                error.message ||
                "No pude procesar el archivo."
            );

        } finally {

            isProcessing = false;

            if (fileInput) {
                fileInput.value = "";
            }
        }
    }

    /* =====================================================
       EVENTOS UI
    ===================================================== */

    if (notch) {

        notch.addEventListener(
            "click",
            () => {
                openIsland();
            }
        );
    }

    if (dynamicIsland) {

        dynamicIsland.addEventListener(
            "click",
            event => {

                /*
                 * Si se hace click en el campo
                 * del Dynamic Island, abrimos el panel.
                 */

                const target =
                    event.target;

                if (
                    target &&
                    (
                        target.matches(
                            ".aidy-island-input"
                        ) ||
                        target.closest(
                            ".aidy-island-input"
                        )
                    )
                ) {

                    openPanel();
                    return;
                }

                openPanel();
            }
        );
    }

    root.querySelectorAll(
        "[data-aidy-close]"
    ).forEach(button => {

        button.addEventListener(
            "click",
            event => {

                event.preventDefault();

                closeAidy();
            }
        );
    });

    root.querySelectorAll(
        "[data-aidy-open]"
    ).forEach(button => {

        button.addEventListener(
            "click",
            event => {

                event.preventDefault();

                openPanel();
            }
        );
    });

    /* =====================================================
       SEND
    ===================================================== */

    if (sendButton) {

        sendButton.addEventListener(
            "click",
            event => {

                event.preventDefault();

                if (!chatInput) {
                    return;
                }

                sendMessage(
                    chatInput.value
                );
            }
        );
    }

    /* =====================================================
       ENTER
    ===================================================== */

    if (chatInput) {

        chatInput.addEventListener(
            "keydown",
            event => {

                if (
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {

                    event.preventDefault();

                    sendMessage(
                        chatInput.value
                    );
                }
            }
        );
    }

    /* =====================================================
       FILE
    ===================================================== */

    if (
        fileButton &&
        fileInput
    ) {

        fileButton.addEventListener(
            "click",
            event => {

                event.preventDefault();

                fileInput.click();
            }
        );
    }

    if (fileInput) {

        fileInput.addEventListener(
            "change",
            event => {

                const file =
                    event.target.files?.[0];

                if (file) {
                    uploadFile(file);
                }
            }
        );
    }

    /* =====================================================
       DRAG & DROP
    ===================================================== */

    const dropZone =
        root.querySelector(
            "[data-aidy-dropzone]"
        );

    if (dropZone) {

        [
            "dragenter",
            "dragover",
        ].forEach(
            eventName => {

                dropZone.addEventListener(
                    eventName,
                    event => {

                        event.preventDefault();

                        dropZone.classList.add(
                            "dragging"
                        );
                    }
                );
            }
        );

        [
            "dragleave",
            "drop",
        ].forEach(
            eventName => {

                dropZone.addEventListener(
                    eventName,
                    event => {

                        event.preventDefault();

                        dropZone.classList.remove(
                            "dragging"
                        );
                    }
                );
            }
        );

        dropZone.addEventListener(
            "drop",
            event => {

                const file =
                    event.dataTransfer
                        ?.files?.[0];

                if (file) {
                    uploadFile(file);
                }
            }
        );
    }

    /* =====================================================
       NEW CHAT
    ===================================================== */

    root.querySelectorAll(
        "[data-aidy-new-chat]"
    ).forEach(button => {

        button.addEventListener(
            "click",
            event => {

                event.preventDefault();

                conversationId = null;

                if (messagesContainer) {
                    messagesContainer.innerHTML = "";
                }

                addMessage(
                    "assistant",
                    "Hola 👋\n\nSoy Aidy, el asistente de NexoRetail.\n\nPuedo ayudarte con productos, stock, presupuestos, ventas, archivos y soporte."
                );

                faceNormal();

                openPanel();
            }
        );
    });

    /* =====================================================
       ESC
    ===================================================== */

    document.addEventListener(
        "keydown",
        event => {

            if (event.key === "Escape") {
                closeAidy();
            }
        }
    );

    /* =====================================================
       PAGE LIFECYCLE
    ===================================================== */

    window.addEventListener(
        "pageshow",
        () => {

            isProcessing = false;

            if (chatInput) {
                chatInput.disabled = false;
            }

            if (sendButton) {
                sendButton.disabled = false;
            }

            faceNormal();

            console.log(
                "[AIDY] pageshow → desbloqueado"
            );
        }
    );

    window.addEventListener(
        "pagehide",
        () => {

            isProcessing = false;

            console.log(
                "[AIDY] pagehide → desbloqueado"
            );
        }
    );

    /* =====================================================
       INIT
    ===================================================== */

    function init() {

        if (!root.dataset.state) {
            root.dataset.state = "notch";
        }

        if (
            root.dataset.state === "notch" &&
            notch
        ) {

            notch.classList.add(
                "active"
            );
        }

        /*
         * Arrancar comportamiento de la cara.
         */

        faceNormal();

        scheduleBlink();

        console.log(
            "[AIDY] Inicializado."
        );

        console.log(
            "[AIDY] Chat URL:",
            CHAT_URL
        );

        console.log(
            "[AIDY] File URL:",
            FILE_URL
        );

        console.log(
            "[AIDY] Chat input:",
            chatInput
        );

        console.log(
            "[AIDY] Send button:",
            sendButton
        );

        console.log(
            "[AIDY] Messages container:",
            messagesContainer
        );

        console.log(
            "[AIDY] Caras encontradas:",
            faces.length
        );
    }

    init();

})();