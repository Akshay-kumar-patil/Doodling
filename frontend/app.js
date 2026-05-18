const state = {
    ws: null,
    roomId: "",
    username: "",
    drawer: "",
    players: [],
    connected: false,
    canDraw: false,
    isDrawing: false,
    lastX: null,
    lastY: null,
    scores: {},
    roomPoll: null,
    currentRound: 0,
    totalRounds: 0,
    roundActive: false,
    selectedColor: "#111111",
    pendingWordChoices: [],
};

const PEER_VOICE_BACKEND_URL = `${window.location.origin}/voice`;

const roomIdInput = document.getElementById("roomId");
const usernameInput = document.getElementById("username");
const playerCountInput = document.getElementById("playerCount");
const totalRoundsInput = document.getElementById("totalRounds");
const totalTimeInput = document.getElementById("totalTime");
const createRoomBtn = document.getElementById("createRoomBtn");
const connectBtn = document.getElementById("connectBtn");
const startBtn = document.getElementById("startBtn");
const clearCanvasBtn = document.getElementById("clearCanvasBtn");
const brushSize = document.getElementById("brushSize");
const statusText = document.getElementById("statusText");
const roleText = document.getElementById("roleText");
const wordText = document.getElementById("wordText");
const hintText = document.getElementById("hintText");
const drawerText = document.getElementById("drawerText");
const roundLabel = document.getElementById("roundLabel");
const timerBadge = document.getElementById("timerBadge");
const playersBox = document.getElementById("players");
const wordChoices = document.getElementById("wordChoices");
const scores = document.getElementById("scores");
const messages = document.getElementById("messages");
const chatInput = document.getElementById("chatInput");
const sendChatBtn = document.getElementById("sendChatBtn");
const wordModal = document.getElementById("wordModal");
const palette = document.getElementById("palette");
const roomSetup = document.getElementById("roomSetup");
const lobbyOverlay = document.getElementById("lobbyOverlay");
const lobbyPlayers = document.getElementById("lobbyPlayers");
const lobbyDrawtime = document.getElementById("lobbyDrawtime");
const lobbyRounds = document.getElementById("lobbyRounds");
const lobbyStartBtn = document.getElementById("lobbyStartBtn");
const lobbyJoinVoiceBtn = document.getElementById("lobbyJoinVoiceBtn");
const lobbyLeaveVoiceBtn = document.getElementById("lobbyLeaveVoiceBtn");
const inviteBtn = document.getElementById("inviteBtn");
const toolbar = document.getElementById("toolbar");
const sharedRoomIdText = document.getElementById("sharedRoomIdText");
const copyPeerRoomBtn = document.getElementById("copyPeerRoomBtn");
const openPeerRoomBtn = document.getElementById("openPeerRoomBtn");
const peerRoomLink = document.getElementById("peerRoomLink");
const joinVoiceBtn = document.getElementById("joinVoiceBtn");
const leaveVoiceBtn = document.getElementById("leaveVoiceBtn");
const quickJoinVoiceBtn = document.getElementById("quickJoinVoiceBtn");
const quickLeaveVoiceBtn = document.getElementById("quickLeaveVoiceBtn");
const voiceStatus = document.getElementById("voiceStatus");
const voiceMembers = document.getElementById("voiceMembers");
const voiceAudios = document.getElementById("voiceAudios");
const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");
const voiceClient = window.voiceRoom.createVoiceRoomClient({
    roomIdInput,
    usernameInput,
    statusNode: voiceStatus,
    membersNode: voiceMembers,
    audiosNode: voiceAudios,
    onStatus: addMessage,
});

ctx.lineCap = "round";
ctx.lineJoin = "round";

function setStatus(text) {
    statusText.textContent = text;
}

function syncSharedRoomIdDisplay() {
    window.peerRoom.syncPeerRoomControls({
        roomIdInput,
        usernameInput,
        roomIdText: sharedRoomIdText,
        linkNode: peerRoomLink,
    });
}

function addMessage(text, kind = "system") {
    const item = document.createElement("div");
    item.className = `message ${kind}`;
    item.textContent = text;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
}

function renderScores() {
    scores.innerHTML = "";
    const entries = Object.entries(state.scores).sort((a, b) => b[1] - a[1]);

    if (entries.length === 0) {
        scores.innerHTML = `<div class="score-row"><div></div><div>No scores yet</div><div></div></div>`;
        return;
    }

    entries.forEach(([name, score], index) => {
        const row = document.createElement("div");
        row.className = "score-row";
        row.innerHTML = `
            <div class="player-rank">#${index + 1}</div>
            <div class="player-meta">
                <div class="player-name">${name}</div>
                <div class="player-points">${score} points</div>
            </div>
            <div></div>
        `;
        scores.appendChild(row);
    });
}

function renderPlayers() {
    playersBox.innerHTML = "";

    if (state.players.length === 0) {
        playersBox.innerHTML = `<div class="player-card"><div class="player-rank">#</div><div class="player-meta"><div class="player-name">No players</div><div class="player-points">waiting</div></div><div class="player-badge">?</div></div>`;
        return;
    }

    const ordered = [...state.players].sort((a, b) => {
        const scoreA = state.scores[a] ?? 0;
        const scoreB = state.scores[b] ?? 0;
        return scoreB - scoreA;
    });

    ordered.forEach((player, index) => {
        const row = document.createElement("div");
        const isDrawer = player === state.drawer;
        const isSelf = player === state.username;
        row.className = `player-card${isDrawer ? " drawer" : ""}${isSelf ? " self" : ""}`;
        row.innerHTML = `
            <div class="player-rank">#${index + 1}</div>
            <div class="player-meta">
                <div class="player-name">${player}${isSelf ? " (You)" : ""}</div>
                <div class="player-points">${state.scores[player] ?? 0} points</div>
            </div>
            <div class="player-badge">${isDrawer ? "✏" : "☺"}</div>
        `;
        playersBox.appendChild(row);
    });
}

function updateRole() {
    const isDrawer = state.drawer === state.username;
    state.canDraw = state.connected && state.roundActive && isDrawer;
    if (!state.roundActive) {
        roleText.textContent = "WAITING";
    } else {
        roleText.textContent = isDrawer ? "DRAW THIS" : "GUESS THIS";
    }
    drawerText.textContent = state.drawer || "-";
}

function syncLobbyFields() {
    lobbyPlayers.value = playerCountInput.value;
    lobbyDrawtime.value = totalTimeInput.value;
    lobbyRounds.value = totalRoundsInput.value;
}

function syncTopFields() {
    playerCountInput.value = lobbyPlayers.value;
    totalTimeInput.value = lobbyDrawtime.value;
    totalRoundsInput.value = lobbyRounds.value;
}

function updateLobbyVisibility() {
    if (!state.connected) {
        lobbyOverlay.classList.remove("hidden");
        roomSetup.classList.remove("hidden");
        toolbar.classList.add("hidden-tools");
        return;
    }

    if (state.currentRound > 0 || state.roundActive) {
        lobbyOverlay.classList.add("hidden");
        roomSetup.classList.add("hidden");
    } else {
        lobbyOverlay.classList.remove("hidden");
        roomSetup.classList.remove("hidden");
    }

    if (state.canDraw) {
        toolbar.classList.remove("hidden-tools");
    } else {
        toolbar.classList.add("hidden-tools");
    }
}

function updateRoundLabel() {
    const total = Number(totalRoundsInput.value) || state.totalRounds || 0;
    const current = state.currentRound || 0;
    roundLabel.textContent = `Round ${current} of ${total}`;
}

function setWordChoices(choices) {
    wordChoices.innerHTML = "";
    wordModal.classList.remove("hidden");

    choices.forEach((word) => {
        const button = document.createElement("button");
        button.textContent = word;
        button.onclick = () => {
            sendMessage("word_selected", { select_word: word });
            wordModal.classList.add("hidden");
            wordChoices.innerHTML = "";
        };
        wordChoices.appendChild(button);
    });
}

function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function drawLine(x1, y1, x2, y2, color, size) {
    ctx.strokeStyle = color;
    ctx.lineWidth = size;
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
}

function sendMessage(type, data) {
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) {
        return;
    }
    state.ws.send(JSON.stringify({ type, data }));
}

async function createRoom() {
    syncTopFields();
    const username = usernameInput.value.trim();

    if (!username) {
        addMessage("Username is required", "system");
        return;
    }

    let sharedRoomId = "";
    try {
        const peerResponse = await fetch(`${PEER_VOICE_BACKEND_URL}/rooms/create`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                display_name: username,
            }),
        });

        if (!peerResponse.ok) {
            addMessage("Voice room could not be created", "system");
            return;
        }

        const peerRoom = await peerResponse.json();
        sharedRoomId = String(peerRoom.room_id || "").trim();
    } catch (error) {
        addMessage("Voice backend is not reachable", "system");
        return;
    }

    roomIdInput.value = sharedRoomId;
    syncSharedRoomIdDisplay();

    const params = new URLSearchParams({
        room_id: roomIdInput.value.trim(),
        username,
        total_rounds: totalRoundsInput.value.trim(),
        total_time: totalTimeInput.value.trim(),
    });

    const response = await fetch(`/host/create-room?${params.toString()}`, {
        method: "POST",
    });
    const result = await response.json();
    addMessage(result.message, "system");

    if (result.message === "room created successfully") {
        connectRoom();
    }
}

async function loadRoomState() {
    if (!state.roomId || !state.connected) {
        return;
    }

    try {
        const response = await fetch(`/room/${state.roomId}/state`);
        const result = await response.json();

        if (!result.success) {
            return;
        }

        state.players = result.players || [];
        state.scores = result.scores || {};
        state.drawer = result.drawer || "";
        state.roundActive = Boolean(result.round_active);
        state.currentRound = result.current_round || state.currentRound;
        state.totalRounds = result.total_rounds || state.totalRounds;
        if (result.time_remaining !== undefined) {
            timerBadge.textContent = result.time_remaining;
        }
        if (!state.roundActive) {
            wordModal.classList.add("hidden");
            state.pendingWordChoices = [];
            wordText.textContent = "-";
            hintText.textContent = "_ _ _ _ _";
        }
        updateRoundLabel();
        renderPlayers();
        renderScores();
        updateRole();
        updateLobbyVisibility();
    } catch (error) {
        console.error(error);
    }
}

function startRoomPolling() {
    if (state.roomPoll) {
        clearInterval(state.roomPoll);
    }

    loadRoomState();
    state.roomPoll = setInterval(loadRoomState, 1500);
}

function stopRoomPolling() {
    if (state.roomPoll) {
        clearInterval(state.roomPoll);
        state.roomPoll = null;
    }
}

function connectRoom() {
    syncSharedRoomIdDisplay();
    const roomId = roomIdInput.value.trim();
    const username = usernameInput.value.trim();

    if (!roomId || !username) {
        addMessage("Room ID and username are required", "system");
        return;
    }

    if (state.ws) {
        state.ws.close();
    }

    state.roomId = roomId;
    state.username = username;
    state.totalRounds = Number(totalRoundsInput.value) || 0;
    updateRoundLabel();
    timerBadge.textContent = totalTimeInput.value || "60";
    state.ws = new WebSocket(`ws://${window.location.host}/ws/${roomId}/${username}`);

    state.ws.onopen = () => {
        state.connected = true;
        setStatus("Connected");
        addMessage(`Connected as ${username}`, "system");
        startRoomPolling();
        updateLobbyVisibility();
    };

    state.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleIncoming(message);
    };

    state.ws.onclose = () => {
        state.connected = false;
        state.canDraw = false;
        state.players = [];
        state.drawer = "";
        state.roundActive = false;
        setStatus("Disconnected");
        wordModal.classList.add("hidden");
        renderPlayers();
        renderScores();
        updateRole();
        stopRoomPolling();
        updateLobbyVisibility();
        addMessage("Connection closed", "system");
    };
}

function handleIncoming(message) {
    if (message.error) {
        addMessage(`Error: ${message.error}`, "system");
        return;
    }

    if (message.type === "start") {
        state.drawer = message.drawer;
        state.currentRound = message.current_round || (state.currentRound + 1);
        state.totalRounds = message.total_rounds || state.totalRounds;
        state.roundActive = true;
        timerBadge.textContent = message.total_time ?? timerBadge.textContent;
        updateRoundLabel();
        updateRole();
        renderPlayers();
        clearCanvas();
        if (state.drawer !== state.username) {
            wordChoices.innerHTML = "";
            wordModal.classList.add("hidden");
        }
        wordText.textContent = state.drawer === state.username ? "choose a word" : "hidden";
        hintText.textContent = "_ _ _ _ _";
        updateLobbyVisibility();
        addMessage(`${message.drawer} is drawing now!`, "system");

        if (state.drawer === state.username && state.pendingWordChoices.length > 0) {
            setWordChoices(state.pendingWordChoices);
            state.pendingWordChoices = [];
        }
    }

    if (message.word_choices) {
        state.pendingWordChoices = message.word_choices;
        if (state.drawer === state.username) {
            setWordChoices(message.word_choices);
            state.pendingWordChoices = [];
        }
    }

    if (message.word) {
        wordText.textContent = message.word;
        hintText.textContent = "";
        state.pendingWordChoices = [];
    }

    if (message.hint) {
        hintText.textContent = message.hint;
        if (state.drawer !== state.username) {
            wordText.textContent = "hidden";
        }
    }

    if (message.type === "draw") {
        if (message.last_x !== undefined && message.last_y !== undefined) {
            drawLine(message.last_x, message.last_y, message.x, message.y, message.color, message.size);
        } else {
            drawLine(message.x, message.y, message.x + 0.01, message.y + 0.01, message.color, message.size);
        }
    }

    if (message.type === "chat") {
        addMessage(`${message.username}: ${message.text}`, "chat");
    }

    if (message.type === "correct_guess") {
        addMessage(message.text, "success");
    }

    if (message.type === "score_update") {
        state.scores = message.scores;
        renderScores();
        renderPlayers();
    }

    if (message.message) {
        const text = String(message.message);
        if (text.includes("joined") || text.includes("left") || text.includes("game over") || text.includes("round ended")) {
            addMessage(text, "system");
        }
        if (text.includes("round ended") || text.includes("game over")) {
            state.roundActive = false;
            wordModal.classList.add("hidden");
            updateRole();
            updateLobbyVisibility();
        }
    }
}

function getCanvasPoint(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    return {
        x: (event.clientX - rect.left) * scaleX,
        y: (event.clientY - rect.top) * scaleY,
    };
}

function startDrawing(event) {
    if (!state.canDraw) {
        return;
    }
    const point = getCanvasPoint(event);
    state.isDrawing = true;
    state.lastX = point.x;
    state.lastY = point.y;
}

function moveDrawing(event) {
    if (!state.isDrawing || !state.canDraw) {
        return;
    }

    const point = getCanvasPoint(event);
    const size = Number(brushSize.value);
    drawLine(state.lastX, state.lastY, point.x, point.y, state.selectedColor, size);
    sendMessage("draw", {
        last_x: state.lastX,
        last_y: state.lastY,
        x: point.x,
        y: point.y,
        color: state.selectedColor,
        size,
    });
    state.lastX = point.x;
    state.lastY = point.y;
}

function stopDrawing() {
    state.isDrawing = false;
    state.lastX = null;
    state.lastY = null;
}

palette.addEventListener("click", (event) => {
    const swatch = event.target.closest(".color-swatch");
    if (!swatch) {
        return;
    }

    document.querySelectorAll(".color-swatch").forEach((node) => node.classList.remove("active"));
    swatch.classList.add("active");
    state.selectedColor = swatch.dataset.color;
});

lobbyPlayers.addEventListener("change", syncTopFields);
lobbyDrawtime.addEventListener("change", () => {
    syncTopFields();
    timerBadge.textContent = lobbyDrawtime.value;
});
lobbyRounds.addEventListener("change", () => {
    syncTopFields();
    state.totalRounds = Number(lobbyRounds.value) || 0;
    updateRoundLabel();
});
playerCountInput.addEventListener("change", syncLobbyFields);
totalTimeInput.addEventListener("change", syncLobbyFields);
totalRoundsInput.addEventListener("change", syncLobbyFields);

createRoomBtn.onclick = createRoom;
connectBtn.onclick = connectRoom;
startBtn.onclick = () => {
    syncTopFields();
    sendMessage("start", {
        total_time: Number(totalTimeInput.value),
        total_rounds: Number(totalRoundsInput.value),
    });
};
lobbyStartBtn.onclick = () => {
    syncTopFields();
    sendMessage("start", {
        total_time: Number(totalTimeInput.value),
        total_rounds: Number(totalRoundsInput.value),
    });
};
inviteBtn.onclick = async () => {
    const text = `${window.location.origin} | room: ${roomIdInput.value.trim()}`;
    try {
        await navigator.clipboard.writeText(text);
        addMessage("Invite copied to clipboard", "system");
    } catch (error) {
        addMessage(text, "system");
    }
};
copyPeerRoomBtn.onclick = async () => {
    syncSharedRoomIdDisplay();
    try {
        const peerText = await window.peerRoom.copyPeerRoomId(roomIdInput.value.trim());
        addMessage("Peer room ID copied", "system");
    } catch (error) {
        const peerText = `Peer room ID: ${roomIdInput.value.trim()}`;
        addMessage(peerText, "system");
    }
};
openPeerRoomBtn.onclick = () => {
    syncSharedRoomIdDisplay();
    window.peerRoom.openPeerRoom(peerRoomLink.href);
};
joinVoiceBtn.onclick = () => {
    syncSharedRoomIdDisplay();
    voiceClient.join();
};
leaveVoiceBtn.onclick = () => {
    voiceClient.leave();
};
quickJoinVoiceBtn.onclick = () => {
    syncSharedRoomIdDisplay();
    voiceClient.join();
};
quickLeaveVoiceBtn.onclick = () => {
    voiceClient.leave();
};
lobbyJoinVoiceBtn.onclick = () => {
    syncSharedRoomIdDisplay();
    voiceClient.join();
};
lobbyLeaveVoiceBtn.onclick = () => {
    voiceClient.leave();
};
roomIdInput.addEventListener("input", syncSharedRoomIdDisplay);
usernameInput.addEventListener("input", syncSharedRoomIdDisplay);

sendChatBtn.onclick = () => {
    const text = chatInput.value.trim();
    if (!text) {
        return;
    }
    sendMessage("chat", { text });
    chatInput.value = "";
};

chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        sendChatBtn.click();
    }
});

clearCanvasBtn.onclick = clearCanvas;
canvas.addEventListener("pointerdown", startDrawing);
canvas.addEventListener("pointermove", moveDrawing);
canvas.addEventListener("pointerup", stopDrawing);
canvas.addEventListener("pointerleave", stopDrawing);

renderPlayers();
renderScores();
updateRoundLabel();
syncLobbyFields();
roomIdInput.value = window.sharedRoom.generateSharedRoomId();
syncSharedRoomIdDisplay();
updateLobbyVisibility();
