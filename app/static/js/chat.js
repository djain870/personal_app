const input = document.getElementById("userInput");
const box = document.getElementById("chatBox");

function addBubble(text, sender) {
    const side = sender === "user" ? "user" : "bot";
    box.innerHTML += `<div class="msg ${side}">${text}</div>`;
    box.scrollTop = box.scrollHeight;
}

async function sendMessage() {
    const message = input.value;
    if (!message) return;

    addBubble(message, "user");
    input.value = "";

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        });
        const data = await res.json();
        addBubble(data.reply, "bot");
    } catch (err) {
        addBubble("⚠️ Error: Could not reach the brain.", "bot");
    }
}

input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

window.addEventListener("load", async () => {
    try {
        const res = await fetch("/chat-history");
        const data = await res.json();
        data.forEach(chat => {
            addBubble(chat.user_message, "user");
            addBubble(chat.bot_reply, "bot");
        });
    } catch (err) {
        console.log("No history found.");
    }
});

function clearChat() {
    if (confirm("Are you sure you want to wipe the conversation?")) {
        fetch("/clear-chat").then(() => location.reload());
    }
}
