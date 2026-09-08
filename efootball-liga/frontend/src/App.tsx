import { useState } from "react";

type League = "laliga" | "premier";

const leagues = [
  {
    id: "laliga" as League,
    name: "La Liga",
    flag: "🇪🇸",
    country: "Ispaniya"
  },
  {
    id: "premier" as League,
    name: "Premier League",
    flag: "🏴",
    country: "Angliya"
  }
];
const demoTeams = {
  laliga: [
    "Athletic Club",
    "Atlético de Madrid",
    "CA Osasuna",
    "Celta",
    "Deportivo Alavés",
    "Elche CF",
    "FC Barcelona",
    "Getafe CF",
    "Levante UD",
    "Málaga CF",
    "R. Racing Club",
    "Rayo Vallecano",
    "RC Deportivo",
    "RCD Espanyol de Barcelona",
    "Real Betis",
    "Real Madrid",
    "Real Sociedad",
    "Sevilla FC",
    "Valencia CF",
    "Villarreal CF"
  ],

  premier: [
    "AFC Bournemouth",
    "Arsenal",
    "Aston Villa",
    "Brentford",
    "Brighton & Hove Albion",
    "Chelsea",
    "Coventry City",
    "Crystal Palace",
    "Everton",
    "Fulham",
    "Hull City",
    "Ipswich Town",
    "Leeds United",
    "Liverpool",
    "Manchester City",
    "Manchester United",
    "Newcastle United",
    "Nottingham Forest",
    "Sunderland",
    "Tottenham Hotspur"
  ]
};

function App() {
  const [league, setLeague] = useState<League | null>(null);
  const [page, setPage] = useState("home");

  const currentTeams = league
    ? demoTeams[league]
    : [];

  return (
    <div className="app">

      <header className="header">
        <div>
          <div className="logo">⚽ eFootball Liga</div>

          <div className="season">
            2026/27 mavsum
          </div>
        </div>

        <div className="user-icon">
          👤
        </div>
      </header>

      <main className="content">

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
                ⏱️ Natijalar har kuni 23:30 gacha
              </div>
            </section>

            <h2>
              Ligani tanlang
            </h2>

            <div className="league-grid">

              {leagues.map((item) => (
                <button
                  key={item.id}
                  className="league-card"
                  onClick={() => {
                    setLeague(item.id);
                    setPage("teams");
                  }}
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
              ))}

            </div>
          </>
        )}

        {page === "teams" && league && (
          <>
            <button
              className="back-button"
              onClick={() => setPage("home")}
            >
              ← Orqaga
            </button>

            <section className="page-title">
              <div className="big-flag">
                {league === "laliga" ? "🇪🇸" : "🏴"}
              </div>

              <div>
                <h1>
                  {league === "laliga"
                    ? "La Liga"
                    : "Premier League"}
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

            <div className="team-list">
              {currentTeams.map(
                (team, index) => (
                  <button
                    key={team}
                    className="team-card"
                    onClick={() =>
                      alert(
                        ${team} jamoasini tanlash keyingi bosqichda API orqali amalga oshiriladi.
                      )
            }
              >
                    <div className="team-number">
                      {index + 1}
                    </div>

                    <div className="team-logo">
                      ⚽
                    </div>

                    <div className="team-info">
                      <strong>
                        {team}
                      </strong>

                      <span>
                        Jamoa mavjud
                      </span>
                    </div>
              className="team-arrow">
                      →
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
          className={page === "home" ? "active" : ""}
          onClick={() => setPage("home")}
        >
          <span>🏠</span>
          <small>Bosh sahifa</small>
        </button>

        <button
          onClick={() =>
            alert("Jadval keyingi bosqichda ulanadi.")
          }
           >
          <span>🏆</span>
          <small>Jadval</small>
        </button>

        <button
          onClick={() =>
            alert("O'yinlar keyingi bosqichda ulanadi.")
          }
        >
          <span>🎮</span>
          <small>O'yinlar</small>
        </button>

         <button
          onClick={() =>
            alert("Chat keyingi bosqichda ulanadi.")
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

          
