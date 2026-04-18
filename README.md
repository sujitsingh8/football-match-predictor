# ⚽ Football Match Predictor

A terminal-based football match outcome predictor that uses head-to-head history, recent form, and expected goals (xG) to forecast results between top clubs.

---

## 📸 Demo

```
========================================================
           FOOTBALL MATCH PREDICTOR              
========================================================

  TOP 10 FOOTBALL TEAMS
  ----------------------------------------
   1.  Manchester City
   2.  Real Madrid
   ...

  Matchup  :  Real Madrid  (H)  vs  Liverpool  (A)
  ──────────────────────────────────────────────────────

  HEAD TO HEAD HISTORY
  Total Meetings   :  5
  Real Madrid           Wins :  4
  Draws                      :  1
  Liverpool             Wins :  0

  Last 5 Results :
    2019-06-01   Real Madrid        3 - 1  Liverpool         [UCL Final]
    2021-04-06   Liverpool          0 - 0  Real Madrid       [UCL]
    2021-04-14   Real Madrid        3 - 1  Liverpool         [UCL]
    2022-05-28   Real Madrid        1 - 0  Liverpool         [UCL Final]
    2024-03-05   Real Madrid        1 - 0  Liverpool         [UCL]

  PREDICTION RESULT
  Predicted Score   :  Real Madrid  2  -  1  Liverpool
  Expected xG       :  2.08  vs  1.31
  Predicted Outcome :  Real Madrid  WIN

  Win Probabilities :
    Real Madrid               51.2%   █████████████░░░░░░░░░░░░░
    Draw                      25.9%   ██████░░░░░░░░░░░░░░░░░░░░
    Liverpool                 22.9%   █████░░░░░░░░░░░░░░░░░░░░░
```

---

## 🧠 How It Works

The predictor combines three data sources into a weighted composite score:

| Component | Weight | Description |
|---|---|---|
| Recent Form | 55% | Last 5 matches per team, split by home/away venue |
| Expected Goals (xG) | 25% | Derived from goals scored/conceded averages |
| Head-to-Head History | 20% | All-time record with recency bias on last 4 meetings |

**Additional factors:**
- Home advantage boost (~8%) applied to the home team's attack and form rating
- Draw probability modelled from H2H draw rate + closeness of the two teams' strengths
- Predicted scoreline adjusted when win probability gap exceeds 12%

---

## 📁 Project Structure

```
football-match-predictor/
│
├── main.py              # CLI interface — team selection and match loop
├── predictor.py         # Core logic — data loading, algorithm, output display
│
└── data/
    ├── h2h_data.csv     # Head-to-head match records
    └── recent_form.csv  # Last 5 matches per team
```

---

## 📊 Data Format

**`data/h2h_data.csv`** — 204 matches across UCL, La Liga, Premier League and more

| Column | Type | Description |
|---|---|---|
| `date` | YYYY-MM-DD | Match date |
| `home_team` | string | Home team name |
| `away_team` | string | Away team name |
| `home_goals` | int | Goals scored by home team |
| `away_goals` | int | Goals scored by away team |
| `competition` | string | Tournament or league (e.g. UCL, PL, La Liga) |

Sample rows:
```
date,home_team,away_team,home_goals,away_goals,competition
2024-04-17,Real Madrid,Manchester City,3,3,UCL
2022-05-28,Real Madrid,Liverpool,1,0,UCL Final
2020-08-14,Bayern Munich,Barcelona,8,2,UCL QF
```

---

**`data/recent_form.csv`** — Last 5 matches for each of the 10 teams (50 rows total)

| Column | Type | Description |
|---|---|---|
| `team` | string | Team name |
| `date` | YYYY-MM-DD | Match date |
| `opponent` | string | Opposing team |
| `venue` | H / A | Home or Away |
| `goals_for` | int | Goals scored |
| `goals_against` | int | Goals conceded |
| `result` | W / D / L | Match outcome |

Sample rows:
```
team,date,opponent,venue,goals_for,goals_against,result
Real Madrid,2026-03-22,Celta Vigo,H,3,0,W
Liverpool,2026-03-22,Newcastle,A,2,1,W
Bayern Munich,2026-02-21,Dortmund,A,2,0,W
```

---

## 🚀 Getting Started

**Requirements:** Python 3.7+, no external libraries needed.

```bash
# Clone the repository
git clone https://github.com/your-username/football-match-predictor.git
cd football-match-predictor

# Run the predictor
python main.py
```

Then follow the on-screen prompts to select a home and away team.

---

## 🏟️ Supported Teams

| # | Team | League |
|---|---|---|
| 1 | Manchester City | Premier League |
| 2 | Real Madrid | La Liga |
| 3 | Bayern Munich | Bundesliga |
| 4 | Liverpool | Premier League |
| 5 | Barcelona | La Liga |
| 6 | Paris Saint-Germain | Ligue 1 |
| 7 | Arsenal | Premier League |
| 8 | Sporting CP | Primeira Liga |
| 9 | Juventus | Serie A |
| 10 | Atletico Madrid | La Liga |

---

## 🔧 Extending the Project

**Adding more teams:** Update the `TEAMS` dictionary in `main.py` and add corresponding rows in both CSV files. Team names must match exactly across all files.

**Adjusting prediction weights:** Modify the composite score line in `predictor.py`:

```python
s1 = 0.20 * ht1 + 0.55 * ft1 + 0.25 * gt1
#    ^^^^          ^^^^          ^^^^
#    H2H           Form          xG
```

**Updating form data:** Replace or append rows in `recent_form.csv` with the latest 5 matches per team. Keep dates in `YYYY-MM-DD` format and venue as `H` or `A`.
