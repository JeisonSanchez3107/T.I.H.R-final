const chatForm = document.getElementById('chatForm');
        const loadingMessage = document.getElementById('loadingMessage');
        const messageInput = document.getElementById('messageInput');
        const submitButton = chatForm.querySelector('button[type="submit"]');
        const chatBox = document.getElementById('chatBox');
        // const openChatbotButton ha sido eliminado
        const chatContainer = document.getElementById('chatContainer');

        function scrollToBottom() {
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        // Se elimina el evento de clic del botón de despliegue

        chatForm.addEventListener('submit', function() {
            loadingMessage.style.display = 'block';
            messageInput.disabled = true;
            submitButton.disabled = true;
            scrollToBottom();
        });

        window.onload = function() {
            // El chat container ya está visible por defecto
            loadingMessage.style.display = 'none';
            messageInput.disabled = false;
            submitButton.disabled = false;
            scrollToBottom();
            messageInput.focus(); // Enfoca el input directamente al cargar
        };