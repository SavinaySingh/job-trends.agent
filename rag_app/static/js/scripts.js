// Global variables
let isLoading = false;

// Theme toggle functionality
function toggleTheme() {
  const body = document.body;
  const toggleBtn = document.getElementById("toggleThemeBtn");
  const icon = toggleBtn.querySelector('i');

  body.classList.toggle("dark-mode");
  const isDark = body.classList.contains("dark-mode");

  // Store preference
  localStorage.setItem("darkMode", isDark);

  // Update button
  if (isDark) {
    icon.className = "fas fa-sun";
    toggleBtn.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
  } else {
    icon.className = "fas fa-moon";
    toggleBtn.innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
  }
}

// Load theme preference
window.addEventListener('load', () => {
  const prefersDark = localStorage.getItem("darkMode") === "true";
  const toggleBtn = document.getElementById("toggleThemeBtn");

  if (prefersDark) {
    document.body.classList.add("dark-mode");
    toggleBtn.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
  }
});

// Auto-resize textarea
const textInput = document.getElementById('textInput');
textInput.addEventListener('input', function () {
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Send message on Enter (but allow Shift+Enter for new lines)
textInput.addEventListener('keydown', function (event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    if (!isLoading) {
      sendMessage();
    }
  }
});

// Send message function
function sendMessage() {
  if (isLoading) return;

  const textInput = document.getElementById("textInput");
  const fileInput = document.getElementById("fileInput");
  const sendBtn = document.getElementById("sendBtn");
  const text = textInput.value.trim();
  const file = fileInput.files[0];

  if (!text && !file) return;

  // Set loading state
  isLoading = true;
  sendBtn.disabled = true;
  sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span class="loading-dots">Thinking</span>';

  // Display user message
  if (text) {
    displayUserMessage(text);
  }

  // Prepare form data
  const formData = new FormData();
  if (file) formData.append("file", file);
  if (text) formData.append("text", text);

  fetch("/process_request/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      displayBotMessage(data.response, data.context_docs || [], text);  // pass user query here!
    })
    .catch(error => {
      console.error("Error:", error);
      displayBotResponse("Sorry, I encountered an error. Please try again.");
    })
    .finally(() => {
      isLoading = false;
      sendBtn.disabled = false;
      sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> <span>Send</span>';

      textInput.value = "";
      textInput.style.height = 'auto';
      fileInput.value = "";
      resetCameraIcon();
    });
}
// Display user message
function displayUserMessage(text) {
  const div = document.createElement("div");
  div.className = "message user-message";
  div.textContent = text;
  document.getElementById("chatBox").appendChild(div);
  scrollChatToBottom();
}

// Display bot response
function displayBotResponse(response) {
  const div = document.createElement("div");
  div.className = "message bot-message";
  div.innerHTML = response;
  document.getElementById("chatBox").appendChild(div);
  scrollChatToBottom();
}

// Update file upload icon
function updateIcon() {
  const icon = document.getElementById("cameraIcon");
  icon.className = "fas fa-check file-uploaded";
}

// Reset camera icon
function resetCameraIcon() {
  const icon = document.getElementById("cameraIcon");
  icon.className = "fas fa-camera";
}

// Scroll chat to bottom
function scrollChatToBottom() {
  const chatBox = document.getElementById("chatBox");
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Get CSRF cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

let botMessageCount = 0;

function displayBotMessage(responseText, contextDocs, userQuery) {
  botMessageCount++;

  const chatBox = document.getElementById("chatBox");

  const messageEl = document.createElement("div");
  messageEl.classList.add("message", "bot-message");

  const contentEl = document.createElement("div");
  contentEl.classList.add("bot-reply-content");

  const textEl = document.createElement("span");
  textEl.classList.add("bot-text");
  textEl.innerHTML = responseText;

  const tooltipEl = document.createElement("span");
  tooltipEl.classList.add("info-tooltip");
  tooltipEl.setAttribute("data-bs-toggle", "tooltip");
  tooltipEl.setAttribute("data-bs-placement", "top");
  tooltipEl.setAttribute("title", contextDocs.join("\n---\n"));

  const icon = document.createElement("i");
  icon.classList.add("fas", "fa-info-circle", "text-primary", "ms-2");
  tooltipEl.appendChild(icon);

  contentEl.appendChild(textEl);
  contentEl.appendChild(tooltipEl);

  // ✅ Add feedback buttons if it's a real reply
  if (userQuery && responseText) {
    const feedbackDiv = document.createElement("div");
    feedbackDiv.classList.add("feedback-buttons", "mt-2");

    const thumbsUp = document.createElement("button");
    thumbsUp.classList.add("btn", "btn-sm", "btn-outline-success", "me-2");
    thumbsUp.title = "Thumbs Up";
    thumbsUp.innerHTML = '<i class="fas fa-thumbs-up"></i>';
    thumbsUp.onclick = () => sendFeedback(userQuery, contextDocs, responseText, 1, feedbackDiv);

    const thumbsDown = document.createElement("button");
    thumbsDown.classList.add("btn", "btn-sm", "btn-outline-danger");
    thumbsDown.title = "Thumbs Down";
    thumbsDown.innerHTML = '<i class="fas fa-thumbs-down"></i>';
    thumbsDown.onclick = () => sendFeedback(userQuery, contextDocs, responseText, 0, feedbackDiv);

    feedbackDiv.appendChild(thumbsUp);
    feedbackDiv.appendChild(thumbsDown);
    contentEl.appendChild(feedbackDiv);
  }

  messageEl.appendChild(contentEl);
  chatBox.appendChild(messageEl);

  // Initialize Bootstrap tooltip
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltips.forEach(t => new bootstrap.Tooltip(t));

  scrollChatToBottom();
}

// Function to send feedback
function sendFeedback(userQuery, retrievedDocs, generatedResponse, feedbackRating, feedbackContainer) {
  const feedbackData = {
    timestamp: new Date().toISOString(),
    query: userQuery,
    retrieved_docs: retrievedDocs,
    generated_response: generatedResponse,
    feedback_rating: feedbackRating
  };

  fetch("/log_feedback/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify(feedbackData)
  })
    .then(res => {
      if (res.ok) {
        if (feedbackContainer) {
          feedbackContainer.innerHTML = `<div class="text-success small"><i class="fas fa-check-circle me-1"></i>Thanks for your feedback!</div>`;
        }
      } else {
        alert("⚠️ Failed to send feedback.");
      }
    })
    .catch(() => alert("❌ Error sending feedback."));
}