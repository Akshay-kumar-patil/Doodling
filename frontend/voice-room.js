(function () {
    function getBackendUrl() {
        return `${window.location.origin}/voice`;
    }

    function getSocketBaseUrl() {
        return window.location.origin.replace("http://", "ws://").replace("https://", "wss://");
    }

    function makePeerId() {
        const array = new Uint32Array(4);
        window.crypto.getRandomValues(array);
        return Array.from(array, (value) => value.toString(16).padStart(8, "0")).join("").slice(0, 16);
    }

    function createVoiceRoomClient(options) {
        const {
            roomIdInput,
            usernameInput,
            statusNode,
            membersNode,
            audiosNode,
            onStatus,
        } = options;

        const state = {
            socket: null,
            localStream: null,
            currentMembers: [],
            peerId: "",
            peers: new Map(),
            remoteAudios: new Map(),
            waitingIceCandidates: new Map(),
        };

        function reportStatus(text, kind = "system") {
            statusNode.textContent = text;
            if (onStatus) {
                onStatus(text, kind);
            }
        }

        function renderMembers() {
            membersNode.innerHTML = "";

            if (state.currentMembers.length === 0) {
                membersNode.innerHTML = `<div class="voice-member-empty">No one in voice yet</div>`;
                return;
            }

            state.currentMembers.forEach((member) => {
                const row = document.createElement("div");
                row.className = "voice-member";
                row.innerHTML = `
                    <div class="voice-member-name">${member.display_name}</div>
                    <div class="voice-member-role">${member.peer_id === state.peerId ? "You" : (member.is_host ? "Host" : "Guest")}</div>
                `;
                membersNode.appendChild(row);
            });
        }

        function makeAudioPlayer(remotePeerId, remoteName) {
            if (state.remoteAudios.has(remotePeerId)) {
                return state.remoteAudios.get(remotePeerId);
            }

            const wrapper = document.createElement("div");
            wrapper.className = "voice-audio-row";
            wrapper.id = `voice-audio-${remotePeerId}`;

            const title = document.createElement("div");
            title.className = "voice-audio-title";
            title.textContent = `Listening to ${remoteName}`;

            const audio = document.createElement("audio");
            audio.autoplay = true;
            audio.controls = true;

            wrapper.appendChild(title);
            wrapper.appendChild(audio);
            audiosNode.appendChild(wrapper);

            state.remoteAudios.set(remotePeerId, audio);
            return audio;
        }

        function removeAudioPlayer(remotePeerId) {
            const audio = state.remoteAudios.get(remotePeerId);
            if (audio) {
                audio.srcObject = null;
                state.remoteAudios.delete(remotePeerId);
            }

            const wrapper = document.getElementById(`voice-audio-${remotePeerId}`);
            if (wrapper) {
                wrapper.remove();
            }
        }

        async function sendSignal(type, target, payload) {
            if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
                return;
            }

            state.socket.send(JSON.stringify({
                type,
                target,
                payload,
            }));
        }

        async function getOrCreatePeerConnection(remotePeer, shouldCreateOffer) {
            if (state.peers.has(remotePeer.peer_id)) {
                return state.peers.get(remotePeer.peer_id);
            }

            const connection = new RTCPeerConnection({
                iceServers: [
                    { urls: "stun:stun.l.google.com:19302" },
                    { urls: "stun:stun1.l.google.com:19302" },
                ],
            });

            if (state.localStream) {
                state.localStream.getTracks().forEach((track) => {
                    connection.addTrack(track, state.localStream);
                });
            }

            connection.onicecandidate = (event) => {
                if (event.candidate) {
                    sendSignal("ice-candidate", remotePeer.peer_id, event.candidate);
                }
            };

            connection.ontrack = (event) => {
                const audio = makeAudioPlayer(remotePeer.peer_id, remotePeer.display_name || remotePeer.peer_id);
                audio.srcObject = event.streams[0];
                reportStatus("Voice connected", "success");
            };

            connection.onconnectionstatechange = () => {
                if (["failed", "disconnected", "closed"].includes(connection.connectionState)) {
                    state.peers.delete(remotePeer.peer_id);
                    removeAudioPlayer(remotePeer.peer_id);
                }
            };

            state.peers.set(remotePeer.peer_id, connection);

            const earlyCandidates = state.waitingIceCandidates.get(remotePeer.peer_id) || [];
            for (const oneCandidate of earlyCandidates) {
                await connection.addIceCandidate(new RTCIceCandidate(oneCandidate));
            }
            state.waitingIceCandidates.delete(remotePeer.peer_id);

            if (shouldCreateOffer) {
                const offer = await connection.createOffer();
                await connection.setLocalDescription(offer);
                await sendSignal("offer", remotePeer.peer_id, offer);
            }

            return connection;
        }

        async function handleOffer(sourcePeerId, offerPayload) {
            const remotePeer = state.currentMembers.find((member) => member.peer_id === sourcePeerId) || {
                peer_id: sourcePeerId,
                display_name: sourcePeerId,
            };

            const connection = await getOrCreatePeerConnection(remotePeer, false);
            await connection.setRemoteDescription(new RTCSessionDescription(offerPayload));

            const answer = await connection.createAnswer();
            await connection.setLocalDescription(answer);
            await sendSignal("answer", sourcePeerId, answer);
        }

        async function handleAnswer(sourcePeerId, answerPayload) {
            const connection = state.peers.get(sourcePeerId);
            if (!connection) {
                return;
            }

            await connection.setRemoteDescription(new RTCSessionDescription(answerPayload));
        }

        async function handleIceCandidate(sourcePeerId, candidatePayload) {
            const connection = state.peers.get(sourcePeerId);
            if (connection) {
                await connection.addIceCandidate(new RTCIceCandidate(candidatePayload));
                return;
            }

            const savedList = state.waitingIceCandidates.get(sourcePeerId) || [];
            savedList.push(candidatePayload);
            state.waitingIceCandidates.set(sourcePeerId, savedList);
        }

        async function join() {
            const roomId = window.sharedRoom.ensureSharedRoomId(roomIdInput.value);
            const username = String(usernameInput.value || "").trim();

            if (!roomId || !username) {
                reportStatus("Enter room ID and username first", "system");
                return;
            }

            if (state.socket && state.socket.readyState === WebSocket.OPEN) {
                reportStatus("Voice already connected", "system");
                return;
            }

            roomIdInput.value = roomId;
            state.peerId = makePeerId();

            try {
                const createResponse = await fetch(`${getBackendUrl()}/rooms/create`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        display_name: username,
                        room_id: roomId,
                    }),
                });

                if (!createResponse.ok && createResponse.status !== 409) {
                    reportStatus("Voice room could not be prepared", "system");
                    return;
                }
            } catch (error) {
                reportStatus("Voice backend is not reachable", "system");
                return;
            }

            try {
                state.localStream = await navigator.mediaDevices.getUserMedia({
                    audio: true,
                    video: false,
                });
                reportStatus("Microphone ready, joining voice room...", "system");
            } catch (error) {
                reportStatus("Microphone access failed", "system");
                return;
            }

            const params = new URLSearchParams({ name: username });
            state.socket = new WebSocket(`${getSocketBaseUrl()}/voice/ws/${roomId}/${state.peerId}?${params.toString()}`);

            state.socket.onopen = () => {
                reportStatus("Connected to voice room", "success");
            };

            state.socket.onmessage = async (event) => {
                const message = JSON.parse(event.data);

                if (message.type === "welcome") {
                    const peopleAlreadyInRoom = message.existing_peers || [];
                    for (const onePeer of peopleAlreadyInRoom) {
                        await getOrCreatePeerConnection(onePeer, true);
                    }
                }

                if (message.type === "room_state") {
                    state.currentMembers = message.room.members || [];
                    renderMembers();
                }

                if (message.type === "new_peer") {
                    reportStatus("A player joined voice", "system");
                }

                if (message.type === "offer") {
                    await handleOffer(message.source, message.payload);
                }

                if (message.type === "answer") {
                    await handleAnswer(message.source, message.payload);
                }

                if (message.type === "ice-candidate") {
                    await handleIceCandidate(message.source, message.payload);
                }

                if (message.type === "peer_left") {
                    const connection = state.peers.get(message.peer_id);
                    if (connection) {
                        connection.close();
                        state.peers.delete(message.peer_id);
                    }
                    removeAudioPlayer(message.peer_id);
                }

                if (message.type === "kicked") {
                    reportStatus("You were removed from the voice room", "system");
                    leave();
                }

                if (message.type === "error") {
                    reportStatus(message.message || "Voice room error", "system");
                }
            };

            state.socket.onclose = () => {
                reportStatus("Voice disconnected", "system");
            };
        }

        function leave() {
            if (state.socket) {
                state.socket.close();
                state.socket = null;
            }

            state.peers.forEach((connection) => {
                connection.close();
            });
            state.peers.clear();
            state.waitingIceCandidates.clear();

            state.remoteAudios.forEach((audio) => {
                audio.srcObject = null;
            });
            state.remoteAudios.clear();
            audiosNode.innerHTML = "";

            if (state.localStream) {
                state.localStream.getTracks().forEach((track) => track.stop());
                state.localStream = null;
            }

            state.currentMembers = [];
            renderMembers();
            reportStatus("Voice disconnected", "system");
        }

        renderMembers();

        return {
            join,
            leave,
        };
    }

    window.voiceRoom = {
        createVoiceRoomClient,
    };
})();
