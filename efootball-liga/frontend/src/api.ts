const API_URL = "http://localhost:8000";

export async function getLeagues() {
  const response = await fetch(
    ${API_URL}/api/leagues
  );

  if (!response.ok) {
    throw new Error("Ligalarni olishda xatolik");
  }

  return response.json();
}

export async function getTeams(
  league?: string
) {
  const url = league
    ? ${API_URL}/api/teams?league=${encodeURIComponent(
        league
      )}
    : ${API_URL}/api/teams;

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(
      "Jamoalarni olishda xatolik"
    );
  }

  return response.json();
}

export async function selectTeam(
  teamId: number,
  telegramId: number
) {
  const response = await fetch(
    ${API_URL}/api/teams/${teamId}/select?telegram_id=${telegramId},
    {
      method: "POST"
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Jamoani tanlashda xatolik"
    );
  }

  return data;
}

export async function getMyTeam(
  telegramId: number,
  seasonId: number
) {
  const response = await fetch(
    ${API_URL}/api/my-team?telegram_id=${telegramId}&season_id=${seasonId}
  );

   if (!response.ok) {
    throw new Error(
      "Jamoangizni olishda xatolik"
    );
  }

  return response.json();
}

export async function getStandings(
  seasonId: number
) {
  const response = await fetch(
    ${API_URL}/api/standings?season_id=${seasonId}
  );

  if (!response.ok) {
    throw new Error(
      "Jadvalni olishda xatolik"
    );
  }

  return response.json();
}

export async function getMyMatches(
  telegramId: number,
  seasonId: number,
  roundNumber?: number
) {
  let url =
    ${API_URL}/api/my-matches +
    ?telegram_id=${telegramId} +
    &season_id=${seasonId};

   if (roundNumber) {
    url += &round_number=${roundNumber};
  }

  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(
      "O'yinlarni olishda xatolik"
    );
  }

  return response.json();
}

export async function submitResult(
  telegramId: number,
  matchId: number,
  homeGoals: number,
  awayGoals: number
) {
  const response = await fetch(
    ${API_URL}/api/results?telegram_id=${telegramId},
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        match_id: matchId,
        home_goals: homeGoals,
        away_goals: awayGoals
      })
    }
  );

  const data = await response.json();

   if (!response.ok) {
    throw new Error(
      data.detail || "Natijani yuborishda xatolik"
    );
  }

  return data;
}

export async function confirmResult(
  telegramId: number,
  resultId: number
) {
  const response = await fetch(
    ${API_URL}/api/results/${resultId}/confirm?telegram_id=${telegramId},
    {
      method: "POST"
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Natijani tasdiqlashda xatolik"
    );
  }

  return data;
}

export async function rejectResult(
  telegramId: number,
  resultId: number
) {
  const response = await fetch(
    ${API_URL}/api/results/${resultId}/reject?telegram_id=${telegramId},
    {
      method: "POST"
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Natijani rad etishda xatolik"
    );
  }

  return data;
}

export async function getMessages(
  telegramId: number,
  recipientId?: number
) {
  let url =
    ${API_URL}/api/messages +
    ?telegram_id=${telegramId};

  if (recipientId) {
    url += &recipient_id=${recipientId};
  }

  const response = await fetch(url);

   if (!response.ok) {
    throw new Error(
      "Xabarlarni olishda xatolik"
    );
  }

  return response.json();
}

export async function sendMessage(
  telegramId: number,
  text: string,
  recipientId?: number
) {
  const response = await fetch(
    ${API_URL}/api/messages?telegram_id=${telegramId},
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json"
      },

      body: JSON.stringify({
        text,
        recipient_id: recipientId ?? null
      })
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
        "Xabar yuborishda xatolik"
    );
  }

  return data;
}
