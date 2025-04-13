// Toggle password visibility
document.addEventListener('DOMContentLoaded', function() {
    const togglePassword = document.querySelector('.toggle-password');
    const passwordInput = document.querySelector('#password');
    
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Toggle icon
            const icon = this.querySelector('i');
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });
    }
});
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const errorParam = urlParams.get('error');
    const success = document.getElementById('success');
    const danger = document.getElementById('danger');
    
    // Handle error parameter from Flask
    if (errorParam === 'invalid') {
        danger.style.display = 'block';
        
        setTimeout(() => {
            danger.style.display = 'none';
        }, 4000);
    }


    // Handle form submission
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            // Only check for empty fields - don't show success message yet
            if (email === '' || password === '') {
                e.preventDefault(); // Prevent form submission
                danger.textContent = "Fields can't be empty!";
                danger.style.display = 'block';
                
                setTimeout(() => {
                    danger.style.display = 'none';
                }, 4000);
            }
            // Let the server handle validation and success state
            // Don't show success message here
        });
    }
});
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
        
        // Create a container for the bot message with empty content initially
        let botMessageContainer = document.createElement('div');
        botMessageContainer.className = "text-left text-gray-600 mt-2";
        
        // Create header and content container
        botMessageContainer.innerHTML = `<strong>Assistant:</strong> <div class="markdown-content typing-content"></div>`;
        chatContainer.appendChild(botMessageContainer);
        
        const typingContent = botMessageContainer.querySelector('.typing-content');
        
        // Get the raw text response
        const responseText = data.response;
        let charIndex = 0;
        
        // Typing speed (milliseconds per character)
        const typingSpeed = 0.1;
        
        // Function to type characters one by one
        function typeNextCharacter() {
            if (charIndex < responseText.length) {
                // Get current text and add next character
                typingContent.textContent = responseText.substring(0, charIndex + 1);
                charIndex++;
                
                // Schedule next character
                setTimeout(typeNextCharacter, typingSpeed);
            } else {
                // Typing finished - now apply markdown formatting
                typingContent.innerHTML = marked.parse(responseText);
                
                // Scroll to bottom
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            // Scroll as we type
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        // Start typing effect
        typeNextCharacter();
    })
    .catch(error => {
        // Error handling
        console.error("Error sending message:", error);
        document.getElementById("typing-indicator").remove();
        chatContainer.innerHTML += `<div class="text-left text-red-500 mt-2"><em>Error sending message. Please try again.</em></div>`;
    });
}

// // Handle file attachment
// function handleAttachment() {
//     document.getElementById('file-upload').click();
// }

// // Process the selected file
// function processFile(event) {
//     const file = event.target.files[0];
//     if (!file) return;
    
//     // Check if file is an image
//     if (!file.type.match('image.*')) {
//         alert('Please select an image file');
//         return;
//     }
    
//     // Display preview of the image
//     const reader = new FileReader();
//     reader.onload = function(e) {
//         const chatContainer = document.getElementById("chat-container");
        
//         // Clear initial placeholder if this is the first message
//         if (chatContainer.querySelector('p.text-gray-500')) {
//             chatContainer.innerHTML = '';
//         }
        
//         // Add image message to chat
//         let imageMessage = `
//             <div class="text-right text-blue-600 mt-2">
//                 <strong>You:</strong> 
//                 <div class="mt-2">
//                     <img src="${e.target.result}" alt="Uploaded image" class="max-w-xs max-h-64 rounded inline-block">
//                 </div>
//             </div>
//         `;
//         chatContainer.innerHTML += imageMessage;
//         chatContainer.scrollTop = chatContainer.scrollHeight;
        
//         // TODO: Implement server-side handling of image uploads
//         // For now, just show a response
//         let typingIndicator = `<div id="typing-indicator" class="text-left text-gray-500 mt-2"><em>Assistant is typing...</em></div>`;
//         chatContainer.innerHTML += typingIndicator;
        
//         setTimeout(() => {
//             document.getElementById("typing-indicator").remove();
//             let botMessage = `<div class="text-left text-gray-600 mt-2"><strong>Assistant:</strong> I've received your image. However, image processing isn't fully implemented yet.</div>`;
//             chatContainer.innerHTML += botMessage;
//             chatContainer.scrollTop = chatContainer.scrollHeight;
//         }, 1000);
//     };
//     reader.readAsDataURL(file);
    
//     // Reset the input
//     event.target.value = '';
// }

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
                        <p class="mt-4 text-sm text-gray-500">Note: If the document doesn't load, it will update soon.</p>
                    </div>
                    <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
                `;
            } else {
                document.getElementById("content-area").innerHTML = `
                    <h3 class="text-lg font-bold text-gray-800">${resourceType}</h3>
                    <div class="mt-4 p-4 border rounded bg-white text-center">
                        <p class="text-blue-500 text-lg font-medium">Coming Soon</p>
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
                    <p class="text-blue-500 text-lg font-medium">Coming Soon</p>
                </div>
                <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
            `;
        });
}

// Updated loadYouTube function with consistent color scheme
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
                <a href="/" class="mt-3 inline-block px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded hover:from-blue-600 hover:to-indigo-700 transition">
                    Go to Dashboard
                </a>
            </div>
        `;
        return;
    }
    
    // Create search query for the current subject and unit
    const searchQuery = `${subject} ${unit} aktu one shot`;
    const encodedQuery = encodeURIComponent(searchQuery);
    
    // Create UI with input field for YouTube URL
    document.getElementById("content-area").innerHTML = `
        <h3 class="text-lg font-bold text-gray-800">YouTube Tutorials - ${subject}: ${unit}</h3>
        <div class="mt-2 p-4 border rounded bg-white">
            <div id="youtube-input-section" class="mb-4">
                <label class="block text-gray-700 mb-2">Enter YouTube Video URL:</label>
                <div class="flex">
                    <input type="text" id="youtube-url" placeholder="https://www.youtube.com/watch?v=..." 
                           class="flex-1 px-3 py-2 border rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500">
                    <button onclick="embedYoutubeVideo()" 
                            class="px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-r hover:from-blue-600 hover:to-indigo-700 transition">
                        Embed Video
                    </button>
                </div>
                <p class="text-xs text-gray-500 mt-1">Paste a YouTube video link to embed it directly</p>
            </div>
            
            <div id="video-container" class="mt-5">
                <p class="text-center text-gray-600">Enter a YouTube URL above or search for videos</p>
            </div>
            
            <div id="youtube-search-section" class="mt-4 text-center">
                <p class="text-gray-600">Find more educational videos for this topic:</p>
                <a href="https://www.youtube.com/results?search_query=${encodedQuery}" 
                   target="_blank" 
                   class="mt-2 inline-block px-4 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 transition">
                    Search YouTube for "${searchQuery}"
                </a>
            </div>
        </div>
        <button onclick="loadNotes()" class="mt-3 px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition">← Back to options</button>
    `;
}

// Function to extract video ID from YouTube URL and embed it with reduced ads
function embedYoutubeVideo() {
    const videoContainer = document.getElementById("video-container");
    const youtubeUrl = document.getElementById("youtube-url").value.trim();
    
    if (!youtubeUrl) {
        videoContainer.innerHTML = `<p class="text-red-500 text-center">Please enter a YouTube URL</p>`;
        return;
    }
    
    // Extract video ID from various YouTube URL formats
    let videoId = null;
    
    // Regular expression patterns for different YouTube URL formats
    const patterns = [
        // Format: youtube.com/watch?v=VIDEO_ID (standard)
        /(?:youtube\.com\/watch\?v=)([^&\?\/]+)/,
        
        // Format: youtu.be/VIDEO_ID (shortened)
        /(?:youtu\.be\/)([^&\?\/]+)/,
        
        // Format: youtube.com/embed/VIDEO_ID (embedded)
        /(?:youtube\.com\/embed\/)([^&\?\/]+)/,
        
        // Format: youtube.com/shorts/VIDEO_ID (YouTube Shorts)
        /(?:youtube\.com\/shorts\/)([^&\?\/]+)/,
        
        // Format: youtube-nocookie.com/embed/VIDEO_ID (privacy-enhanced)
        /(?:youtube-nocookie\.com\/embed\/)([^&\?\/]+)/
    ];
    
    // Try each pattern until we find a match
    for (const pattern of patterns) {
        const match = youtubeUrl.match(pattern);
        if (match && match[1]) {
            videoId = match[1];
            break;
        }
    }
    
    if (videoId) {
        try {
            // Use youtube-nocookie.com domain for better privacy
            // Add parameters to reduce ads:
            const embedUrl = `https://www.youtube-nocookie.com/embed/${videoId}?rel=0&modestbranding=1&iv_load_policy=3&cc_load_policy=0&fs=1&playsinline=1`;
            
            // Get direct references to sections by ID
            const inputSection = document.getElementById("youtube-input-section");
            const searchSection = document.getElementById("youtube-search-section");
            
            // If sections don't have IDs, try to find them the old way
            if (!inputSection) {
                const tempInput = document.querySelector('#youtube-url').closest('.mb-4');
                if (tempInput) {
                    tempInput.id = "youtube-input-section";
                    tempInput.style.display = 'none';
                }
            } else {
                inputSection.style.display = 'none';
            }
            
            if (!searchSection) {
                const tempSearch = document.querySelector('.mt-4.text-center');
                if (tempSearch) {
                    tempSearch.id = "youtube-search-section";
                    tempSearch.style.display = 'none';
                }
            } else {
                searchSection.style.display = 'none';
            }
            
            // Replace the video container with the embedded video
            videoContainer.innerHTML = `
                <div class="relative pt-1">
                    <div class="flex mb-2 items-center justify-between">
                        <div>
                            <span class="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full bg-red-200 text-red-600">
                                Ad-Reduced Mode
                            </span>
                        </div>
                        <div class="text-right">
                            <span class="text-xs font-semibold inline-block text-gray-600">
                                Enhanced Viewing Experience
                            </span>
                        </div>
                    </div>
                </div>
                <div class="mb-2">
                    <iframe class="w-full h-96" src="${embedUrl}" 
                            frameborder="0" allowfullscreen></iframe>
                </div>
                <div class="flex justify-between items-center mt-3">
                    <a href="${youtubeUrl}" target="_blank" class="text-blue-500 hover:underline">
                        Open on YouTube
                    </a>
                    <button onclick="resetYouTubeEmbed()" class="px-3 py-1 bg-gray-200 rounded hover:bg-gray-300">
                        Embed Another Video
                    </button>
                </div>
            `;
            
            // Ensure video container is visible
            videoContainer.style.display = 'block';
        } catch (error) {
            console.error("Error embedding YouTube video:", error);
            videoContainer.innerHTML = `
                <p class="text-red-500 text-center">Error embedding video. Please try again.</p>
            `;
        }
    } else {
        videoContainer.innerHTML = `
            <p class="text-red-500 text-center mb-2">
                Invalid YouTube URL. Please use a URL from youtube.com or youtu.be
            </p>
            <div class="text-xs text-gray-600 p-2 bg-gray-100 rounded">
                <p class="font-semibold">Supported URL formats:</p>
                <ul class="list-disc pl-5 mt-1">
                    <li>youtube.com/watch?v=VIDEO_ID</li>
                    <li>youtu.be/VIDEO_ID</li>
                    <li>youtube.com/embed/VIDEO_ID</li>
                    <li>youtube.com/shorts/VIDEO_ID</li>
                </ul>
            </div>
        `;
    }
}

// Function to reset the YouTube embed section
function resetYouTubeEmbed() {
    // Get sections by ID first, fall back to selectors if needed
    let inputSection = document.getElementById("youtube-input-section");
    let searchSection = document.getElementById("youtube-search-section");
    
    // Fallback to querySelector if IDs aren't found
    if (!inputSection) {
        inputSection = document.querySelector('#youtube-url').closest('.mb-4');
    }
    
    if (!searchSection) {
        searchSection = document.querySelector('.mt-4.text-center');
    }
    
    // Show the sections again
    if (inputSection) inputSection.style.display = 'block';
    if (searchSection) inputSection.style.display = 'block';
    
    // Clear the current video
    const videoContainer = document.getElementById('video-container');
    if (videoContainer) {
        videoContainer.innerHTML = `
            <p class="text-center text-gray-600">Enter a YouTube URL above or search for videos</p>
        `;
    }
    
    // Clear the input field
    const urlInput = document.getElementById('youtube-url');
    if (urlInput) urlInput.value = '';
}

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


