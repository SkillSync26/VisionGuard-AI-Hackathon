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

    if (stream) {
        return;
    }

    try {

        stream =
            await navigator.mediaDevices.getUserMedia({
                video: {
                    width: 960,
                    height: 540
                },
                audio: false
            });

        video.srcObject = stream;


        // ----------------------------------------------------
        // WebSocket connection
        // ----------------------------------------------------

        socket =
            new WebSocket(
                `ws://${location.host}/ws/live`
            );


        // ----------------------------------------------------
        // Receive backend results
        // ----------------------------------------------------

        socket.onmessage = (event) => {

            const data =
                JSON.parse(event.data);


            // -----------------------------------------------
            // Backend error
            // -----------------------------------------------

            if (data.error) {

                alertBox.textContent =
                    `⚠️ ${data.error}`;

                busy = false;

                return;
            }


            // -----------------------------------------------
            // Processed image
            // -----------------------------------------------

            if (data.image) {

                result.src =
                    data.image;
            }


            // -----------------------------------------------
            // Statistics
            // -----------------------------------------------

            const statistics =
                data.statistics || {};


            objects.textContent =
                statistics.total_objects ?? 0;


            people.textContent =
                statistics.people ?? 0;


            fps.textContent =
                statistics.fps ?? 0;


            confidence.textContent =
                `${(
                    (statistics.average_confidence || 0)
                    * 100
                ).toFixed(1)}%`;


            // -----------------------------------------------
            // Object counts
            // -----------------------------------------------

            counts.innerHTML =
                Object.entries(
                    statistics.counts || {}
                )
                .map(
                    ([name, count]) =>
                        `<div>${name}: <b>${count}</b></div>`
                )
                .join("")
                || "No objects";


            // -----------------------------------------------
            // SMART ALERTS
            // -----------------------------------------------

            const alerts =
                data.alerts || [];


            if (alerts.length > 0) {

                const alert =
                    alerts[0];


                const icons = {

                    PHONE_DETECTED:
                        "📱",

                    CROWD_DETECTED:
                        "🚨"
                };


                const icon =
                    icons[alert.type]
                    || "⚠️";


                alertBox.textContent =
                    `${icon} ${alert.message}`;


            } else {

                alertBox.textContent =
                    "✓ No active alert.";

            }


            busy = false;
        };


        // ----------------------------------------------------
        // WebSocket closed
        // ----------------------------------------------------

        socket.onclose = () => {

            busy = false;
        };


        // ----------------------------------------------------
        // Send frames
        // ----------------------------------------------------

        timer =
            setInterval(
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

    }
}


// ============================================================
// SEND FRAME TO YOLO
// ============================================================

function sendFrame() {

    if (
        !socket ||
        socket.readyState !== WebSocket.OPEN ||
        busy ||
        video.readyState < 2
    ) {

        return;
    }


    busy = true;


    // Use the full camera resolution
    canvas.width = 960;
    canvas.height = 540;


    const ctx =
        canvas.getContext("2d");


    ctx.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );


    // Higher JPEG quality
    socket.send(
        canvas.toDataURL(
            "image/jpeg",
            0.82
        )
    );
}


// ============================================================
// STOP CAMERA
// ============================================================

async function stop() {

    clearInterval(timer);

    timer = null;


    if (socket) {

        socket.close();
    }

    socket = null;


    if (stream) {

        stream
            .getTracks()
            .forEach(
                track => track.stop()
            );
    }

    stream = null;

    busy = false;
}


// ============================================================
// BUTTONS
// ============================================================

startBtn.onclick = start;

stopBtn.onclick = stop;


// ============================================================
// CLEANUP WHEN PAGE CLOSES
// ============================================================

window.addEventListener(
    "beforeunload",
    stop
);