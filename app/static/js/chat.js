const input = document.getElementById("userInput");
const box = document.getElementById("chatBox");
const conversationList = document.getElementById("conversationList");
const newChatBtn = document.getElementById("newChatBtn");
const activeConversationTitle = document.getElementById("activeConversationTitle");

function addBubble(text, sender) {
    const side = sender === "user" ? "user" : "bot";
    const bubble = document.createElement("div");
    bubble.className = `msg ${side}`;
    bubble.textContent = text;
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
}

let activeConversationId = null;
let conversations = [];

function setActiveTitle(title) {
    activeConversationTitle.textContent = title || "New conversation";
}

function renderConversations() {
    conversationList.innerHTML = "";

    if (!conversations.length) {
        const empty = document.createElement("div");
        empty.className = "conversation-empty";
        empty.textContent = "No saved conversations yet";
        conversationList.appendChild(empty);
        return;
    }

    conversations.forEach((conversation) => {
        const row = document.createElement("div");
        row.className = "conversation-item";
        if (conversation.id === activeConversationId) {
            row.classList.add("active");
        }

        const titleButton = document.createElement("button");
        titleButton.type = "button";
        titleButton.className = "conversation-title";
        titleButton.textContent = conversation.title;
        titleButton.addEventListener("click", () => loadConversation(conversation.id));

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "conversation-delete";
        deleteButton.textContent = "Delete";
        deleteButton.title = "Delete conversation";
        deleteButton.addEventListener("click", (event) => {
            event.stopPropagation();
            deleteConversation(conversation.id);
        });

        row.appendChild(titleButton);
        row.appendChild(deleteButton);
        conversationList.appendChild(row);
    });
}

async function loadConversations() {
    const res = await fetch("/chat-conversations");
    conversations = await res.json();
    renderConversations();
}

async function loadConversation(conversationId) {
    activeConversationId = conversationId;
    const conversation = conversations.find(item => item.id === conversationId);
    setActiveTitle(conversation ? conversation.title : "Saved conversation");
    renderConversations();

    box.innerHTML = "";
    const res = await fetch(`/chat-history?conversation_id=${conversationId}`);
    const data = await res.json();
    data.forEach(chat => {
        addBubble(chat.user_message, "user");
        addBubble(chat.bot_reply, "bot");
    });
}

async function startNewConversation() {
    activeConversationId = null;
    setActiveTitle("New conversation");
    box.innerHTML = "";
    renderConversations();
    input.focus();
}

async function deleteConversation(conversationId) {
    const conversation = conversations.find(item => item.id === conversationId);
    const title = conversation ? conversation.title : "this conversation";

    if (!confirm(`Delete "${title}"? This cannot be undone.`)) {
        return;
    }

    await fetch(`/chat-conversations/${conversationId}`, {
        method: "DELETE"
    });

    conversations = conversations.filter(item => item.id !== conversationId);

    if (activeConversationId === conversationId) {
        if (conversations.length) {
            await loadConversation(conversations[0].id);
        } else {
            startNewConversation();
        }
        return;
    }

    renderConversations();
}

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    addBubble(message, "user");
    input.value = "";

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                conversation_id: activeConversationId
            })
        });
        const data = await res.json();
        addBubble(data.reply, "bot");

        if (data.conversation_id) {
            activeConversationId = data.conversation_id;

            const existing = conversations.find(item => item.id === data.conversation_id);
            if (existing) {
                existing.title = data.conversation_title || existing.title;
            } else {
                conversations.unshift({
                    id: data.conversation_id,
                    title: data.conversation_title || "Saved conversation"
                });
            }

            setActiveTitle(data.conversation_title);
            renderConversations();
        }
    } catch (err) {
        addBubble("Error: Could not reach the brain.", "bot");
    }
}

input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendMessage();
});

window.addEventListener("load", async () => {
    try {
        await loadConversations();
        if (conversations.length) {
            await loadConversation(conversations[0].id);
        } else {
            startNewConversation();
        }
    } catch (err) {
        console.log("No conversations found.");
    }
});

newChatBtn.addEventListener("click", startNewConversation);

async function clearChat() {
    if (!activeConversationId) {
        box.innerHTML = "";
        return;
    }

    if (confirm("Clear messages in this conversation?")) {
        await fetch(`/clear-chat?conversation_id=${activeConversationId}`);
        box.innerHTML = "";
    }
}
