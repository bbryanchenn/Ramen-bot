const DISCORD_WEBHOOK_URL = "";

function onFormSubmit(e) {
  const itemResponses = e.response.getItemResponses();

  let discordId = "Unknown";

  itemResponses.forEach(item => {
    const question = item.getItem().getTitle().toLowerCase();

    if (question.includes("discord id")) {
      discordId = item.getResponse().toString().trim();
    }
  });

  const payload = {
    content: `Survey submitted by ${discordId !== "Unknown" ? `<@${discordId}>` : "Unknown"}`,
    embeds: [
      {
        title: "Survey Submitted",
        color: 0x57F287,
        fields: [
          {
            name: "User",
            value: discordId !== "Unknown" ? `<@${discordId}>` : "Unknown",
            inline: true
          },
          {
            name: "Discord ID",
            value: discordId,
            inline: true
          },
          {
            name: "Submitted At",
            value: new Date().toLocaleString(),
            inline: false
          }
        ]
      }
    ]
  };

  const res = UrlFetchApp.fetch(DISCORD_WEBHOOK_URL, {
    method: "post",
    contentType: "application/json",
    headers: {
      "User-Agent": "GoogleAppsScript-SurveyBot/1.0"
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  console.log("Status:", res.getResponseCode());
  console.log("Response:", res.getContentText());
}

function testWebhook() {
  const payload = {
    content: "Manual webhook test"
  };

  const res = UrlFetchApp.fetch(DISCORD_WEBHOOK_URL, {
    method: "post",
    contentType: "application/json",
    headers: {
      "User-Agent": "GoogleAppsScript-SurveyBot/1.0"
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });

  console.log("Status:", res.getResponseCode());
  console.log("Response:", res.getContentText());
}