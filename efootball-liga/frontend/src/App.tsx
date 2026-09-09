import { useEffect, useState } from "react";

import {
  authTelegram,
  getLeagues,
  getActiveSeason,
  getTeams,
  getMyTeam,
  getMyMatches,
  getStandings,
  initializeTelegramWebApp,
  selectTeam,
  submitResult,
  confirmResult,
  rejectResult,
  getMessages,
  sendMessage,
} from "./api";

type League = {
  id: number;
  name: string;
  country: string;
  active: boolean;
};

type Season = {
  id: number;
  league_id: number;
  name: string;
  active: boolean;
  deadline_hour: number;
  deadline_minute: number;
};

type Team = {
  id: number;
  name: string;
  short_name: string;
  logo_url?: string | null;
  participant_id?: number | null;
  blocked?: boolean;
  available?: boolean;
};

type MatchResult = {
  id: number;
  home_goals: number;
  away_goals: number;
  submitted_by: number;
  confirmed_by?: number | null;
  submitted_at?: string;
  confirmed_at?: string | null;
};

type Match = {
  id: number;
  round_number: number;
  home_team_id: number;
  away_team_id: number;
  home_team_name?: string;
  away_team_name?: string;
  status: string;
  deadline?: string | null;
  result?: MatchResult | null;
};

type Standing = {
  position: number;
  team_id: number;
  team_name: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
};

type Message = {
  id: number;
  sender_id: number;
  recipient_id?: number | null;
  text: string;
  created_at?: string;
};

type Page = "home" | "teams" | "matches" | "table" | "chat";

function App() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] =
    useState<League | null>(null);
  const [season, setSeason] =
    useState<Season | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [myTeam, setMyTeam] =
    useState<Team | null>(null);
  const [matches, setMatches] =
    useState<Match[]>([]);
  const [standings, setStandings] =
    useState<Standing[]>([]);
  const [messages, setMessages] =
    useState<Message[]>([]);

  const [page, setPage] =
    useState<Page>("home");
  const [loading, setLoading] =
    useState(true);
  const [selectingTeam, setSelectingTeam] =
    useState<number | null>(null);
  const [actionLoading, setActionLoading] =
    useState<number | null>(null);
  const [error, setError] =
    useState("");

const [userId, setUserId] =
    useState<number | null>(null);

  const [scoreInputs, setScoreInputs] =
    useState<
      Record<
        number,
        { home: string; away: string }
      >
    >({});

  const [messageText, setMessageText] =
    useState("");
  const [chatLoading, setChatLoading] =
    useState(false);

  useEffect(() => {
    initializeTelegramWebApp();
    loadInitialData();
  }, []);

  useEffect(() => {
    if (page === "chat") {
      loadChat();
    }
  }, [page]);

  async function loadInitialData() {
    try {
      setLoading(true);
      setError("");

      const auth = await authTelegram();

          if (auth?.id) {
        setUserId(Number(auth.id));
      }

      const leagueList = await getLeagues();
      setLeagues(leagueList);

      if (leagueList.length > 0) {
        await openLeague(leagueList[0]);
      } else {
        setError("Faol liga topilmadi.");
      }
    } catch (err: any) {
      setError(
        err?.message ||
          "Ma'lumotlarni yuklashda xatolik."
      );
    } finally {
      setLoading(false);
    }
  }

async function openLeague(league: League) {
    try {
      setSelectedLeague(league);

      const activeSeason =
        await getActiveSeason(league.id);

      setSeason(activeSeason);

      const [
        teamList,
        currentTeam,
        matchList,
        standingList,
      ] = await Promise.all([
        getTeams(activeSeason.id),
        getMyTeam(activeSeason.id),
        getMyMatches(activeSeason.id),
        getStandings(activeSeason.id),
      ]);

  setTeams(teamList);
      setMyTeam(currentTeam);
      setMatches(matchList);
      setStandings(standingList);
      setPage("home");
    } catch (err: any) {
      setError(
        err?.message ||
          "Liga ma'lumotlarini yuklashda xatolik."
      );
    }
  }

  async function refreshData() {
    if (!season) return;

    try {
      setError("");

    const [
        teamList,
        currentTeam,
        matchList,
        standingList,
      ] = await Promise.all([
        getTeams(season.id),
        getMyTeam(season.id),
        getMyMatches(season.id),
        getStandings(season.id),
      ]);

      setTeams(teamList);
      setMyTeam(currentTeam);
      setMatches(matchList);
      setStandings(standingList);
    } catch (err: any) {
      setError(
        err?.message ||
          "Yangilashda xatolik."
      );
    }
  }

async function handleSelectTeam(
    teamId: number
  ) {
    if (!season) return;

    try {
      setSelectingTeam(teamId);
      setError("");

      const result = await selectTeam(
        season.id,
        teamId
      );

      setMyTeam(result);

      const teamList =
        await getTeams(season.id);

      setTeams(teamList);
      setPage("home");
    } catch (err: any) {
      setError(
        err?.message ||
          "Jamoani tanlashda xatolik."
      );
    } finally {
      setSelectingTeam(null);
    }
}

function updateScore(
    matchId: number,
    side: "home" | "away",
    value: string
  ) {
    setScoreInputs((prev) => ({
      ...prev,
      [matchId]: {
        home: prev[matchId]?.home ?? "",
        away: prev[matchId]?.away ?? "",
        [side]: value.replace(
          /[^0-9]/g,
          ""
        ),
      },
    }));
  }

  async function handleSubmitResult(
    match: Match
  ) {
    const input = scoreInputs[match.id];

    if (!input?.home || !input?.away) {
      setError(
        "Avval ikkala hisobni ham kiriting."
      );
      return;
    }

  const homeGoals = Number(input.home);
    const awayGoals = Number(input.away);

    if (
      !Number.isInteger(homeGoals) ||
      !Number.isInteger(awayGoals) ||
      homeGoals < 0 ||
      awayGoals < 0
    ) {
      setError(
        "Hisob 0 yoki undan katta butun son bo‘lishi kerak."
      );
      return;
    }

    try {
      setActionLoading(match.id);
      setError("");

      await submitResult(
        match.id,
        homeGoals,
        awayGoals
      );

    setScoreInputs((prev) => {
        const next = { ...prev };
        delete next[match.id];
        return next;
      });

      await refreshData();
    } catch (err: any) {
      setError(
        err?.message ||
          "Natijani yuborishda xatolik."
      );
    } finally {
      setActionLoading(null);
    }
  }

async function handleConfirmResult(
    resultId: number
  ) {
    try {
      setActionLoading(resultId);
      setError("");

      await confirmResult(resultId);
      await refreshData();
    } catch (err: any) {
      setError(
        err?.message ||
          "Natijani tasdiqlashda xatolik."
      );
    } finally {
      setActionLoading(null);
    }
}

async function handleRejectResult(
    resultId: number
  ) {
    try {
      setActionLoading(resultId);
      setError("");

      await rejectResult(resultId);
      await refreshData();
    } catch (err: any) {
      setError(
        err?.message ||
          "Natijani rad etishda xatolik."
      );
    } finally {
      setActionLoading(null);
    }
}

async function loadChat() {
    try {
      setChatLoading(true);

      const result = await getMessages();

      setMessages(result || []);
    } catch (err: any) {
      setError(
        err?.message ||
          "Chatni yuklashda xatolik."
      );
    } finally {
      setChatLoading(false);
    }
  }

  async function handleSendMessage() {
    const text = messageText.trim();

    if (!text) return;

  try {
      setChatLoading(true);
      setError("");

      await sendMessage(text);

      setMessageText("");

      await loadChat();
    } catch (err: any) {
      setError(
        err?.message ||
          "Xabar yuborishda xatolik."
      );
    } finally {
      setChatLoading(false);
    }
  }

  function getTeamName(teamId: number) {
    const team = teams.find(
      (item) => item.id === teamId
    );

  return (
      team?.name ||
      Team #${teamId}
    );
  }

  function getTeamLogo(teamId: number) {
    const team = teams.find(
      (item) => item.id === teamId
    );

    return team?.logo_url || "";
  }

function statusText(status: string) {
    switch (status) {
      case "confirmed":
        return "Tasdiqlangan";
      case "pending_confirmation":
        return "Tasdiq kutilmoqda";
      case "disputed":
        return "Bahsli";
      case "completed":
        return "Tugagan";
      case "closed":
        return "Yopilgan";
      default:
        return "Kutilmoqda";
    }
}

function statusIcon(status: string) {
    switch (status) {
      case "confirmed":
        return "✅";
      case "pending_confirmation":
        return "⏳";
      case "disputed":
        return "⚠️";
      case "completed":
        return "🏁";
      default:
        return "🕐";
    }
}

function formatDate(
    date?: string | null
  ) {
    if (!date) return "";

    try {
      return new Date(date).toLocaleString(
        "uz-UZ",
        {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        }
      );
    } catch {
      return "";
    }
}

