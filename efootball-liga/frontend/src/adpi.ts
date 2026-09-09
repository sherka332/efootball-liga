const API_URL = "http://localhost:8000";

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string;
        ready: () => void;
        expand: () => void;
      };
    };
  }
}

function getInitData(): string {
  const initData = window.Telegram?.WebApp?.initData;

  if (!initData) {
    throw new Error(
      "Telegram Mini App ma'lumotlari topilmadi."
    );
  }

return initData;
}

function authQuery(): string {
  return init_data=${encodeURIComponent(getInitData())};
}

async function request<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(url, options);

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail || "Serverda xatolik yuz berdi."
    );
  }

return data;
}


// ===============================
// AUTH
// ===============================

export async function authTelegram() {
  return request(
    ${API_URL}/api/auth/telegram?${authQuery()},
    {
      method: "POST",
    }
  );
}

// ===============================
// LEAGUES
// ===============================

export async function getLeagues() {
  return request<any[]>(
    ${API_URL}/api/leagues
  );
}

// ===============================
// SEASONS
// ===============================

export async function getActiveSeason(
  leagueId: number
) {
  return request<any>(
    ${API_URL}/api/leagues/${leagueId}/season
  );
}

// ===============================
// TEAMS
// ===============================

export async function getTeams(
  seasonId: number
) {
  return request<any[]>(
    ${API_URL}/api/seasons/${seasonId}/teams
  );
}

export async function selectTeam(
  seasonId: number,
  teamId: number
) {
  return request<any>(
    ${API_URL}/api/seasons/${seasonId}/teams/${teamId}/select?${authQuery()},
    {
      method: "POST",
    }
  );
}

export async function getMyTeam(
  seasonId: number
) {
  return request<any>(
    ${API_URL}/api/seasons/${seasonId}/my-team?${authQuery()}
  );
}

// ===============================
// MATCHES
// ===============================

export async function getMyMatches(
  seasonId: number
) {
  return request<any[]>(
    ${API_URL}/api/seasons/${seasonId}/my-matches?${authQuery()}
  );
}

export async function getRoundMatches(
  seasonId: number,
  roundNumber: number
) {
  return request<any[]>(
    ${API_URL}/api/seasons/${seasonId}/round/${roundNumber}
  );
}

// ===============================
// RESULTS
// ===============================

export async function submitResult(
  matchId: number,
  homeGoals: number,
  awayGoals: number
) {
  return request<any>(
    ${API_URL}/api/results?${authQuery()},
    {
      method: "POST",

        headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        match_id: matchId,
        home_goals: homeGoals,
        away_goals: awayGoals,
      }),
    }
  );
}

export async function confirmResult(
  resultId: number
) {
  return request<any>(
    ${API_URL}/api/results/${resultId}/confirm?${authQuery()},
    {
      method: "POST",
    }
  );
}

export async function rejectResult(
  resultId: number
) {
  return request<any>(
    ${API_URL}/api/results/${resultId}/reject?${authQuery()},
    {
      method: "POST",
    }
  );
}

// ===============================
// STANDINGS
// ===============================

export async function getStandings(
  seasonId: number
) {
  return request<any[]>(
    ${API_URL}/api/seasons/${seasonId}/standings
  );
}

// ===============================
// CHAT
// ===============================

export async function getMessages(
  recipientId?: number
) {
  let url =
    ${API_URL}/api/messages?${authQuery()};

  if (recipientId !== undefined) {
    url += &recipient_id=${recipientId};
  }

export async function sendMessage(
  text: string,
  recipientId?: number
) {
  return request<any>(
    ${API_URL}/api/messages?${authQuery()},
    {
      method: "POST",

        headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        text,
        recipient_id:
          recipientId ?? null,
      }),
    }
  );
}

// ===============================
// TELEGRAM APP
// ===============================

export function initializeTelegramWebApp() {
  const webApp =
    window.Telegram?.WebApp;

  if (!webApp) {
    return;
  }

  webApp.ready();
  webApp.expand();
}
