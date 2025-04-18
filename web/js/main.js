document.addEventListener('DOMContentLoaded', () => {
    // Configuration
    const config = {
        refreshInterval: 60000,       // Refresh data every minute
        scoresPerPage: 8,             // Number of scores visible at once
        scrollDelay: 5000,            // Milliseconds before scrolling to next page
        machineDisplayTime: 10000,    // Time to display each machine (ms) - changed from 20000
        fadeTransitionTime: 800,      // Fade animation duration (ms)
        scrollSpeed: 40,              // Pixels per second for smooth scrolling
    };

    // Time windows for the quadrants
    const timeWindows = ['day', 'week', 'month', 'all'];

    // State variables
    let machines = [];
    let currentMachineIndex = 0;
    let allScores = {};
    let isScrolling = {};

    // DOM Elements
    const machineTitle = document.getElementById('machine-title');
    const clockElement = document.getElementById('clock');
    const statusMessage = document.getElementById('status-message');

    // Initialize scrolling state for each quadrant
    timeWindows.forEach(window => {
        isScrolling[window] = false;
    });

    // Initialize the application
    initApp();

    // Update clock every second
    setInterval(updateClock, 1000);

    async function initApp() {
        updateClock();
        try {
            await loadMachines();
            if (machines.length > 0) {
                await loadAndDisplayAllTimeWindows(machines[0].id);

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

    async function loadAndDisplayAllTimeWindows(machineId) {
        try {
            // Get the current machine
            const currentMachine = machines.find(m => m.id === machineId);

            // Update machine title
            machineTitle.textContent = currentMachine.title;

            // Initialize scores cache for this machine if needed
            if (!allScores[machineId]) {
                allScores[machineId] = {};
            }

            // Load scores for each time window in parallel
            const loadPromises = timeWindows.map(window => loadTimeWindowScores(machineId, window));
            await Promise.all(loadPromises);

            statusMessage.textContent = `Showing scores for ${currentMachine.title}`;
        } catch (error) {
            showError(`Failed to load scores: ${error.message}`);
        }
    }

    async function loadTimeWindowScores(machineId, timeWindow) {
        try {
            // Fetch scores for the machine if we don't have them cached
            if (!allScores[machineId][timeWindow]) {
                const response = await fetch(`/api/machines/${machineId}/highscores?time_window=${timeWindow}`);

                if (!response.ok) {
                    throw new Error(`HTTP error ${response.status}`);
                }

                allScores[machineId][timeWindow] = await response.json();
            }

            // Display scores for this time window
            displayScores(allScores[machineId][timeWindow], timeWindow);

        } catch (error) {
            showError(`Failed to load ${timeWindow} scores: ${error.message}`);
        }
    }

    function displayScores(scores, timeWindow) {
        // Get the appropriate scores body element
        const scoresBody = document.getElementById(`${timeWindow}-scores-body`);

        // Clear existing scores
        scoresBody.innerHTML = '';

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
        appendScoresToTable(initialScores, scoresBody);

        // If we have more scores than fit on a page, set up scrolling
        if (scores.length > config.scoresPerPage) {
            setTimeout(() => {
                scrollScores(scores, timeWindow);
            }, config.scrollDelay);
        }
    }

    function appendScoresToTable(scores, scoresBody) {
        scores.forEach((score, index) => {
            const position = index + 1 + Math.floor(scoresBody.children.length / config.scoresPerPage) * config.scoresPerPage;

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

    function scrollScores(scores, timeWindow) {
        const scoresContainer = document.querySelector(`#${timeWindow}-scores-body`).closest('.scores-container');

        if (isScrolling[timeWindow] || scores.length <= config.scoresPerPage) return;

        isScrolling[timeWindow] = true;
        const table = scoresContainer.querySelector('table');
        const totalHeight = table.scrollHeight - scoresContainer.clientHeight;

        if (totalHeight <= 0) {
            isScrolling[timeWindow] = false;
            return;
        }

        // If already at bottom, reset to top with animation
        if (scoresContainer.scrollTop >= totalHeight - 5) {
            // Fade out
            table.classList.add('fade-out');

            // Wait for animation to complete then reset
            setTimeout(() => {
                scoresContainer.scrollTop = 0;
                table.classList.remove('fade-out');
                table.classList.add('fade-in');

                setTimeout(() => {
                    table.classList.remove('fade-in');
                    isScrolling[timeWindow] = false;
                }, config.fadeTransitionTime);
            }, config.fadeTransitionTime);

            return;
        }

        // Smooth scroll down
        const scrollAmount = Math.min(30, totalHeight - scoresContainer.scrollTop);
        scoresContainer.scrollTop += scrollAmount;

        // Continue scrolling
        setTimeout(() => {
            isScrolling[timeWindow] = false;
            scrollScores(scores, timeWindow);
        }, 1000); // Scroll a bit every second for smooth effect
    }

    async function rotateToNextMachine() {
        // Fade out current content
        document.getElementById('leaderboard-container').style.opacity = '0';

        setTimeout(async () => {
            // Update machine index
            currentMachineIndex = (currentMachineIndex + 1) % machines.length;

            // Load the next machine's scores for all time windows
            await loadAndDisplayAllTimeWindows(machines[currentMachineIndex].id);

            // Fade in new content
            document.getElementById('leaderboard-container').style.opacity = '1';

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
                await loadAndDisplayAllTimeWindows(machines[currentMachineIndex].id);
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
