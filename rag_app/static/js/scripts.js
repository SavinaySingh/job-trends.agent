function sendMessage() {
  var textInput = document.getElementById("textInput").value;
  var fileInput = document.getElementById("fileInput").files[0];
  document.getElementById("cameraIcon").src = "/static/icons/camera_icon.svg";
  var formData = new FormData();

  if (fileInput) {
    formData.append("file", fileInput);
  }
  if (textInput.trim() !== "") {
    formData.append("text", textInput);
    displayUserMessage(textInput); // Display user's query first
  }

  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/process_request/", true);
  xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));

  xhr.onload = function () {
    if (xhr.status === 200) {
      var response = JSON.parse(xhr.responseText).response;
      displayBotResponse(response);
    } else {
      console.error("Error receiving data:", xhr.statusText);
    }
  };

  xhr.onerror = function () {
    console.error("Error receiving data:", xhr.statusText);
  };

  xhr.send(formData);

  // Clear input fields after sending
  document.getElementById("textInput").value = "";
  document.getElementById("fileInput").value = "";
}

function displayBotResponse(response) {
  var div = document.createElement("div");
  div.className = "message bot-message";
  div.innerHTML = response; // Supports HTML formatting
  document.getElementById("chatBox").appendChild(div);
  scrollChatToBottom();
}

function displayUserMessage(text) {
  var div = document.createElement("div");
  div.className = "message user-message";
  div.innerText = text;
  document.getElementById("chatBox").appendChild(div);
  scrollChatToBottom();
}

function updateIcon() {
  document.getElementById("cameraIcon").src = "static/icons/image_uploaded.svg";
}

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.getElementById('textInput').addEventListener('keydown', function(event) {
  if (event.key === 'Enter') {
    event.preventDefault();
    sendMessage();
  }
});

// Optional: Automatically scroll chat to bottom after a new message
function scrollChatToBottom() {
  var chatBox = document.getElementById("chatBox");
  chatBox.scrollTop = chatBox.scrollHeight;
}
