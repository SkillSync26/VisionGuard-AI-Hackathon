const video = document.getElementById("camera");
const result = document.getElementById("result");
const canvas = document.getElementById("canvas");

const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");

const objects = document.getElementById("objects");
const people = document.getElementById("people");
const fps = document.getElementById("fps");
const confidence = document.getElementById("confidence");
const counts = document.getElementById("counts");

const alertBox = document.getElementById("alert");

let stream = null;
let socket = null;
let timer = null;
let busy = false;


// ============================================================
// START CAMERA
// ============================================================

async function start() {

    // Camera already running
    if (stream) {
        return;
    }

    try {

        // ----------------------------------------------------
        // Request browser camera
        // ----------------------------------------------------

        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: 960,
                height: 540
            },
            audio: false
        });

        video.srcObject = stream;

        // Make sure video starts playing
        await video.play();


        // ----------------------------------------------------
        // WebSocket connection
        // IMPORTANT:
        // HTTPS  -> WSS
        // HTTP   -> WS
        // ----------------------------------------------------

        const wsProtocol =
            location.protocol === "https:"
                ? "wss:"
                : "ws:";

        const wsUrl =
            `${wsProtocol}//${location.host}/ws/live`;

        console.log("Connecting WebSocket:", wsUrl);

        socket = new WebSocket(wsUrl);


        // ----------------------------------------------------
        // WebSocket opened
        // ----------------------------------------------------

        socket.onopen = () => {

            console.log("WebSocket connected.");

            alertBox.textContent =
                "✓ Camera connected. AI detection running.";
        };


        // ----------------------------------------------------
        // Receive backend results
        // ----------------------------------------------------

        socket.onmessage = (event) => {

            try {

                const data = JSON.parse(event.data);


                // --------------------------------------------
                // Backend error
                // --------------------------------------------

                if (data.error) {

                    alertBox.textContent =
                        `⚠️ ${data.error}`;

                    busy = false;

                    return;
                }


                // --------------------------------------------
                // Processed image
                // --------------------------------------------

                if (data.image) {

                    result.src = data.image;
                }


                // --------------------------------------------
                // Statistics
                // --------------------------------------------

                const statistics =
                    data.statistics || {};


                objects.textContent =
                    statistics.total_objects ?? 0;


                people.textContent =
                    statistics.people ?? 0;


                fps.textContent =
                    Number(statistics.fps ?? 0).toFixed(2);


                const averageConfidence =
                    Number(
                        statistics.average_confidence ?? 0
                    );


                confidence.textContent =
                    `${(averageConfidence * 100).toFixed(1)}%`;


                // --------------------------------------------
                // Object counts
                // --------------------------------------------

                const objectCounts =
                    statistics.counts || {};


                counts.innerHTML =
                    Object.entries(objectCounts)
                        .map(
                            ([name, count]) =>
                                `<div>${name}: <b>${count}</b></div>`
                        )
                        .join("")
                    || "No objects";


                // --------------------------------------------
                // SMART ALERTS
                // --------------------------------------------

                const alerts =
                    data.alerts || [];


                if (alerts.length > 0) {

                    const alert =
                        alerts[0];


                    const icons = {

                        PHONE_DETECTED: "📱",

                        CROWD_DETECTED: "🚨",

                        PERSON_DETECTED: "👤",

                        WEAPON_DETECTED: "⚠️",

                        FIRE_DETECTED: "🔥"

                    };


                    const icon =
                        icons[alert.type] || "⚠️";


                    alertBox.textContent =
                        `${icon} ${alert.message}`;

                } else {

                    alertBox.textContent =
                        "✓ No active alert.";
                }


                busy = false;

            } catch (error) {

                console.error(
                    "Invalid backend response:",
                    error
                );

                busy = false;
            }
        };


        // ----------------------------------------------------
        // WebSocket error
        // ----------------------------------------------------

        socket.onerror = (error) => {

            console.error(
                "WebSocket error:",
                error
            );

            alertBox.textContent =
                "⚠️ AI backend connection failed.";

            busy = false;
        };


        // ----------------------------------------------------
        // WebSocket closed
        // ----------------------------------------------------

        socket.onclose = () => {

            console.log(
                "WebSocket connection closed."
            );

            busy = false;

        };


        // ----------------------------------------------------
        // Send frames to backend
        // ----------------------------------------------------

        timer = setInterval(
            sendFrame,
            140
        );

    } catch (error) {

        console.error(
            "Camera error:",
            error
        );

        alertBox.textContent =
            "⚠️ Camera access failed.";

        stream = null;
    }
}


// ============================================================
// SEND FRAME TO YOLO
// ============================================================

function sendFrame() {

    // Do not send if WebSocket isn't ready
    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN ||
        busy ||
        video.readyState < 2
    ) {

        return;
    }


    busy = true;


    // --------------------------------------------------------
    // Camera resolution
    // --------------------------------------------------------

    canvas.width = 960;
    canvas.height = 540;


    const ctx =
        canvas.getContext("2d");


    // --------------------------------------------------------
    // Draw current camera frame
    // --------------------------------------------------------

    ctx.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );


    // --------------------------------------------------------
    // Convert frame to JPEG
    // --------------------------------------------------------

    const imageData =
        canvas.toDataURL(
            "image/jpeg",
            0.82
        );


    // --------------------------------------------------------
    // Send frame to YOLO backend
    // --------------------------------------------------------

    socket.send(imageData);
}


// ============================================================
// STOP CAMERA
// ============================================================

async function stop() {

    console.log("Stopping camera...");


    // --------------------------------------------------------
    // Stop frame timer
    // --------------------------------------------------------

    if (timer) {

        clearInterval(timer);

        timer = null;
    }


    // --------------------------------------------------------
    // Close WebSocket
    // --------------------------------------------------------

    if (socket) {

        try {

            socket.close();

        } catch (error) {

            console.error(
                "WebSocket close error:",
                error
            );
        }
    }

    socket = null;


    // --------------------------------------------------------
    // Stop camera tracks
    // --------------------------------------------------------

    if (stream) {

        stream
            .getTracks()
            .forEach(
                track => track.stop()
            );
    }

    stream = null;


    // --------------------------------------------------------
    // Clear video
    // --------------------------------------------------------

    if (video) {

        video.srcObject = null;
    }


    busy = false;


    console.log("Camera stopped.");
}


// ============================================================
// BUTTONS
// ============================================================

if (startBtn) {

    startBtn.onclick = start;
}


if (stopBtn) {

    stopBtn.onclick = stop;
}


// ============================================================
// CLEANUP WHEN PAGE CLOSES
// ============================================================

window.addEventListener(
    "beforeunload",
    stop
);  