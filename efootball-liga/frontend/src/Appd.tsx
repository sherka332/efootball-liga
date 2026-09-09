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
};

type Match = {
  id: number;
  round_number: number;
  home_team_id: number;
  away_team_id: number;
  status: string;
  deadline?: string | null;
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

type Page = "home" | "teams" | "matches" | "table" | "chat";

function App() {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null);
  const [season, setSeason] = useState<Season | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [myTeam, setMyTeam] = useState<Team | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [standings, setStandings] = useState<Standing[]>([]);
  const [page, setPage] = useState<Page>("home");
  const [loading, setLoading] = useState(true);
  const [selectingTeam, setSelectingTeam] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    initializeTelegramWebApp();
    loadInitialData();
  }, []);

  async function loadInitialData() {
    try {
      setLoading(true);
      setError("");
      await authTelegram();

      const leagueData = await getLeagues();
      setLeagues(leagueData);

      if (leagueData.length > 0) {
        await openLeague(leagueData[0]);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Ma'lumotlarni yuklashda xatolik."
      );
    } finally {
      setLoading(false);
    }
  }

  async function openLeague(league: League) {
    try {
      setError("");
      setSelectedLeague(league);

      const seasonData = await getActiveSeason(league.id);
      setSeason(seasonData);

      const teamData = await getTeams(seasonData.id);
      setTeams(teamData);

      try {
        const currentTeam = await getMyTeam(seasonData.id);
        setMyTeam(currentTeam);
      } catch {
        setMyTeam(null);
      }

      const matchData = await getMyMatches(seasonData.id);
      setMatches(matchData);

      const tableData = await getStandings(seasonData.id);
      setStandings(tableData);

      setPage("home");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Liga ma'lumotlarini yuklashda xatolik."
      );
    }
  }

  async function handleSelectTeam(teamId: number) {
    if (!season || selectingTeam) return;

    try {
      setSelectingTeam(true);
      setError("");

      const result = await selectTeam(season.id, teamId);
      setMyTeam(result);

      const updatedTeams = await getTeams(season.id);
      setTeams(updatedTeams);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Jamoani tanlashda xatolik."
      );
    } finally {
      setSelectingTeam(false);
    }
  }

  async function refreshData() {
    if (!season) return;

    try {
      setError("");

      const [teamData, matchData, tableData] = await Promise.all([
        getTeams(season.id),
        getMyMatches(season.id),
        getStandings(season.id),
      ]);

      setTeams(teamData);
      setMatches(matchData);
      setStandings(tableData);

      try {
        const currentTeam = await getMyTeam(season.id);
        setMyTeam(currentTeam);
      } catch {
        setMyTeam(null);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Ma'lumotlarni yangilashda xatolik."
      );
    }
  }

  if (loading) {
    return (
      <div className="app">
        <div className="loading">
          <div className="loading-spinner" />
          <p>Yuklanmoqda...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>⚽ eFootball Liga</h1>
          <p>
            {selectedLeague?.name ?? "Liga"}
            {season ? ` • ${season.name}` : ""}
          </p>
        </div>

        <button className="refresh-button" onClick={refreshData}>
          ↻
        </button>
      </header>

      {error && <div className="error-box">{error}</div>}

      {leagues.length > 1 && (
        <div className="league-switcher">
          {leagues.map((league) => (
            <button
              key={league.id}
              className={
                selectedLeague?.id === league.id
                  ? "league-button active"
                  : "league-button"
              }
              onClick={() => openLeague(league)}
            >
              {league.name}
            </button>
          ))}
        </div>
      )}

      <main className="content">
        {page === "home" && (
          <section>
            <div className="hero-card">
              <span className="hero-icon">🏆</span>
              <h2>{season?.name ?? "Mavsum"}</h2>
              <p>eFootball ligasiga xush kelibsiz!</p>
            </div>

            {myTeam ? (
              <div className="my-team-card">
                <span>🏟️</span>
                <div>
                  <small>Sizning jamoangiz</small>
                  <strong>{myTeam.name}</strong>
                </div>
              </div>
            ) : (
              <div className="notice-card">
                <h3>🏟️ Jamoangizni tanlang</h3>
                <p>
                  Ligada qatnashish uchun 20 ta jamoadan bittasini tanlang.
                </p>
                <button
                  className="primary-button"
                  onClick={() => setPage("teams")}
                >
                  Jamoa tanlash
                </button>
              </div>
            )}

            <div className="stats-grid">
              <div className="stat-card">
                <strong>20</strong>
                <span>Jamoa</span>
              </div>
              <div className="stat-card">
                <strong>38</strong>
                <span>Tur</span>
              </div>
              <div className="stat-card">
                <strong>380</strong>
                <span>O'yin</span>
              </div>
            </div>
          </section>
        )}

        {page === "teams" && (
          <section>
            <div className="section-title">
              <div>
                <h2>🏟️ Jamoalar</h2>
                <p>Bitta jamoani tanlang</p>
              </div>
            </div>

            <div className="team-grid">
              {teams.map((team) => {
                const taken =
                  team.participant_id !== null &&
                  team.participant_id !== undefined;

                const mine = myTeam?.id === team.id;

                return (
                  <button
                    key={team.id}
                    className={
                      mine
                        ? "team-card selected"
                        : taken
                        ? "team-card taken"
                        : "team-card"
                    }
                    disabled={taken || selectingTeam}
                    onClick={() => handleSelectTeam(team.id)}
                  >
                    <div className="team-logo">
                      {team.logo_url ? (
                        <img src={team.logo_url} alt={team.name} />
                      ) : (
                        <span>{team.short_name}</span>
                      )}
                    </div>

                    <strong>{team.name}</strong>

                    <small>
                      {mine ? "Sizniki" : taken ? "Band" : "Bo'sh"}
                    </small>
                  </button>
                );
              })}
            </div>
          </section>
        )}

        {page === "matches" && (
          <section>
            <div className="section-title">
              <div>
                <h2>⚽ O'yinlarim</h2>
                <p>Sizga tegishli uchrashuvlar</p>
              </div>
            </div>

            {!myTeam ? (
              <div className="empty-card">Avval jamoa tanlang.</div>
            ) : matches.length === 0 ? (
              <div className="empty-card">
                Hozircha o'yinlar mavjud emas.
              </div>
            ) : (
              <div className="matches-list">
                {matches.map((match) => {
                  const home = teams.find(
                    (team) => team.id === match.home_team_id
                  );

                  const away = teams.find(
                    (team) => team.id === match.away_team_id
                  );

                  return (
                    <div className="match-card" key={match.id}>
                      <div className="match-round">
                        {match.round_number}-tur
                      </div>

                      <div className="match-teams">
                        <span>{home?.name ?? "Jamoa"}</span>
                        <b>VS</b>
                        <span>{away?.name ?? "Jamoa"}</span>
                      </div>

                      <div
                        className={`match-status status-${match.status}`}
                      >
                        {match.status === "confirmed"
                          ? "✅ Tasdiqlangan"
                          : match.status === "completed"
                          ? "✅ Yakunlangan"
                          : match.status === "closed"
                          ? "🔒 Yopilgan"
                          : match.status === "disputed"
                          ? "⚠️ Nizo"
                          : "⏳ Kutilmoqda"}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        )}

        {page === "table" && (
          <section>
            <div className="section-title">
              <div>
                <h2>📊 Liga jadvali</h2>
                <p>{season?.name ?? "Mavsum"}</p>
              </div>
            </div>

            <div className="table-wrapper">
              <table className="standings-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Jamoa</th>
                    <th>O</th>
                    <th>G</th>
                    <th>D</th>
                    <th>M</th>
                    <th>GD</th>
                    <th>Ochko</th>
                  </tr>
                </thead>

                <tbody>
                  {standings.map((row) => (
                    <tr
                      key={row.team_id}
                      className={
                        myTeam?.id === row.team_id ? "my-row" : ""
                      }
                    >
                      <td>{row.position}</td>
                      <td>{row.team_name}</td>
                      <td>{row.played}</td>
                      <td>{row.wins}</td>
                      <td>{row.draws}</td>
                      <td>{row.losses}</td>
                      <td>{row.goal_difference}</td>
                      <td>
                        <strong>{row.points}</strong>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {page === "chat" && (
          <section>
            <div className="section-title">
              <div>
                <h2>💬 Chat</h2>
                <p>Liga ishtirokchilari bilan muloqot</p>
              </div>
            </div>

            <div className="empty-card">
              Chat tizimi keyingi bosqichda to'liq ulanadi.
            </div>
          </section>
        )}
      </main>

      <nav className="bottom-nav">
        <button
          className={page === "home" ? "nav-item active" : "nav-item"}
          onClick={() => setPage("home")}
        >
          <span>🏠</span>
          <small>Bosh sahifa</small>
        </button>

        <button
          className={page === "teams" ? "nav-item active" : "nav-item"}
          onClick={() => setPage("teams")}
        >
          <span>🏟️</span>
          <small>Jamoalar</small>
        </button>

        <button
          className={page === "matches" ? "nav-item active" : "nav-item"}
          onClick={() => setPage("matches")}
        >
          <span>⚽</span>
          <small>O'yinlar</small>
        </button>

        <button
          className={page === "table" ? "nav-item active" : "nav-item"}
          onClick={() => setPage("table")}
        >
          <span>📊</span>
          <small>Jadval</small>
        </button>

        <button
          className={page === "chat" ? "nav-item active" : "nav-item"}
          onClick={() => setPage("chat")}
        >
          <span>💬</span>
          <small>Chat</small>
        </button>
      </nav>
    </div>
  );
}

export default App;
