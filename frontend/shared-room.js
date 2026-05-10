(function () {
    const ROOM_ID_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    const DEFAULT_PEER_APP_URL = "http://127.0.0.1:8501";

    function generateSharedRoomId(length = 6) {
        const array = new Uint32Array(length);
        window.crypto.getRandomValues(array);

        let roomId = "";
        for (let index = 0; index < length; index += 1) {
            roomId += ROOM_ID_CHARS[array[index] % ROOM_ID_CHARS.length];
        }
        return roomId;
    }

    function ensureSharedRoomId(value) {
        const normalized = String(value || "")
            .toUpperCase()
            .replace(/[^A-Z0-9]/g, "");

        if (normalized) {
            return normalized;
        }

        return generateSharedRoomId();
    }

    function buildPeerTalkingJoinUrl(roomId, baseUrl = DEFAULT_PEER_APP_URL) {
        const url = new URL(baseUrl);
        url.searchParams.set("room_id", ensureSharedRoomId(roomId));
        return url.toString();
    }

    window.sharedRoom = {
        buildPeerTalkingJoinUrl,
        ensureSharedRoomId,
        generateSharedRoomId,
    };
})();
