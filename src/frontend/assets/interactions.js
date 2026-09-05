// Small UX enhancements layered on top of the Dash-rendered chat UI.
// Dash serves everything in assets/ automatically and re-mounts the layout
// in place, so these listeners are attached once via polling for the
// (stable-id) elements rather than depending on load-order timing.
(function () {
    var attachedEnterToSend = false;
    var attachedAutoScroll = false;

    function attach() {
        if (!attachedEnterToSend) {
            document.addEventListener("keydown", function (event) {
                if (
                    event.target &&
                    event.target.id === "message-input" &&
                    event.key === "Enter" &&
                    !event.shiftKey
                ) {
                    event.preventDefault();
                    var sendButton = document.getElementById("send");
                    if (sendButton && !sendButton.disabled) {
                        sendButton.click();
                    }
                }
            });
            attachedEnterToSend = true;
        }

        var transcript = document.getElementById("transcript");
        if (transcript && !attachedAutoScroll) {
            var observer = new MutationObserver(function () {
                transcript.scrollTop = transcript.scrollHeight;
            });
            observer.observe(transcript, { childList: true, subtree: true });
            attachedAutoScroll = true;
        }

        if (attachedEnterToSend && attachedAutoScroll) {
            clearInterval(poll);
        }
    }

    var poll = setInterval(attach, 200);
    attach();
})();
