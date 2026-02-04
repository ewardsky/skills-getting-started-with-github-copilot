document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and reset activity select options
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Escape text to avoid accidental HTML injection
        function escapeHtml(str) {
          return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        }

        // Build participants section (no bullets) and include delete button for each participant
        let participantsHtml = '<div class="participants"><strong>Participants:</strong>';
        if (details.participants && details.participants.length) {
          participantsHtml += '<ul class="participants-list">';
          participantsHtml += details.participants
            .map(p => `<li><span class="participant-email">${escapeHtml(p)}</span><button class="delete-participant" data-email="${escapeHtml(p)}" data-activity="${escapeHtml(name)}" title="Remove participant">🗑️</button></li>`)
            .join("");
          participantsHtml += "</ul>";
        } else {
          participantsHtml += '<p class="no-participants">No participants yet.</p>';
        }
        participantsHtml += "</div>";

        activityCard.innerHTML = `
          <h4>${escapeHtml(name)}</h4>
          <p>${escapeHtml(details.description)}</p>
          <p><strong>Schedule:</strong> ${escapeHtml(details.schedule)}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHtml}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);

        // Handle delete participant clicks via event delegation
        activityCard.addEventListener("click", async (e) => {
          const btn = e.target.closest('.delete-participant');
          if (!btn) return;
          const email = btn.dataset.email;
          const activity = btn.dataset.activity;

          if (!email || !activity) return;

          try {
            const resp = await fetch(`/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`, {
              method: 'DELETE'
            });

            const result = await resp.json();

            if (resp.ok) {
              messageDiv.textContent = result.message;
              messageDiv.className = 'success';
              messageDiv.classList.remove('hidden');
              // Refresh activities to reflect change
              fetchActivities();
            } else {
              messageDiv.textContent = result.detail || 'Failed to remove participant';
              messageDiv.className = 'error';
              messageDiv.classList.remove('hidden');
            }

            setTimeout(() => messageDiv.classList.add('hidden'), 5000);
          } catch (err) {
            console.error('Error unregistering participant:', err);
            messageDiv.textContent = 'Failed to remove participant. Please try again.';
            messageDiv.className = 'error';
            messageDiv.classList.remove('hidden');
            setTimeout(() => messageDiv.classList.add('hidden'), 5000);
          }
        });
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        // Refresh activities list so the new participant appears immediately
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
