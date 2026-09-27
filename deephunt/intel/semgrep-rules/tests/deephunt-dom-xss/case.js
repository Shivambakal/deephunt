// ruleid: deephunt-dom-xss
el.innerHTML = location.hash.slice(1);

// ok: deephunt-dom-xss
el.textContent = location.hash.slice(1);

// ok: deephunt-dom-xss
el.innerHTML = DOMPurify.sanitize(location.hash);
