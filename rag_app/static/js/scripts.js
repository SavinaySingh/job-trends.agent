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

  // Send request
  fetch("/process_request/", {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      displayBotResponse(data.response);
    })
    .catch(error => {
      console.error("Error:", error);
      displayBotResponse("Sorry, I encountered an error. Please try again.");
    })
    .finally(() => {
      // Reset loading state
      isLoading = false;
      sendBtn.disabled = false;
      sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i> <span>Send</span>';

      // Clear inputs
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

// Document upload functionality
document.getElementById("uploadForm").addEventListener("submit", function (e) {
  e.preventDefault();

  const fileInput = document.getElementById("docFileInput");
  const uploadBtn = document.querySelector("#uploadForm .upload-btn");

  if (!fileInput.files.length) {
    alert("Please select a file to upload.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  // Disable button and show loading animation
  uploadBtn.disabled = true;
  uploadBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Uploading...`;

  fetch("{% url 'upload_file' %}", {
    method: "POST",
    headers: {
      "X-CSRFToken": "{{ csrf_token }}",
    },
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      const statusDiv = document.getElementById("uploadStatus");
      if (data.message) {
        statusDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
      } else if (data.error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
      }
    })
    .catch((error) => {
      document.getElementById("uploadStatus").innerHTML =
        `<div class="alert alert-danger">Upload failed: ${error}</div>`;
    })
    .finally(() => {
      // Re-enable button and reset text
      uploadBtn.disabled = false;
      uploadBtn.innerHTML = `<i class="fas fa-upload"></i> Upload Document`;
      fileInput.value = ""; // Clear file input
    });
});