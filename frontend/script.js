// State management
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let audioContext;
let analyser;
let animationFrameId;

// DOM Elements
const sentenceInput = document.getElementById('sentenceInput');
const updateBtn = document.getElementById('updateBtn');
const sentenceDisplay = document.getElementById('sentenceDisplay');
const recordBtn = document.getElementById('recordBtn');
const recordBtnText = document.getElementById('recordBtnText');
const recordingIndicator = document.getElementById('recordingIndicator');
const audioPlayer = document.getElementById('audioPlayer');
const audioPlayback = document.getElementById('audioPlayback');
const retryBtn = document.getElementById('retryBtn');
const submitBtn = document.getElementById('submitBtn');
const feedbackSection = document.getElementById('feedbackSection');
const feedbackContent = document.getElementById('feedbackContent');
const progress = document.getElementById('progress');
const recordingControls = document.getElementById('recordingControls');
const newRecordingBtn = document.getElementById('newRecordingBtn');
const waveformContainer = document.getElementById('waveformContainer');
const waveform = document.getElementById('waveform');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Speech Teacher App Initialized');
    checkMicrophonePermission();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    updateBtn.addEventListener('click', updateSentence);
    sentenceInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            updateSentence();
        }
    });
    recordBtn.addEventListener('click', toggleRecording);
    retryBtn.addEventListener('click', retryRecording);
    submitBtn.addEventListener('click', submitRecording);
    newRecordingBtn.addEventListener('click', startNewRecording);
}

// Update the sentence to practice
function updateSentence() {
    const newSentence = sentenceInput.value.trim();
    if (newSentence) {
        sentenceDisplay.textContent = newSentence;
        // Reset recording state
        resetRecordingState();
        // Update progress
        updateProgress(10);
    } else {
        alert('Please enter a sentence to practice.');
    }
}

// Check microphone permission
async function checkMicrophonePermission() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        console.log('Microphone access granted');
    } catch (error) {
        console.error('Microphone access denied:', error);
        alert('Please allow microphone access to use this app.');
    }
}

// Toggle recording
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

// Start recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        // Set up Web Audio API for visualization
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        analyser.fftSize = 512; // Increased for better frequency resolution
        analyser.smoothingTimeConstant = 0.7; // Smoother transitions
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayback.src = audioUrl;
            
            // Stop visualization
            cancelAnimationFrame(animationFrameId);
            
            // Update waveform to static state
            waveform.classList.remove('recording');
            waveform.classList.add('static');
            
            // Hide recording controls and show audio player
            recordingControls.classList.add('hidden');
            audioPlayer.classList.remove('hidden');
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Close audio context
            if (audioContext) {
                audioContext.close();
            }
            
            // Update progress
            updateProgress(50);
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        recordBtn.classList.add('recording');
        recordBtnText.textContent = 'Stop Recording';
        recordingIndicator.classList.remove('hidden');
        waveformContainer.classList.remove('hidden');
        waveform.classList.add('recording');
        waveform.classList.remove('static');
        audioPlayer.classList.add('hidden');
        feedbackSection.classList.add('hidden');
        
        // Start visualization
        visualizeAudio();
        
        console.log('Recording started');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Could not start recording. Please check your microphone.');
    }
}

// Stop recording
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Stop visualization
        cancelAnimationFrame(animationFrameId);
        
        // Update UI
        recordBtn.classList.remove('recording');
        recordBtnText.textContent = 'Start Recording';
        recordingIndicator.classList.add('hidden');
        
        console.log('Recording stopped');
    }
}

// Visualize audio in real-time
function visualizeAudio() {
    if (!analyser || !isRecording) return;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);
    
    // Get waveform bars
    const bars = waveform.querySelectorAll('.waveform-bar');
    const barCount = bars.length;
    
    // Focus on speech frequencies (100Hz - 3000Hz)
    // Skip very low frequencies (0-100Hz) which can cause issues
    const minFrequency = 100; // Start at 100Hz to avoid DC offset and very low noise
    const maxFrequency = 3000; // Focus on speech frequencies
    const nyquist = audioContext.sampleRate / 2;
    const minBin = Math.floor((minFrequency / nyquist) * bufferLength);
    const maxBin = Math.floor((maxFrequency / nyquist) * bufferLength);
    const usableBins = maxBin - minBin;
    
    // Distribute bars with more weight on lower frequencies
    // Use exponential distribution for more bars at lower frequencies
    bars.forEach((bar, index) => {
        // Exponential curve: more samples for lower frequency bars
        // Ensure first bar gets a range by using (index+1) for end calculation
        const t = index / barCount;
        const exponentialT = Math.pow(t, 1.35);
        
        const nextT = (index + 1) / barCount;
        const nextExponentialT = Math.pow(nextT, 1.35); // Use same exponent for consistency
        
        const startBin = minBin + Math.floor(exponentialT * usableBins);
        const endBin = minBin + Math.floor(nextExponentialT * usableBins);
        
        // Ensure each bar has at least some bins to sample
        const actualEndBin = Math.max(startBin + 1, endBin);
        
        // Get average frequency data for this bar's range
        let sum = 0;
        let count = 0;
        
        for (let i = startBin; i < actualEndBin && i < bufferLength; i++) {
            sum += dataArray[i];
            count++;
        }
        
        const average = count > 0 ? sum / count : 0;
        
        // Reduced amplification (1.8x multiplier instead of 2.5x)
        // Convert to percentage with balanced sensitivity
        const amplified = average * 1.8;
        const height = Math.max(20, Math.min(100, (amplified / 255) * 100));
        
        // Apply height with smooth transition
        bar.style.height = `${height}%`;
    });
    
    // Continue animation
    animationFrameId = requestAnimationFrame(visualizeAudio);
}

// Retry recording
function retryRecording() {
    resetRecordingState();
    updateProgress(10);
}

// Reset recording state
function resetRecordingState() {
    audioChunks = [];
    audioPlayer.classList.add('hidden');
    feedbackSection.classList.add('hidden');
    recordingControls.classList.remove('hidden');
    waveformContainer.classList.add('hidden');
    waveform.classList.remove('recording', 'static');
    if (isRecording) {
        stopRecording();
    }
}

// Start a new recording (from feedback screen)
function startNewRecording() {
    resetRecordingState();
    updateProgress(10);
}

// Submit recording for feedback
async function submitRecording() {
    if (audioChunks.length === 0) {
        alert('No recording to submit. Please record first.');
        return;
    }
    
    console.log('Submitting recording for analysis...');
    
    try {
        // Create blob from audio chunks
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        
        // Convert to base64
        const base64Audio = await blobToBase64(audioBlob);
        
        // Also save the audio
        await window.pywebview.api.save_audio(
            base64Audio,
            sentenceDisplay.textContent
        );

        // Call Python backend via pywebview API to analyze
        const result = await window.pywebview.api.analyze_audio(
            base64Audio,
            sentenceDisplay.textContent
        );
        
        if (result.success) {
            console.log('Analysis complete:', result);
            
            // Show feedback with corrections
            showFeedback(result);
            updateProgress(100);
        } else {
            throw new Error(result.error || 'Failed to analyze audio');
        }
        
    } catch (error) {
        console.error('Error submitting recording:', error);
        alert('Failed to analyze recording. Please try again.');
    }
}

// Show feedback
function showFeedback(result) {
    console.log('Full result from backend:', result);
    
    // Hide recording controls and audio player
    recordingControls.classList.add('hidden');
    audioPlayer.classList.add('hidden');
    
    // Show feedback section
    feedbackSection.classList.remove('hidden');
    
    // Convert AI message (markdown) to safe HTML
    console.log('Raw message from backend:', result.message);
    const messageHtml = markdownToHtml(result.message || '');
    console.log('Converted message HTML:', messageHtml);

    let feedbackHTML = '';
    
    // Show sentence with highlighted corrections
    if (result.corrections && result.corrections.length > 0) {
        feedbackHTML += '<div class="feedback-layout">';
        
        // Left side: Sentence with corrections
        feedbackHTML += '<div class="corrections-container">';
        feedbackHTML += '<h3>Your Pronunciation:</h3>';
        feedbackHTML += '<div class="sentence-with-corrections">';
        feedbackHTML += highlightSentenceWithCorrections(result.sentence, result.corrections);
        feedbackHTML += '</div>';
        
    // Show score under sentence
        if (result.score !== undefined) {
            const scoreColor = result.score >= 90 ? '#58CC02' : result.score >= 70 ? '#FFC800' : '#FF4B4B';
            feedbackHTML += `
                <div class="score-container">
                    <div class="score-label">Your Score</div>
                    <div class="score-value" style="color: ${scoreColor};">${result.score}/100</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${result.score}%;"></div>
                    </div>
                </div>
            `;
        }
        feedbackHTML += '</div>';
        
        // Right side: Viseme images for corrections
        const correctionsWithVisemes = result.corrections.filter(c => c.viseme_img_path);
        if (correctionsWithVisemes.length > 0) {
            feedbackHTML += '<div class="viseme-corrections">';
            feedbackHTML += '<h3>How to improve:</h3>';
            correctionsWithVisemes.forEach((correction, index) => {
                const errorText = result.sentence.substring(correction.start_index, correction.end_index);
                // Use file:// protocol for local file access in pywebview
                const imagePath = correction.viseme_img_path;
                feedbackHTML += `
                    <div class="viseme-card" data-correction-index="${index}">
                        <div class="viseme-label">
                            <span class="error-word">"${errorText}"</span>
                            <span class="error-type ${correction.type}">${correction.type}</span>
                        </div>
                        <img src="${imagePath}" alt="Correct mouth position" class="viseme-img" onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22180%22 height=%22180%22%3E%3Crect fill=%22%23ccc%22 width=%22180%22 height=%22180%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22 fill=%22%23666%22%3EImage not found%3C/text%3E%3C/svg%3E';"/>
                        <p class="viseme-hint">Try positioning your mouth like this</p>
                    </div>
                `;
            });
            feedbackHTML += '</div>';
        }

        // AI message (markdown converted to HTML) - always show the message even when there are corrections
        if (messageHtml) {
            feedbackHTML += `
                <div class="ai-message">
                    ${messageHtml}
                </div>
            `;
        }

        feedbackHTML += '</div>';
    } else {
        feedbackHTML += '<div class="perfect-message">';
        feedbackHTML += '<svg width="60" height="60" viewBox="0 0 24 24" fill="none" style="margin-bottom: 15px;">';
        feedbackHTML += '<circle cx="12" cy="12" r="10" fill="#58CC02"/>';
        feedbackHTML += '<path d="M8 12L11 15L16 9" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
        feedbackHTML += '</svg>';
        // Render converted markdown message
        feedbackHTML += `<div class="ai-message perfect">${messageHtml}</div>`;
        feedbackHTML += '</div>';

        // Show score for perfect score
        if (result.score !== undefined) {
            const scoreColor = result.score >= 90 ? '#58CC02' : result.score >= 70 ? '#FFC800' : '#FF4B4B';
            feedbackHTML += `
                <div class="score-container">
                    <div class="score-label">Your Score</div>
                    <div class="score-value" style="color: ${scoreColor};">${result.score}/100</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${result.score}%;"></div>
                    </div>
                </div>
            `;
        }
    }
    
    feedbackContent.innerHTML = feedbackHTML;
    
    // Set up hover interactions after content is rendered
    setupCorrectionHoverEffects();
}

// Simple HTML-escaping helper
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Lightweight markdown -> HTML converter (supports **bold**, *italic*, `code`, [link](url), and line breaks)
function markdownToHtml(md) {
    if (!md) return '';
    // Escape HTML first to avoid XSS
    let html = escapeHtml(md);

    // Convert links: [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

    // Bold: **text**
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic: *text* (avoid conflict with bold by running after)
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Inline code: `code`
    html = html.replace(/`(.+?)`/g, '<code>$1</code>');

    // Replace double newlines with paragraph breaks, single newline -> <br>
    // First normalize CRLF to LF
    html = html.replace(/\r\n/g, '\n');
    html = html.replace(/\n\n+/g, '</p><p>');
    // Wrap with paragraph tags if there are paragraphs
    if (html.indexOf('</p><p>') !== -1) {
        html = '<p>' + html + '</p>';
        // Escape the regex boundary by escaping the slash in the closing tag
        html = html.replace(/<\/p><p>/g, '</p><p>');
    }
    // Single newlines to <br>
    // After wrapping paragraphs above, replace remaining newlines with <br>
    html = html.replace(/\n/g, '<br>');

    return html;
}

// Setup hover effects to highlight corresponding viseme cards
function setupCorrectionHoverEffects() {
    const errorSpans = feedbackContent.querySelectorAll('[data-viseme-index]');
    const visemeCards = feedbackContent.querySelectorAll('.viseme-card');
    
    errorSpans.forEach(span => {
        span.addEventListener('mouseenter', () => {
            const index = span.getAttribute('data-viseme-index');
            visemeCards.forEach(card => {
                if (card.getAttribute('data-correction-index') === index) {
                    card.classList.add('active');
                }
            });
        });
        
        span.addEventListener('mouseleave', () => {
            visemeCards.forEach(card => {
                card.classList.remove('active');
            });
        });
    });
}

// Highlight sentence with corrections
function highlightSentenceWithCorrections(sentence, corrections) {
    if (!corrections || corrections.length === 0) {
        return `<span class="correct-text">${sentence}</span>`;
    }
    
    let html = '';
    let lastIndex = 0;
    let visemeIndex = 0;
    
    // Sort corrections by start_index
    const sortedCorrections = [...corrections].sort((a, b) => a.start_index - b.start_index);
    
    sortedCorrections.forEach(correction => {
        // Add correct text before this correction
        if (correction.start_index > lastIndex) {
            html += `<span class="correct-text">${sentence.substring(lastIndex, correction.start_index)}</span>`;
        }
        
        // Add highlighted correction based on type
        const errorText = sentence.substring(correction.start_index, correction.end_index);
        const hasViseme = correction.viseme_img_path ? true : false;
        const dataAttr = hasViseme ? `data-viseme-index="${visemeIndex}"` : '';
        
        if (correction.type === 'insertion') {
            // Insertion: show with red dotted underline (these characters shouldn't be said)
            html += `<span class="error-insertion" ${dataAttr} title="Remove this sound">${errorText}</span>`;
        } else if (correction.type === 'deletion') {
            // Deletion: show what was said with highlight (this sound is missing/wrong)
            html += `<span class="error-deletion" ${dataAttr} title="This sound is missing or incorrect">${errorText}</span>`;
        } else if (correction.type === 'substitution') {
            // Substitution: show incorrect pronunciation
            html += `<span class="error-substitution" ${dataAttr} title="Incorrect pronunciation">${errorText}</span>`;
        }
        
        if (hasViseme) visemeIndex++;
        lastIndex = correction.end_index;
    });
    
    // Add remaining correct text
    if (lastIndex < sentence.length) {
        html += `<span class="correct-text">${sentence.substring(lastIndex)}</span>`;
    }
    
    return html;
}

// Update progress bar
function updateProgress(percentage) {
    progress.style.width = `${percentage}%`;
}

// Utility function to convert audio blob to base64 (useful for API calls)
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}
