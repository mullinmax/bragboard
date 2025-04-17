document.addEventListener('DOMContentLoaded', () => {
    // Configuration
    const config = {
        refreshInterval: 60000,      // Refresh data every minute
        scoresPerPage: 10,           // Number of scores visible at once
        scrollDelay: 5000,           // Milliseconds before scrolling to next page
        scrollDuration: 1000,        // Scroll animation duration
        machineDisplayTime: 20000,   // Time to display each machine (ms)
        fadeTransitionTime: 800,     // Fade animation duration (ms)
    };

    // State variables
    let machines = [];
    let currentMachineIndex = 0;
    let allScores = {};
    let currentScores = [];
    let isScrolling = false;

    // DOM Elements
    const machineTitle = document.getElementById('machine-title');
    const scoresBody = document.getElementById('scores-body');
    const statusMessage = document.getElementById('status-message');
    const clockElement = document.getElementById('clock');

    // Initialize the application
    initApp();

    // Update clock every second
    setInterval(updateClock, 1000);

    async function initApp() {
        updateClock();
        try {
            await loadMachines();
            if (machines.length > 0) {
                await loadAndDisplayMachineScores(machines[0].id);

                // Set up rotation between machines
                if (machines.length > 1) {
                    setInterval(rotateToNextMachine, config.machineDisplayTime);
                }

                // Set up periodic data refresh
                setInterval(refreshData, config.refreshInterval);
            }
        } catch (error) {
            showError(`Failed to initialize: ${error.message}`);
        }
    }

    async function loadMachines() {
        try {
            statusMessage.textContent = 'Loading machines...';
            const response = await fetch('/api/machines/list');

            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }

            machines = await response.json();

            if (machines.length === 0) {
                machineTitle.textContent = 'No machines available';
                statusMessage.textContent = 'No arcade machines found';
            } else {
                statusMessage.textContent = `Loaded ${machines.length} machine(s)`;
            }

            return machines;
        } catch (error) {
            showError(`Failed to load machines: ${error.message}`);
            return [];
        }
    }

    async function loadAndDisplayMachineScores(machineId) {
        try {
            statusMessage.textContent = 'Loading scores...';

            // Fetch scores for the machine if we don't have them cached
            if (!allScores[machineId]) {
                const response = await fetch(`/api/machines/${machineId}/highscores`);

                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }

                allScores[machineId] = await response.json();
            }

            // Get the current machine
            const currentMachine = machines.find(m => m.id === machineId);

            // Update machine title
            machineTitle.textContent = currentMachine.title;

            // Display scores
            displayScores(allScores[machineId]);

            statusMessage.textContent = `Showing scores for ${currentMachine.title}`;

        } catch (error) {
            showError(`Failed to load scores: ${error.message}`);
        }
    }

    function displayScores(scores) {
        // Clear existing scores
        scoresBody.innerHTML = '';
        currentScores = scores;

        // If no scores
        if (!scores || scores.length === 0) {
            const row = document.createElement('tr');
            row.classList.add('score-row');
            row.innerHTML = `
                <td colspan="4" style="text-align: center;">No high scores yet!</td>
            `;
            scoresBody.appendChild(row);
            return;
        }

        // Display the initial page of scores with an animation
        const initialScores = scores.slice(0, config.scoresPerPage);
        appendScoresToTable(initialScores);

        // If we have more scores than fit on a page, set up scrolling
        if (scores.length > config.scoresPerPage) {
            setTimeout(() => {
                scrollScores();
            }, config.scrollDelay);
        }
    }

    function appendScoresToTable(scores) {
        scores.forEach((score, index) => {
            const position = scores === currentScores.slice(0, config.scoresPerPage) ?
                index + 1 : index + 1 + Math.floor(scoresBody.children.length / config.scoresPerPage) * config.scoresPerPage;

            const row = document.createElement('tr');
            row.classList.add('score-row', 'fade-in');

            // Add special class for top 3 ranks
            if (position <= 3) {
                row.classList.add(`rank-${position}`);
            }

            // Format the date
            const scoreDate = new Date(score.date);
            const formattedDate = scoreDate.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });

            // Format the score with commas
            const formattedScore = score.score.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

            row.innerHTML = `
                <td>${position}</td>
                <td>${score.initials || 'AAA'}</td>
                <td>${formattedScore}</td>
                <td>${formattedDate}</td>
            `;

            scoresBody.appendChild(row);

            // Trigger reflow for animation
            void row.offsetWidth;
        });
    }

    function scrollScores() {
        if (isScrolling || currentScores.length <= config.scoresPerPage) return;

        isScrolling = true;
        const totalScores = currentScores.length;
        const displayedRows = scoresBody.children.length;
        const totalPages = Math.ceil(totalScores / config.scoresPerPage);
        const currentPage = Math.floor(displayedRows / config.scoresPerPage);

        // If we're at the last page, reset to the first page
        if (currentPage >= totalPages - 1) {
            // Remove all rows with animation
            Array.from(scoresBody.children).forEach(row => {
                row.classList.add('fade-out');
            });

            // Wait for animation to complete then reset
            setTimeout(() => {
                scoresBody.innerHTML = '';
                displayScores(currentScores);
                isScrolling = false;
            }, config.fadeTransitionTime);
            return;
        }

        // Calculate next page of scores to show
        const nextPageStart = (currentPage + 1) * config.scoresPerPage;
        const nextPageEnd = Math.min(nextPageStart + config.scoresPerPage, totalScores);
        const nextPageScores = currentScores.slice(nextPageStart, nextPageEnd);

        // Smoothly scroll to the next set
        const currentHeight = scoresBody.scrollHeight;
        appendScoresToTable(nextPageScores);

        // Schedule the next scroll
        setTimeout(() => {
            isScrolling = false;
            scrollScores();
        }, config.scrollDelay);
    }

    async function rotateToNextMachine() {
        // Fade out current content
        document.getElementById('leaderboard-container').classList.add('fade-out');

        setTimeout(async () => {
            // Update machine index
            currentMachineIndex = (currentMachineIndex + 1) % machines.length;

            // Load the next machine's scores
            await loadAndDisplayMachineScores(machines[currentMachineIndex].id);

            // Fade in new content
            document.getElementById('leaderboard-container').classList.remove('fade-out');
            document.getElementById('leaderboard-container').classList.add('fade-in');

            // Remove the fade-in class after animation completes
            setTimeout(() => {
                document.getElementById('leaderboard-container').classList.remove('fade-in');
            }, config.fadeTransitionTime);

        }, config.fadeTransitionTime);
    }

    async function refreshData() {
        try {
            // Refresh machines list
            await loadMachines();

            // Clear cached scores to force refresh
            allScores = {};

            // Update current display
            if (machines.length > 0) {
                // Make sure current index is still valid
                currentMachineIndex = Math.min(currentMachineIndex, machines.length - 1);
                await loadAndDisplayMachineScores(machines[currentMachineIndex].id);
            }

            statusMessage.textContent = 'Data refreshed';
            // Clear status after 3 seconds
            setTimeout(() => {
                statusMessage.textContent = '';
            }, 3000);
        } catch (error) {
            showError(`Failed to refresh data: ${error.message}`);
        }
    }

    function showError(message) {
        console.error(message);
        statusMessage.textContent = message;
        statusMessage.style.color = 'var(--form-element-invalid-active-border-color)';

        // Reset style after 5 seconds
        setTimeout(() => {
            statusMessage.style.color = '';
        }, 5000);
    }

    function updateClock() {
        const now = new Date();
        clockElement.textContent = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }
});
