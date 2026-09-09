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
    throw new Error("Telegram Mini App ma'lumotlari topilmadi.");
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

  let data: any = null;

  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(
      data?.detail ||
        data?.message ||
        "Serverda xatolik yuz berdi."
    );
  }

  return data as T;
}

export async function authTelegram() {
  return request(
    ${API_URL}/api/auth/telegram?${authQuery()},
    {
      method: "POST",
    }
  );
}

export async function getLeagues() {
  return request<any[]>(
    ${API_URL}/api/leagues
  );
}

export async function getActiveSeason(leagueId: number) {
  const seasons = await request<any[]>(
    ${API_URL}/api/seasons?league_id=${leagueId}
  );

  const activeSeason = seasons.find(
    (season) => season.active
  );

  if (!activeSeason) {
    throw new Error(
      "Bu liga uchun faol mavsum topilmadi."
    );
  }

  return activeSeason;
}

export async function getTeams(seasonId: number) {
  return request<any[]>(
    ${API_URL}/api/teams?season_id=${seasonId}
  );
}

export async function selectTeam(
  seasonId: number,
  teamId: number
) {
  // seasonId backend endpointida kerak emas,
  // lekin App.tsx bilan mos bo'lishi uchun argument sifatida qoldirildi.
  void seasonId;

  return request<any>(
    ${API_URL}/api/teams/${teamId}/select?${authQuery()},
    {
      method: "POST",
    }
  );
}

export async function selectTeam(
  seasonId: number,
  teamId: number
) {
  void seasonId;

  const data = await request<any>(
    `${API_URL}/api/teams/${teamId}/select?${authQuery()}`,
    {
      method: "POST",
    }
  );

  return data.team;
}

export async function getRoundMatches(
  seasonId: number,
  roundNumber: number
) {
  return request<any[]>(
    ${API_URL}/api/round/${roundNumber}?season_id=${seasonId}
  );
}

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

export async function getStandings(
  seasonId: number
) {
  return request<any[]>(
    ${API_URL}/api/standings?season_id=${seasonId}
  );
}

export async function getMessages(
  recipientId?: number
) {
  let url = ${API_URL}/api/messages?${authQuery()};

  if (recipientId !== undefined) {
    url += &recipient_id=${recipientId};
  }

  return request<any[]>(url);
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

export function initializeTelegramWebApp() {
  const webApp = window.Telegram?.WebApp;

  if (!webApp) return;

  webApp.ready();
  webApp.expand();
}
