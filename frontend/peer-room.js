(function () {
    const DEFAULT_PEER_APP_URL = "http://127.0.0.1:8501";

    function buildPeerRoomUrl(roomId, username, baseUrl = DEFAULT_PEER_APP_URL) {
        const safeRoomId = window.sharedRoom.ensureSharedRoomId(roomId);
        const safeUsername = String(username || "").trim();
        const url = new URL(baseUrl);

        url.searchParams.set("room_id", safeRoomId);
        if (safeUsername) {
            url.searchParams.set("name", safeUsername);
        }

        return url.toString();
    }

    function syncPeerRoomControls(options) {
        const {
            roomIdInput,
            usernameInput,
            roomIdText,
            linkNode,
        } = options;

        const roomId = window.sharedRoom.ensureSharedRoomId(roomIdInput.value);
        roomIdInput.value = roomId;
        roomIdText.textContent = roomId;

        const peerUrl = buildPeerRoomUrl(roomId, usernameInput.value);
        linkNode.href = peerUrl;
        linkNode.textContent = peerUrl;

        return { roomId, peerUrl };
    }

    async function copyPeerRoomId(roomId) {
        const text = `Peer room ID: ${roomId}`;
        await navigator.clipboard.writeText(text);
        return text;
    }

    function openPeerRoom(peerUrl) {
        window.open(peerUrl, "_blank", "noopener,noreferrer");
    }

    window.peerRoom = {
        buildPeerRoomUrl,
        copyPeerRoomId,
        openPeerRoom,
        syncPeerRoomControls,
    };
})();
