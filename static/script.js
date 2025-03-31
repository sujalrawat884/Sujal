document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM is fully loaded!");

    const yearDropdown = document.getElementById("year");
    const subjectDropdown = document.getElementById("subject");
    const unitDropdown = document.getElementById("unit");

    if (!yearDropdown || !subjectDropdown || !unitDropdown) {
        console.error("❌ Dropdown not found!");
        return;
    }

    console.log("✅ Dropdowns found!");

    document.querySelector('form').addEventListener('submit', function(e) {
        const year = document.getElementById('year').value;
        const subject = document.getElementById('subject').value;
        const unit = document.getElementById('unit').value;
        
        if (!year || !subject || !unit) {
            e.preventDefault();
            alert('Please select all fields (Year, Subject, and Unit) before submitting.');
            return false;
        }
    });

    function updateSubjects(selectedYear) {
        subjectDropdown.innerHTML = "<option value=''>Select Subject</option>"; // Reset
        unitDropdown.innerHTML = "<option value=''>Select Unit</option>"; // Reset unit as well
        
        // Fetch subjects for the selected year
        fetch(`/get_subjects_by_year/${selectedYear}`)
            .then(response => response.json())
            .then(subjects => {
                if (subjects && subjects.length > 0) {
                    subjects.forEach(subject => {
                        const option = document.createElement("option");
                        option.value = subject;
                        option.textContent = subject;
                        subjectDropdown.appendChild(option);
                    });
                    console.log("📌 Subjects updated for:", selectedYear);
                } else {
                    console.warn("⚠️ No subjects found for:", selectedYear);
                }
            })
            .catch(error => console.error("Error fetching subjects:", error));
    }
    
    function updateUnits(selectedSubject) {
        unitDropdown.innerHTML = "<option value=''>Select Unit</option>"; // Reset
        
        // Fetch units for the selected subject
        fetch(`/get_units/${selectedSubject}`)
            .then(response => response.json())
            .then(units => {
                if (units && Object.keys(units).length > 0) {
                    Object.entries(units).forEach(([unitCode, topic]) => {
                        const option = document.createElement("option");
                        // Store the unit code as the value
                        option.value = unitCode;
                        // Display "U1: Topic Name" format in the dropdown
                        option.textContent = `${unitCode}: ${topic}`;
                        unitDropdown.appendChild(option);
                    });
                    console.log("📚 Units updated for:", selectedSubject);
                } else {
                    console.warn("⚠️ No units found for:", selectedSubject);
                }
            })
            .catch(error => console.error("Error fetching units:", error));
    }

    // Listen for year selection change
    yearDropdown.addEventListener("change", function () {
        console.log("✅ Year changed:", this.value);
        updateSubjects(this.value);
    });
    
    // Listen for subject selection change
    subjectDropdown.addEventListener("change", function () {
        console.log("✅ Subject changed:", this.value);
        updateUnits(this.value);
    });

    // 🚀 Auto-trigger subject update if year is pre-selected
    if (yearDropdown.value) {
        updateSubjects(yearDropdown.value);
    }
});

// Chat functionality
document.getElementById("send-btn").addEventListener("click", function() {
    sendMessage();
});

document.getElementById("chat-input").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});

function sendMessage() {
    const input = document.getElementById("chat-input").value.trim();
    const chatContainer = document.getElementById("chat-container");
    
    if (!input) return; // Don't send empty messages
    
    // Clear initial placeholder text if this is the first message
    if (chatContainer.querySelector('p.text-gray-500')) {
        chatContainer.innerHTML = '';
    }
    
    // Add user message to chat
    let userMessage = `<div class="text-right text-blue-600 mt-2"><strong>You:</strong> ${input}</div>`;
    chatContainer.innerHTML += userMessage;
    document.getElementById("chat-input").value = "";
    
    // Show typing indicator
    let typingIndicator = `<div id="typing-indicator" class="text-left text-gray-500 mt-2"><em>Assistant is typing...</em></div>`;
    chatContainer.innerHTML += typingIndicator;
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Send message to server
    fetch('/chat_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: input,
            subject: sessionData.subject,
            unit: sessionData.unit
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove typing indicator
        document.getElementById("typing-indicator").remove();
        
        // Process markdown in the response
        const formattedResponse = marked.parse(data.response);
        
        // Add bot response with proper HTML rendering
        let botMessage = `<div class="text-left text-gray-600 mt-2"><strong>Assistant:</strong> <div class="markdown-content">${formattedResponse}</div></div>`;
        chatContainer.innerHTML += botMessage;
        chatContainer.scrollTop = chatContainer.scrollHeight;
    })
    .catch(error => {
        // Error handling
        console.error("Error sending message:", error);
        document.getElementById("typing-indicator").remove();
        chatContainer.innerHTML += `<div class="text-left text-red-500 mt-2"><em>Error sending message. Please try again.</em></div>`;
    });
}

// Handle file attachment
function handleAttachment() {
    document.getElementById('file-upload').click();
}

// Process the selected file
function processFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Check if file is an image
    if (!file.type.match('image.*')) {
        alert('Please select an image file');
        return;
    }
    
    // Display preview of the image
    const reader = new FileReader();
    reader.onload = function(e) {
        const chatContainer = document.getElementById("chat-container");
        
        // Clear initial placeholder if this is the first message
        if (chatContainer.querySelector('p.text-gray-500')) {
            chatContainer.innerHTML = '';
        }
        
        // Add image message to chat
        let imageMessage = `
            <div class="text-right text-blue-600 mt-2">
                <strong>You:</strong> 
                <div class="mt-2">
                    <img src="${e.target.result}" alt="Uploaded image" class="max-w-xs max-h-64 rounded inline-block">
                </div>
            </div>
        `;
        chatContainer.innerHTML += imageMessage;
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        // TODO: Implement server-side handling of image uploads
        // For now, just show a response
        let typingIndicator = `<div id="typing-indicator" class="text-left text-gray-500 mt-2"><em>Assistant is typing...</em></div>`;
        chatContainer.innerHTML += typingIndicator;
        
        setTimeout(() => {
            document.getElementById("typing-indicator").remove();
            let botMessage = `<div class="text-left text-gray-600 mt-2"><strong>Assistant:</strong> I've received your image. However, image processing isn't fully implemented yet.</div>`;
            chatContainer.innerHTML += botMessage;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }, 1000);
    };
    reader.readAsDataURL(file);
    
    // Reset the input
    event.target.value = '';
}

// Handle microphone input
let recognition;
function toggleMicrophone() {
    const micButton = document.getElementById('mic-button');
    
    // Check if browser supports speech recognition
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert("Your browser doesn't support speech recognition. Try Chrome or Edge.");
        return;
    }
    
    // Initialize speech recognition
    if (!recognition) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById("chat-input").value = transcript;
            micButton.classList.remove('text-red-500');
            micButton.classList.add('text-gray-600');
        };
        
        recognition.onerror = function(event) {
            console.error("Speech recognition error", event.error);
            micButton.classList.remove('text-red-500');
            micButton.classList.add('text-gray-600');
        };
        
        recognition.onend = function() {
            micButton.classList.remove('text-red-500');
            micButton.classList.add('text-gray-600');
        };
    }
    
    // Toggle microphone on/off
    if (micButton.classList.contains('text-red-500')) {
        // Stop recording
        recognition.stop();
        micButton.classList.remove('text-red-500');
        micButton.classList.add('text-gray-600');
    } else {
        // Start recording
        recognition.start();
        micButton.classList.remove('text-gray-600');
        micButton.classList.add('text-red-500');
    }
}

// Load Notes section with the 4 options
function loadNotes() {
    document.getElementById("content-area").innerHTML = `
        <h3 class="text-lg font-bold text-gray-800">Select Resource Type</h3>
        <div class="mt-2 grid grid-cols-2 gap-3">
            <button onclick="loadResourceContent('Quantum')" class="px-4 py-3 bg-purple-500 text-white rounded-lg shadow-md hover:bg-purple-600 transition">1. Quatum</button>
            <button onclick="loadResourceContent('PYQ')" class="px-4 py-3 bg-indigo-500 text-white rounded-lg shadow-md hover:bg-indigo-600 transition">2. PYQ</button>
            <button onclick="loadResourceContent('Sessional Paper')" class="px-4 py-3 bg-blue-500 text-white rounded-lg shadow-md hover:bg-blue-600 transition">3. Sessional Paper</button>
            <button onclick="loadResourceContent('Detailed Notes')" class="px-4 py-3 bg-green-500 text-white rounded-lg shadow-md hover:bg-green-600 transition">4. Detailed Notes</button>
        </div>
    `;
}

// Display content based on the selected option using session data
function loadResourceContent(resourceType) {
    // Get subject and unit from session data instead of dropdowns
    const subject = sessionData.subject;
    const unit = sessionData.unit;

    if (!subject || !unit) {
        document.getElementById("content-area").innerHTML = `
            <h3 class="text-lg font-bold text-gray-800">${resourceType}</h3>
            <div class="mt-4 p-4 border rounded bg-white text-center">
                <p class="text-orange-500">Please select a subject and unit from the dashboard first.</p>
                <p class="mt-2 text-gray-600">Your selections will be used to display the appropriate content.</p>
                <a href="/" class="mt-3 inline-block px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                    Go to Dashboard
                </a>
            </div>
        `;
        return;
    }

    // Fetch the Google Drive link from the server
    fetch(`/get_drive_link/${resourceType}/${subject}/${unit}`)
        .then(response => response.json())
        .then(data => {
            if (data.drive_link) {
                const googleDriveLink = data.drive_link;
                console.log("📂 Drive link found:", googleDriveLink);
                document.getElementById("content-area").innerHTML = `
                    <h3 class="text-lg font-bold text-gray-800">${resourceType}</h3>
                    <div class="mt-2 p-4 border rounded bg-white">
                        <div class="flex justify-between items-center mb-3">
                            <div>
                                <span class="font-semibold text-gray-700">Subject:</span> ${subject}
                            </div>
                            <div>
                                <span class="font-semibold text-gray-700">Unit:</span> ${unit}
                            </div>
                        </div>
                        <div class="mt-4">
                            <iframe src="${googleDriveLink}" class="w-full h-96 border rounded" allowfullscreen></iframe>
                        </div>
                        <p class="mt-4 text-sm text-gray-500">Note: If the document doesn't load, ensure the Google Drive file is shared publicly.</p>
                    </div>
                    <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
                `;
            } else {
                document.getElementById("content-area").innerHTML = `
                    <h3 class="text-lg font-bold text-gray-800">${resourceType}</h3>
                    <div class="mt-4 p-4 border rounded bg-white text-center">
                        <p class="text-red-500">Drive link not found for the selected resource.</p>
                    </div>
                    <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
                `;
            }
        })
        .catch(error => {
            console.error("Error fetching drive link:", error);
            document.getElementById("content-area").innerHTML = `
                <h3 class="text-lg font-bold text-gray-800">${resourceType}</h3>
                <div class="mt-4 p-4 border rounded bg-white text-center">
                    <p class="text-red-500">An error occurred while fetching the drive link. Please try again later.</p>
                </div>
                <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
            `;
        });
}

// Load YouTube videos dynamically
function loadYouTube() {
    // Get subject and unit from session data
    const subject = sessionData.subject;
    const unit = sessionData.unit;
    
    if (!subject || !unit) {
        document.getElementById("content-area").innerHTML = `
            <h3 class="text-lg font-bold text-gray-800">YouTube Tutorials</h3>
            <div class="mt-4 p-4 border rounded bg-white text-center">
                <p class="text-orange-500">Please select a subject and unit from the dashboard first.</p>
                <p class="mt-2 text-gray-600">Your selections will be used to display relevant videos.</p>
                <a href="/" class="mt-3 inline-block px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
                    Go to Dashboard
                </a>
            </div>
        `;
        return;
    }
    
    // Show loading state
    document.getElementById("content-area").innerHTML = `
        <h3 class="text-lg font-bold text-gray-800">YouTube Tutorials</h3>
        <div class="mt-2 p-4 border rounded bg-white">
            <div class="flex justify-between items-center mb-3">
                <div><span class="font-semibold text-gray-700">Subject:</span> ${subject}</div>
                <div><span class="font-semibold text-gray-700">Unit:</span> ${unit}</div>
            </div>
            <div class="mt-4 text-center">
                <p class="text-gray-600">Loading video...</p>
                <div class="mt-2 h-4 bg-gray-200 rounded overflow-hidden">
                    <div class="h-full bg-red-500 animate-pulse w-1/2"></div>
                </div>
            </div>
        </div>
    `;
    
    // Try to fetch a specific video for this subject and unit
    fetch(`/get_youtube_url/${subject}/${unit}`)
        .then(response => response.json())
        .then(data => {
            const searchQuery = `${subject} ${unit} aktu one shot `;
            const encodedQuery = encodeURIComponent(searchQuery);
            
            if (data.video_id) {
                // Video found, embed it AND offer search option
                document.getElementById("content-area").innerHTML = `
                    <h3 class="text-lg font-bold text-gray-800">YouTube Tutorial - ${subject}: ${unit}</h3>
                    <div class="mt-2 p-4 border rounded bg-white">
                        <iframe class="w-full h-64" src="https://www.youtube.com/embed/${data.video_id}" 
                                frameborder="0" allowfullscreen></iframe>
                        <div class="mt-2 text-center">
                            <a href="${data.url}" target="_blank" class="text-blue-500 hover:underline">
                                Watch on YouTube
                            </a>
                            <p class="mt-3 text-gray-600">Want to explore more videos?</p>
                            <a href="https://www.youtube.com/results?search_query=${encodedQuery}" 
                               target="_blank" 
                               class="mt-2 inline-block px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition">
                                Search for more videos
                            </a>
                        </div>
                    </div>
                    <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
                `;
            } else {
                // No specific video found, only offer search
                document.getElementById("content-area").innerHTML = `
                    <h3 class="text-lg font-bold text-gray-800">YouTube Tutorials - ${subject}: ${unit}</h3>
                    <div class="mt-2 p-4 border rounded bg-white text-center">
                        <p class="mb-4 text-gray-600">Find educational videos for this topic:</p>
                        <a href="https://www.youtube.com/results?search_query=${encodedQuery}" 
                           target="_blank" 
                           class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition">
                            Search YouTube for "${searchQuery}"
                        </a>
                    </div>
                    <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
                `;
            }
        })
        .catch(error => {
            // Only in case of actual fetch error
            document.getElementById("content-area").innerHTML = `
                <h3 class="text-lg font-bold text-gray-800">YouTube Tutorials</h3>
                <div class="mt-2 p-4 border rounded bg-white text-center">
                    <p class="text-red-500">Sorry, there was an error loading videos.</p>
                    <p class="mt-2 text-gray-600">Please try again later.</p>
                </div>
                <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
            `;
        });
}

// Add these functions at the end of your file

// Handle fullscreen mode
function toggleFullscreen() {
    const chatSection = document.getElementById('chat-section');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const container = document.querySelector('.max-w-5xl');
    
    if (!document.fullscreenElement) {
        // Enter fullscreen
        chatSection.classList.add('fullscreen-mode');
        container.classList.add('fullscreen-container');
        
        if (chatSection.requestFullscreen) {
            chatSection.requestFullscreen();
        } else if (chatSection.webkitRequestFullscreen) { /* Safari */
            chatSection.webkitRequestFullscreen();
        } else if (chatSection.msRequestFullscreen) { /* IE11 */
            chatSection.msRequestFullscreen();
        }
        
        // Change icon to exit fullscreen
        fullscreenBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        `;
        
        // Adjust chat container height for fullscreen
        document.getElementById('chat-container').classList.remove('h-80');
        document.getElementById('chat-container').classList.add('h-[70vh]');
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) { /* Safari */
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) { /* IE11 */
            document.msExitFullscreen();
        }
    }
}

// Listen for fullscreen change events
document.addEventListener('fullscreenchange', handleFullscreenChange);
document.addEventListener('webkitfullscreenchange', handleFullscreenChange); // Safari
document.addEventListener('mozfullscreenchange', handleFullscreenChange);    // Firefox
document.addEventListener('MSFullscreenChange', handleFullscreenChange);     // IE11

function handleFullscreenChange() {
    const chatSection = document.getElementById('chat-section');
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const container = document.querySelector('.max-w-5xl');
    
    if (!document.fullscreenElement) {
        // User has exited fullscreen
        chatSection.classList.remove('fullscreen-mode');
        container.classList.remove('fullscreen-container');
        
        // Restore original icon
        fullscreenBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 0h-4m4 0l-5-5" />
            </svg>
        `;
        
        // Restore original chat container height
        document.getElementById('chat-container').classList.add('h-80');
        document.getElementById('chat-container').classList.remove('h-[70vh]');
    }
}
