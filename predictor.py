import csv
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


def _load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


class FootballPredictor:

    def __init__(self):
        self.h2h_rows  = _load_csv('h2h_data.csv')
        self.form_rows = _load_csv('recent_form.csv')

    # ── Data Loaders ─────────────────────────────────────────────────────────

    def get_h2h(self, team1, team2):
        matches = [
            r for r in self.h2h_rows
            if (r['home_team'] == team1 and r['away_team'] == team2) or
               (r['home_team'] == team2 and r['away_team'] == team1)
        ]
        matches.sort(key=lambda r: r['date'])
        if not matches:
            return None

        t1w = t2w = draws = t1g = t2g = 0
        for r in matches:
            if r['home_team'] == team1:
                g1, g2 = int(r['home_goals']), int(r['away_goals'])
            else:
                g1, g2 = int(r['away_goals']), int(r['home_goals'])
            t1g += g1; t2g += g2
            if   g1 > g2: t1w += 1
            elif g1 < g2: t2w += 1
            else:          draws += 1

        n = len(matches)

        # Recent 4 matches — weighted more heavily in the algorithm
        recent = matches[-4:]
        rn = len(recent)
        rt1w = rt2w = rdraws = 0
        for r in recent:
            if r['home_team'] == team1:
                g1, g2 = int(r['home_goals']), int(r['away_goals'])
            else:
                g1, g2 = int(r['away_goals']), int(r['home_goals'])
            if   g1 > g2: rt1w += 1
            elif g1 < g2: rt2w += 1
            else:          rdraws += 1

        return dict(
            matches=matches, total=n,
            t1w=t1w, t2w=t2w, draws=draws,
            t1wr=t1w/n, t2wr=t2w/n, dr=draws/n,
            t1ag=t1g/n, t2ag=t2g/n,
            rt1wr=rt1w/rn, rt2wr=rt2w/rn, rdr=rdraws/rn,
        )

    def get_form(self, team):
        rows = [r for r in self.form_rows if r['team'] == team]
        if not rows:
            return None

        pts_map = {'W': 3, 'D': 1, 'L': 0}
        pts    = sum(pts_map[r['result']] for r in rows)
        gf     = sum(int(r['goals_for'])     for r in rows) / len(rows)
        ga     = sum(int(r['goals_against']) for r in rows) / len(rows)
        wins   = sum(1 for r in rows if r['result'] == 'W')
        draws  = sum(1 for r in rows if r['result'] == 'D')
        losses = sum(1 for r in rows if r['result'] == 'L')

        # Separate home / away ratings for more accurate venue-aware predictions
        home_rows = [r for r in rows if r['venue'] == 'H']
        away_rows = [r for r in rows if r['venue'] == 'A']

        def _sub_rating(subset):
            if not subset:
                return None
            p = sum(pts_map[r['result']] for r in subset)
            return p / (len(subset) * 3)

        return dict(
            rows=rows,
            wins=wins, draws=draws, losses=losses,
            pts=pts,
            rating=pts / (len(rows) * 3),
            avg_for=gf, avg_against=ga,
            home_rating=_sub_rating(home_rows),
            away_rating=_sub_rating(away_rows),
        )

    # ── Prediction Engine ─────────────────────────────────────────────────────

    def _calculate(self, h2h, f1, f2):
        # Home advantage: top-flight home teams score ~8% more and concede ~8% less
        HOME_EDGE = 0.08

        # ─── H2H component (20% weight) ──────────────────────────────────────
        if h2h:
            # Blend all-time (40%) with most-recent 4 (60%) for recency bias
            ht1 = 0.40 * h2h['t1wr'] + 0.60 * h2h['rt1wr']
            ht2 = 0.40 * h2h['t2wr'] + 0.60 * h2h['rt2wr']
            hdr = 0.40 * h2h['dr']   + 0.60 * h2h['rdr']
            hn  = ht1 + ht2 + hdr
            if hn > 0:
                ht1 /= hn; ht2 /= hn; hdr /= hn
        else:
            ht1, ht2, hdr = 0.40, 0.34, 0.26   # default: slight home edge

        # ─── Form component (55% weight) ─────────────────────────────────────
        # Use venue-specific sub-ratings when available:
        #   team1 is HOME  → prefer their home_rating
        #   team2 is AWAY  → prefer their away_rating
        if f1:
            r1 = (f1['home_rating'] if f1['home_rating'] is not None else f1['rating'])
            r1 *= (1 + HOME_EDGE)   # home-field boost
        else:
            r1 = 0.50

        if f2:
            r2 = f2['away_rating'] if f2['away_rating'] is not None else f2['rating']
        else:
            r2 = 0.50

        ft = r1 + r2 or 1.0
        ft1, ft2 = r1 / ft, r2 / ft

        # ─── Expected Goals component (25% weight) ────────────────────────────
        if f1 and f2:
            # Apply home edge to team1's attack and team2's attack
            xg1 = (f1['avg_for'] * (1 + HOME_EDGE * 0.5) + f2['avg_against']) / 2
            xg2 = (f2['avg_for'] + f1['avg_against'] * (1 - HOME_EDGE * 0.5)) / 2
        elif h2h:
            xg1, xg2 = h2h['t1ag'], h2h['t2ag']
        else:
            xg1, xg2 = 1.6, 1.1   # slight home advantage default

        # Blend with H2H goal averages when both sources exist
        if h2h and f1 and f2:
            xg1 = 0.65 * xg1 + 0.35 * h2h['t1ag']
            xg2 = 0.65 * xg2 + 0.35 * h2h['t2ag']

        # Cap to realistic range (top football rarely exceeds 3.5 xG)
        xg1 = max(0.4, min(3.5, xg1))
        xg2 = max(0.4, min(3.5, xg2))

        gt = xg1 + xg2 or 1.0
        gt1, gt2 = xg1 / gt, xg2 / gt

        # ─── Composite strength ───────────────────────────────────────────────
        s1 = 0.20 * ht1 + 0.55 * ft1 + 0.25 * gt1
        s2 = 0.20 * ht2 + 0.55 * ft2 + 0.25 * gt2

        # ─── Draw probability ─────────────────────────────────────────────────
        # Base = blend of H2H draw rate + typical top-football average (~27%)
        base_dr = 0.50 * hdr + 0.50 * 0.27
        # Closeness boost: evenly-matched teams produce more draws
        norm_diff = abs(s1 - s2) / (s1 + s2 or 1.0)
        closeness_boost = 0.12 * max(0.0, 1.0 - norm_diff * 4)
        dp = max(0.12, min(0.35, base_dr + closeness_boost))

        # ─── Win probabilities ────────────────────────────────────────────────
        st = s1 + s2 or 1.0
        w1 = (1 - dp) * (s1 / st)
        w2 = (1 - dp) * (s2 / st)
        tot = w1 + dp + w2
        w1 /= tot; dp /= tot; w2 /= tot

        # ─── Predicted scoreline ─────────────────────────────────────────────
        sc1 = max(0, round(xg1))
        sc2 = max(0, round(xg2))

        # Only override score when there's a clear favourite (>12% probability gap)
        if   w1 > w2 + 0.12 and sc1 <= sc2: sc1 = sc2 + 1
        elif w2 > w1 + 0.12 and sc2 <= sc1: sc2 = sc1 + 1
        elif abs(w1 - w2) <= 0.08:           sc1 = sc2 = max(sc1, sc2)

        return w1, dp, w2, sc1, sc2, xg1, xg2

    # ── Display ───────────────────────────────────────────────────────────────

    @staticmethod
    def _bar(p, width=26):
        filled = round(p * width)
        return '█' * filled + '░' * (width - filled)

    @staticmethod
    def _badge(result):
        return {'W': '[W]', 'D': '[D]', 'L': '[L]'}[result]

    def predict(self, team1, team2):
        h2h = self.get_h2h(team1, team2)
        f1  = self.get_form(team1)
        f2  = self.get_form(team2)

        SEP = "  " + "─" * 54

        # ── Head to Head ──────────────────────────────────────────────────────
        print(f"\n  HEAD TO HEAD HISTORY")
        print(SEP)
        if h2h:
            print(f"  Total Meetings   :  {h2h['total']}")
            print(f"  {team1:<26}  Wins :  {h2h['t1w']}")
            print(f"  {'Draws':<26}       :  {h2h['draws']}")
            print(f"  {team2:<26}  Wins :  {h2h['t2w']}")
            last_n = min(6, h2h['total'])
            print(f"\n  Last {last_n} Results :")
            for r in h2h['matches'][-last_n:]:
                hg = int(r['home_goals'])
                ag = int(r['away_goals'])
                ht = r['home_team'][:22]
                at = r['away_team'][:22]
                print(f"    {r['date']}   {ht:<22}  {hg} - {ag}  {at:<22}  [{r['competition']}]")
        else:
            print("  No H2H records found. Prediction based on recent form only.")

        # ── Recent Form ───────────────────────────────────────────────────────
        print(f"\n  RECENT FORM  (Last 5 Games)")
        print(SEP)
        for team, form in [(team1, f1), (team2, f2)]:
            if form:
                badges = "  ".join(self._badge(r['result']) for r in form['rows'])
                print(f"\n  {team}")
                print(f"    Form      :  {badges}")
                print(f"    Record    :  {form['wins']}W  {form['draws']}D  {form['losses']}L   ({form['pts']}/15 pts)")
                print(f"    Goals     :  Scored {form['avg_for']:.1f}  |  Conceded {form['avg_against']:.1f} per game")
            else:
                print(f"\n  {team}  :  No recent form data.")

        # ── Prediction Result ─────────────────────────────────────────────────
        w1, dp, w2, sc1, sc2, xg1, xg2 = self._calculate(h2h, f1, f2)

        if   w1 > w2 and w1 > dp: outcome = f"{team1}  WIN"
        elif w2 > w1 and w2 > dp: outcome = f"{team2}  WIN"
        else:                     outcome = "DRAW"

        print(f"\n  {'=' * 56}")
        print(f"  PREDICTION RESULT")
        print(f"  {'=' * 56}")
        print(f"\n  Predicted Score   :  {team1}  {sc1}  -  {sc2}  {team2}")
        print(f"  Expected xG       :  {xg1:.2f}  vs  {xg2:.2f}")
        print(f"  Predicted Outcome :  {outcome}")
        print(f"\n  Win Probabilities :")
        print(f"    {team1:<28}  {w1*100:5.1f}%   {self._bar(w1)}")
        print(f"    {'Draw':<28}  {dp*100:5.1f}%   {self._bar(dp)}")
        print(f"    {team2:<28}  {w2*100:5.1f}%   {self._bar(w2)}")
        print(f"\n  {'=' * 56}")