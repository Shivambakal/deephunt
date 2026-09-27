// ruleid: deephunt-idor-fetch
const params = new URLSearchParams(window.location.search);
const uid = params.get("user_id");
fetch("/api/users/" + uid).then(r => r.json());

// ok: deephunt-idor-fetch
const safe = encodeURIComponent(uid);
fetch("/api/users/" + safe);
