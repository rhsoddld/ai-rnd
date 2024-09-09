const chatForm = document.getElementById('chat-form');
const chatBox = document.getElementById('chat-box');
const argsContainer = document.getElementById('args-container');
const argsContent = document.getElementById('args-content');
const executeButton = document.getElementById('execute-button');
const resultContainer = document.getElementById('result-container');
const functionResponseContent = document.getElementById('function-response-content');

// Chat form submission event listener
chatForm.addEventListener('submit', function(event) {
    event.preventDefault();

    const userInput = document.getElementById('user-input');
    const message = userInput.value;

    fetch('/', {
        method: 'POST',
        body: new FormData(chatForm)
    })
    .then(response => response.json())
    .then(data => {
        const userMessage = document.createElement('div');
        userMessage.className = 'message user';
        userMessage.textContent = `user: ${message}`;
        chatBox.appendChild(userMessage);

        const assistantMessage = document.createElement('div');
        assistantMessage.className = 'message assistant';
        assistantMessage.textContent = `assistant: ${data.response}`;
        chatBox.appendChild(assistantMessage);

        chatForm.reset();

        if (data.args) {
            argsContent.textContent = data.args;
            argsContainer.style.display = 'block';
            executeButton.style.display = 'inline';
        } else {
            argsContainer.style.display = 'none';
            executeButton.style.display = 'none';
        }
    });
});

// PDF Upload form submission event listener
const uploadForm = document.getElementById('upload-form');
const uploadStatus = document.getElementById('upload-status');

uploadForm.addEventListener('submit', function(event) {
    event.preventDefault();

    const formData = new FormData(uploadForm);
    
    console.log(formData)

    fetch('/pdf', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "Successfully Uploaded") {
            uploadStatus.textContent = `File "${data.filename}" uploaded successfully.`;
            uploadStatus.style.color = 'green';
        } else {
            uploadStatus.textContent = `Upload failed: ${data.error}`;
            uploadStatus.style.color = 'red';
        }
    })
    .catch(error => {
        uploadStatus.textContent = `An error occurred: ${error.message}`;
        uploadStatus.style.color = 'red';
    });
});

// Command execution button click event listener
document.getElementById('execute-button').addEventListener('click', function() {
    const args = argsContent.textContent;
    const selectedServer = document.getElementById('server-selection').value;
    const selectedModel = document.getElementById('model-selection').value;  // モデル選択を取得

    fetch('/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: args, server_selection: selectedServer, selected_model: selectedModel })
    })
    .then(response => response.json())
    .then(data => {
        functionResponseContent.innerHTML = data.function_response.replace(/\n/g, '<br>');
        resultContainer.style.display = 'block';

        // final_responseをチャットボックスに追加
        const finalMessage = document.createElement('div');
        finalMessage.className = 'message assistant';
        finalMessage.innerHTML = `assistant: ${data.final_response.replace(/\n/g, '<br>')}`;
        chatBox.appendChild(finalMessage);
    });
});

// Clear chat button click event listener
document.getElementById('clear-button').addEventListener('click', function() {
    fetch('/clear_chat', { method: 'POST' })
    .then(response => response.json())
    .then(() => {
        chatBox.innerHTML = '';
        argsContainer.style.display = 'none';
        resultContainer.style.display = 'none';
        executeButton.style.display = 'none';
    });
});  

function selectPrompt(prompt) {
    // 選択されたpromptの値をhidden inputに設定
    document.getElementById('selected-prompt').value = prompt;

    // 全てのpromptボックスから.activeクラスを削除
    const promptBoxes = document.querySelectorAll('.prompt-box');
    promptBoxes.forEach(box => box.classList.remove('active'));

    // クリックされたボックスに.activeクラスを追加
    document.getElementById(prompt).classList.add('active');
}

function selectServer() {
    const serverSelection = document.getElementById('server-selection').value;
    document.getElementById('selected-server').value = serverSelection;
}

function selectModel() {
    const selectedModel = document.getElementById('model-selection').value;
    document.getElementById('selected-model').value = selectedModel;
}
