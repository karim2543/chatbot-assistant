const chatBox = document.getElementById("chat-box");
const input = document.getElementById("msg-input");
const sendBtn = document.getElementById("send-btn");
const voiceBtn = document.getElementById("voice-btn");
const newConversationBtn = document.getElementById("new-conversation-btn");
const conversationList = document.getElementById("conversation-list");
const conversationStatus = document.getElementById("conversation-status");

let activeConversationId = null;
let lastMessageId = 0;
let displayedMessageIds = new Set();
let conversationLoadToken = 0;
let sendInProgress = false;

function appendMessage(role, text, id = null) {
    if (id !== null && displayedMessageIds.has(id)) return;

    if (role === "assistant") {
        removeTypingIndicator();
    }

    const div = document.createElement("div");
    div.classList.add("message", role);

    div.innerHTML = text
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");

    chatBox.appendChild(div);

    const indicator = document.getElementById("typing-indicator");
    if (indicator) {
        chatBox.appendChild(indicator);
    }

    chatBox.scrollTop = chatBox.scrollHeight;

    if (id !== null) {
        displayedMessageIds.add(id);
        if (id > lastMessageId) {
            lastMessageId = id;
        }
    }
}

function clearMessages() {
    chatBox.innerHTML = "";
    displayedMessageIds = new Set();
    lastMessageId = 0;
    removeTypingIndicator();
}

function renderConversationList(conversations) {
    conversationList.innerHTML = "";

    conversations.forEach(conversation => {
        const row = document.createElement("div");
        row.className = "conversation-row";

        const button = document.createElement("button");
        button.type = "button";
        button.className = "conversation-item flex-grow-1";
        button.dataset.conversationId = conversation.id;
        button.innerHTML = `
            <span class="conversation-title">${escapeHtml(conversation.title)}</span>
        `;
        button.addEventListener("click", () => {
            openConversation(conversation.id);
        });

        const deleteButton = document.createElement("button");
        deleteButton.type = "button";
        deleteButton.className = "btn btn-link delete-conversation-btn";
        deleteButton.title = "Delete conversation";
        deleteButton.setAttribute("aria-label", `Delete ${conversation.title}`);
        deleteButton.innerHTML = '<i class="bi bi-trash"></i>';
        deleteButton.addEventListener("click", event => {
            event.stopPropagation();
            deleteConversation(conversation.id);
        });

        row.appendChild(button);
        row.appendChild(deleteButton);
        conversationList.appendChild(row);
    });

    updateActiveConversation();
}

function updateActiveConversation() {
    document.querySelectorAll(".conversation-item").forEach(button => {
        button.classList.toggle(
            "active",
            Number(button.dataset.conversationId) === activeConversationId
        );
    });
}

function escapeHtml(text) {
    const element = document.createElement("div");
    element.textContent = text || "";
    return element.innerHTML;
}

async function loadConversations(selectFirst = true) {
    const response = await fetch("/chatbot/conversations");
    if (!response.ok) {
        throw new Error("Unable to load conversations.");
    }

    const conversations = await response.json();
    renderConversationList(conversations);
    conversationStatus.textContent = conversations.length
        ? `${conversations.length} conversation${conversations.length > 1 ? "s" : ""}`
        : "No conversations";

    if (selectFirst && conversations.length && activeConversationId === null) {
        await openConversation(conversations[0].id);
    }

    return conversations;
}

async function createConversation() {
    newConversationBtn.disabled = true;
    try {
        const response = await fetch("/chatbot/conversations", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({title: "New conversation"})
        });
        if (!response.ok) {
            throw new Error("Unable to create the conversation.");
        }

        const conversation = await response.json();
        await loadConversations(false);
        await openConversation(conversation.id);
    } catch (error) {
        console.error(error);
        conversationStatus.textContent = "Error creating conversation";
    } finally {
        newConversationBtn.disabled = false;
    }
}

async function deleteConversation(conversationId) {
    if (!window.confirm("Delete this conversation and all its messages?")) return;

    try {
        const response = await fetch(
            `/chatbot/conversations/${conversationId}`,
            {method: "DELETE"}
        );
        if (!response.ok) {
            throw new Error("Unable to delete the conversation.");
        }

        const wasActive = activeConversationId === Number(conversationId);
        if (wasActive) {
            conversationLoadToken++;
            activeConversationId = null;
            clearMessages();
        }

        const conversations = await loadConversations(false);
        if (wasActive && conversations.length) {
            await openConversation(conversations[0].id);
        } else if (wasActive) {
            conversationStatus.textContent = "No conversations";
        }
    } catch (error) {
        console.error(error);
        conversationStatus.textContent = error.message;
    }
}

async function openConversation(conversationId) {
    const loadToken = ++conversationLoadToken;
    activeConversationId = Number(conversationId);
    lastMessageId = 0;
    displayedMessageIds = new Set();
    removeTypingIndicator();
    updateActiveConversation();
    chatBox.innerHTML = "";

    try {
        const response = await fetch(
            `/chatbot/conversations/${activeConversationId}`
        );
        if (!response.ok) {
            throw new Error("Unable to load the conversation.");
        }

        const data = await response.json();
        if (loadToken !== conversationLoadToken ||
            activeConversationId !== Number(conversationId)) {
            return;
        }

        data.messages.forEach(message => {
            appendMessage(
                message.role,
                message.content,
                message.id
            );
        });
        conversationStatus.textContent = data.conversation.title;
    } catch (error) {
        if (loadToken === conversationLoadToken) {
            console.error(error);
            conversationStatus.textContent = "Loading error";
        }
    }
}

async function checkNewMessages() {
    if (activeConversationId === null) return;
    const conversationId = activeConversationId;
    const loadToken = conversationLoadToken;

    try {
        const response = await fetch(
            `/chatbot/new_messages?conversation_id=${conversationId}&last_id=${lastMessageId}`
        );
        if (!response.ok) {
            throw new Error("Unable to load new messages.");
        }

        const messages = await response.json();
        if (loadToken !== conversationLoadToken ||
            activeConversationId !== conversationId) {
            return;
        }

        messages.forEach(message => {
            appendMessage(
                message.role,
                message.content,
                message.id
            );
        });
    } catch (error) {
        if (loadToken === conversationLoadToken &&
            activeConversationId === conversationId) {
            console.error("Polling error:", error);
        }
    }
}

function showTypingIndicator() {
    let indicator = document.getElementById("typing-indicator");

    if (indicator) {
        chatBox.appendChild(indicator);
    } else {
        indicator = document.createElement("div");
        indicator.classList.add("message", "assistant", "typing-indicator");
        indicator.id = "typing-indicator";
        indicator.innerHTML = '<span></span><span></span><span></span> Assistant écrit...';
        chatBox.appendChild(indicator);
    }

    chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTypingIndicator() {
    const ind = document.getElementById("typing-indicator");
    if (ind) ind.remove();
}

async function sendMessage(text) {
    if (sendInProgress) return;
    sendInProgress = true;
    sendBtn.disabled = true;
    let conversationId = activeConversationId;
    let loadToken = conversationLoadToken;

    try {
        if (activeConversationId === null) {
            await createConversation();
            if (activeConversationId === null) return;
        }

        conversationId = activeConversationId;
        loadToken = conversationLoadToken;
        showTypingIndicator();

        const response = await fetch(
            `/chatbot/conversations/${conversationId}/messages`,
            {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({text})
            }
        );
        if (!response.ok) {
            let detail = "Unable to send the message.";
            try {
                const errorData = await response.json();
                if (typeof errorData.error === "string" && errorData.error.trim()) {
                    detail = errorData.error;
                }
            } catch (parseError) {
                console.error("Error playing the response:", parseError);
            }
            throw new Error(detail);
        }

        const data = await response.json();
        if (loadToken !== conversationLoadToken ||
            activeConversationId !== conversationId) {
            return;
        }

        appendMessage(
            data.user_message.role,
            data.user_message.content,
            data.user_message.id
        );
        appendMessage(
            data.assistant_message.role,
            data.assistant_message.content,
            data.assistant_message.id
        );
    } catch (error) {
        console.error(error);
        if (loadToken === conversationLoadToken &&
            activeConversationId === conversationId) {
            removeTypingIndicator();
            conversationStatus.textContent = error.message;
        }
    } finally {
        sendInProgress = false;
        sendBtn.disabled = false;
    }
}

newConversationBtn.onclick = createConversation;

sendBtn.onclick = () => {
    const text = input.value.trim();

    if (text) {
        sendMessage(text);
        input.value = "";
    }
};

let recognition;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = function(event) {
        const transcript = event.results[0][0].transcript.trim();

        if (transcript) {
            sendMessage(transcript);
        }
    };

    recognition.onerror = function(event) {
        console.error("Error in voice recognition:", event.error);
    };
} else {
    voiceBtn.disabled = true;
    voiceBtn.innerText = "🎤 Not supported";
}

voiceBtn.onclick = () => {
    if (recognition) recognition.start();
};

input.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendBtn.click();
});

loadConversations().catch(error => {
    console.error(error);
    conversationStatus.textContent = "Loading error";
});

setInterval(checkNewMessages, 4000);
