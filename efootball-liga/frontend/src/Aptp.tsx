import { useEffect, useState } from "react";

import {
  getTeams,
  selectTeam
} from "./api";

type League = "La Liga" | "Premier League";

type Team = {
  id: number;
  name: string;
  short_name: string;
  logo_url: string | null;
  participant_id: number | null;
  available: boolean;
};

const leagues: {
  name: League;
  flag: string;
  country: string;
}[] = [
  {
    name: "La Liga",
    flag: "🇪🇸",
    country: "Ispaniya"
  },
  {
    name: "Premier League",
    flag: "🏴",
    country: "Angliya"
  }
];

function App() {
  const [page, setPage] = useState<
    "home" | "teams"
  >("home");

  const [league, setLeague] =
    useState<League | null>(null);

  const [teams, setTeams] =
    useState<Team[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [success, setSuccess] =
    useState("");

  
  /*
   * Hozir test uchun Telegram ID.
   *
   * Telegram Mini App'ni ulagan
   * paytimizda bu qiymat avtomatik
   * Telegram WebApp'dan olinadi.
   */
  const telegramId = 123456789;

  async function loadTeams(
    selectedLeague: League
  ) {
    try {
      setLoading(true);
      setError("");
      setSuccess("");

      const data = await getTeams(
        selectedLeague
      );

       setTeams(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Jamoalarni yuklashda xatolik"
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleLeagueSelect(
    selectedLeague: League
  ) {
    setLeague(selectedLeague);
    setPage("teams");

    await loadTeams(
      selectedLeague
    );
  }

  async function handleTeamSelect(
    team: Team
  ) {
    if (!team.available) {
      setError(
        "Bu jamoani boshqa ishtirokchi tanlagan."
      );

      return;
    }

    const confirmed =
      window.confirm(
        ${team.name} jamoasini tanlaysizmi?
      );

    if (!confirmed) {
      return;
    }

    try {
      setLoading(true);
      setError("");
      setSuccess("");

      const data =
        await selectTeam(
          team.id,
          telegramId
        );

      setSuccess(
        data.message ||
          ${team.name} sizga biriktirildi.
      );

      await loadTeams(
        league!
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Jamoani tanlashda xatolik"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!league) {
      return;
    }

    loadTeams(league);
  }, []);

  return (
    <div className="app">

      <header className="header">

        <div>
          <div className="logo">
            ⚽ eFootball Liga
          </div>

          <div className="season">
            2026/27 mavsum
          </div>
        </div>

        <div className="user-icon">
          👤
        </div>

      </header>

      <main className="content">

        {error && (
          <div className="error-box">
            ❌ {error}
          </div>
        )}

        {success && (
          <div className="success-box">
            ✅ {success}
          </div>
        )}

        {page === "home" && (
          <>
            <section className="hero">

              <h1>
                🏆 eFootball Liga
              </h1>

              <p>
                Haqiqiy liga formatida
                raqobatlashing!
              </p>

              <div className="deadline">
                ⏱️ Natijalar 23:30 gacha
              </div>

               </section>

            <h2>
              Ligani tanlang
            </h2>

            <div className="league-grid">

              {leagues.map(
                (item) => (
                  <button
                    key={item.name}
                    className="league-card"
                    onClick={() =>
                      handleLeagueSelect(
                        item.name
                      )
                    }
                  >
                    <div className="league-flag">
                      {item.flag}
                    </div>

                    <div className="league-name">
                      {item.name}
                    </div>

                    <div className="league-country">
                      {item.country}
                    </div>

                    <div className="league-arrow">
                      →
                    </div>

                  </button>
                )
              )}

              </div>
          </>
        )}

        {page === "teams" &&
          league && (
            <>

              <button
                className="back-button"
                onClick={() => {
                  setPage("home");
                  setLeague(null);
                  setTeams([]);
                  setError("");
                  setSuccess("");
                }}
              >
                ← Orqaga
              </button>

               <section className="page-title">

                <div className="big-flag">
                  {league === "La Liga"
                    ? "🇪🇸"
                    : "🏴"}
                </div>

                <div>
                  <h1>
                    {league}
                  </h1>

                  <p>
                    Jamoangizni tanlang
                  </p>
                </div>

              </section>

               <div className="info-box">
                ℹ️ Har bir jamoani faqat
                <b> bitta ishtirokchi </b>
                tanlashi mumkin.
              </div>

              {loading && (
                <div className="loading">
                  ⏳ Yuklanmoqda...
                </div>
              )}

              {!loading &&
                teams.length === 0 && (
                  <div className="empty-box">
                    Hozircha jamoalar
                    topilmadi.
                  </div>
                )}

              <div className="team-list">

                {teams.map(
                  (team, index) => (
                    <button
                      key={team.id}
                      className={team-card ${
                        !team.available
                          ? "team-disabled"
                          : ""
                      }}
                      onClick={() =>
                        handleTeamSelect(
                          team
                        )
                      }
                      disabled={
                        !team.available ||
                        loading
                      }
                    >

                      <div className="team-number">
                        {index + 1}
                      </div>

                      <div className="team-logo">

                        {team.logo_url ? (
                          <img
                            src={
                              team.logo_url
                            }
                            alt={
                              team.name
                            }
                          />
                        ) : (
                          "⚽"
                        )}

                      </div>

                      <div className="team-info">

                        <strong>
                          {team.name}
                        </strong>

                        <span
                          className={
                            team.available
                              ? "available"
                              : "taken"
                          }
                          >
                          {team.available
                            ? "Bo'sh"
                            : "Band"}
                        </span>

                      </div>

                      <div className="team-arrow">
                        {team.available
                          ? "→"
                          : "🔒"}
                      </div>

                    </button>
                  )
                )}

                </div>

            </>
          )}

      </main>

      <nav className="bottom-nav">

        <button
          className={
            page === "home"
              ? "active"
              : ""
          }
          onClick={() => {
            setPage("home");
            setLeague(null);
            setError("");
            setSuccess("");
          }}
        >
          <span>🏠</span>
          <small>
            Bosh sahifa
          </small>
        </button>

        <button
          onClick={() =>
            setError(
              "Jadval keyingi bosqichda ulanadi."
            )
          }
          >
          <span>🏆</span>
          <small>Jadval</small>
        </button>

        <button
          onClick={() =>
            setError(
              "O'yinlar keyingi bosqichda ulanadi."
            )
          }
        >
          <span>🎮</span>
          <small>O'yinlar</small>
        </button>

        <button
          onClick={() =>
            setError(
              "Chat keyingi bosqichda ulanadi."
            )
          }
           >
          <span>💬</span>
          <small>Chat</small>
        </button>

      </nav>

    </div>
  );
}

export default App;

          
