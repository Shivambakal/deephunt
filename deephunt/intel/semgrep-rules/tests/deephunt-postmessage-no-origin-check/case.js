// ruleid: deephunt-postmessage-no-origin-check
window.addEventListener("message", function(e) {
  document.getElementById("out").innerHTML = e.data.html;
});
