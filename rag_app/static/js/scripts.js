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

  // Send data asynchronously through AJAX
  var xhr = new XMLHttpRequest();
  xhr.open("POST", "/process_request/", true);

  // Include CSRF token in the request header
  xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));

  xhr.onload = function () {
    if (xhr.status === 200) {
      var response = JSON.parse(xhr.responseText).response; // Extract the value from the response JSON
      displayBotResponse(response);
    } else {
      console.error("Error receiving data:", xhr.statusText);
    }
  };
  xhr.onerror = function () {
    console.error("Error receiving data:", xhr.statusText);
  };
  xhr.send(formData);

  // Clear input fields
  document.getElementById("textInput").value = "";
  document.getElementById("fileInput").value = "";
}

function displayBotResponse(response) {
  var div = document.createElement("div");
  div.className = "message bot-message";
  div.innerHTML = response; // Use innerHTML to handle HTML content
  document.getElementById("chatBox").appendChild(div);
}

function displayUserMessage(text) {
  var div = document.createElement("div");
  div.className = "message user-message";
  div.innerText = text;
  document.getElementById("chatBox").appendChild(div);
}

function updateIcon() {
  document.getElementById("cameraIcon").src = "static/icons/image_uploaded.svg";
}

// Function to get CSRF cookie value
function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = cookies[i].trim();
      // Check if the cookie name matches the parameter
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
