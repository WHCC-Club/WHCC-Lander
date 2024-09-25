// Define the username variable
document.addEventListener('DOMContentLoaded', function() {
    const inputElement = document.getElementById('input'); // Select the input element
    const username = inputElement.getAttribute('data-username') || 'guest'; // Default to 'guest' if not set

    inputElement.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            const command = event.target.value;
            processCommand(command);
            event.target.value = ''; // Clear the input field
        }
    });

    // Store the username in a closure so it can be accessed later
    window.username = username;
});

// Define the commands object
const commands = {
    help: `
Available commands:
  about    - Learn more about WHCC
  events   - See upcoming events
  ctf      - Learn about our Capture The Flag events
  clear    - Clear the terminal screen
  contact  - Contact us for more info
  join     - How to join WHCC
  login    - Log in to your account
    `,
    about: `
The White Hat Cyber Crew (WHCC) is a BCIT student club focused on ethical hacking,
cybersecurity, and providing a platform for students to engage in Capture The Flag (CTF) competitions.
We aim to foster a community of learners who are passionate about hacking ethically and enhancing their
skills through hands-on challenges and events.

We are a fairly new club, but we are growing fast! Our members range from beginners to experienced
security enthusiasts.
    `,
    events: `
Upcoming Events:
  - CTF #1: Intro to CTF, Date: Oct 15th, 2024
  - Workshop: Getting Started with Ethical Hacking, Date: Oct 20th, 2024
  - CTF #2: Hack the Planet!, Date: Nov 1st, 2024

For more details, visit our website or Discord!
    `,
    ctf: `
Capture The Flag (CTF) is a cybersecurity competition where participants solve challenges related
to ethical hacking, reverse engineering, cryptography, and forensics. WHCC hosts regular CTFs
for members and the broader student community to practice their skills and compete against others.

Join our next CTF and test your hacking skills!
    `,
    contact: `
Contact Us:
  - Email: whcc@bcit.ca
  - Discord: Join our server for real-time updates and discussion.
  - Instagram: @whcc_bcit
    `,
    join: `
To join WHCC, simply:
  - Attend any of our events or workshops
  - Join our Discord server (link on our website)
  - Register on our platform to participate in CTFs

We welcome all skill levels, so come learn, hack, and grow with us!
    `,
    clear: '', // Clears the terminal
    login: function() {
        window.location.href = '/login'; // Redirect to login page
    }
};

// Function to append output to the terminal
function appendOutput(command, message) {
    const outputDiv = document.getElementById('output');
    const prompt = `<span class="prompt">${window.username}<span class="domain">@whcc.club</span>:~$ </span>`; // Use the username from the window object

    // Append the command and its output
    outputDiv.innerHTML += `<pre class="text">${prompt}${command}\n${message}</pre>`;
    outputDiv.scrollTop = outputDiv.scrollHeight; // Scroll to the bottom
}

// Handle command input
function processCommand(command) {
    const cmd = command.trim().toLowerCase();
    let message = '';

    if (commands[cmd]) {
        if (cmd === 'clear') {
            document.getElementById('output').innerHTML = ''; // Clear the terminal screen
            return; // Early return
        } else if (typeof commands[cmd] === 'function') {
            commands[cmd](); // Execute the command function
            return; // Early return
        } else {
            message = commands[cmd]; // Store the output message
        }
    } else {
        message = `Command not found: ${cmd}`;
    }

    appendOutput(command, message); // Call appendOutput with command and message
}
