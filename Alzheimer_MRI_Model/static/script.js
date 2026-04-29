document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const previewArea = document.getElementById('preview-area');
    const imagePreview = document.getElementById('image-preview');
    const fileNameDisplay = document.getElementById('file-name');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resetBtn = document.getElementById('reset-btn');
    const btnLoader = document.getElementById('btn-loader');
    
    const resultsCard = document.getElementById('results-card');
    const diagnosisBadge = document.getElementById('diagnosis-badge');
    const diagnosisText = document.getElementById('diagnosis-text');
    const confidenceBar = document.getElementById('confidence-bar');
    const confidenceValue = document.getElementById('confidence-value');
    const timeValue = document.getElementById('time-value');

    let selectedFile = null;

    // Drag and Drop Handlers
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        selectedFile = file;
        fileNameDisplay.textContent = file.name;
        
        // Hide upload area, show preview
        uploadArea.classList.add('hidden');
        previewArea.classList.remove('hidden');
        resultsCard.classList.add('hidden');

        // Show image preview if it's an image
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        } else {
            // For NIfTI files, show a generic icon or hide preview
            imagePreview.src = '';
            imagePreview.classList.add('hidden');
        }
    }

    resetBtn.addEventListener('click', () => {
        selectedFile = null;
        fileInput.value = '';
        uploadArea.classList.remove('hidden');
        previewArea.classList.add('hidden');
        resultsCard.classList.add('hidden');
        imagePreview.src = '';
    });

    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // UI Loading State
        analyzeBtn.disabled = true;
        btnLoader.classList.remove('hidden');
        analyzeBtn.querySelector('span').textContent = 'Analyzing...';
        resultsCard.classList.add('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Analysis failed');
            }

            const data = await response.json();
            
            // Show Results
            displayResults(data);

        } catch (error) {
            console.error('Error:', error);
            alert('Failed to analyze the scan. Please try again.');
        } finally {
            analyzeBtn.disabled = false;
            btnLoader.classList.add('hidden');
            analyzeBtn.querySelector('span').textContent = 'Analyze Scan';
        }
    });

    function displayResults(data) {
        // Reset classes
        diagnosisBadge.className = 'diagnosis-badge';
        
        // Set Data
        let badgeClass = '';
        if (data.diagnosis === 'Cognitively Normal (CN)') {
            badgeClass = 'badge-cn';
            diagnosisText.textContent = 'Normal (CN)';
        } else if (data.diagnosis === 'Mild Cognitive Impairment (MCI)') {
            badgeClass = 'badge-mci';
            diagnosisText.textContent = 'MCI';
        } else {
            badgeClass = 'badge-ad';
            diagnosisText.textContent = "Alzheimer's (AD)";
        }
        
        diagnosisBadge.classList.add(badgeClass);
        
        const confPercent = (data.confidence * 100).toFixed(1);
        confidenceValue.textContent = confPercent + '%';
        timeValue.textContent = data.processing_time;

        // Show Card
        resultsCard.classList.remove('hidden');
        
        // Animate progress bar
        setTimeout(() => {
            confidenceBar.style.width = confPercent + '%';
        }, 100);
    }
});
