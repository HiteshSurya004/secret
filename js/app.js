let participants = [];
let assignments = {};
let credentials = {};
let loggedInUser = null;

function registerParticipants() {
    if (loggedInUser !== "coordinator") {
        alert("Only the coordinator can register participants.");
        return;
    }
    // Add registration logic here...
}

// Add the rest of your JavaScript here
