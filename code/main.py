import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from predictor import FootballPredictor

TEAMS = {
    1:  "Manchester City",
    2:  "Real Madrid",
    3:  "Bayern Munich",
    4:  "Liverpool",
    5:  "Barcelona",
    6:  "Paris Saint-Germain",
    7:  "Arsenal",
    8:  "Sporting CP",
    9:  "Juventus",
    10: "Atletico Madrid",
}


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    print("=" * 56)
    print("           FOOTBALL MATCH PREDICTOR              ")
    print("=" * 56)


def display_teams():
    print("\n  TOP 10 FOOTBALL TEAMS")
    print("  " + "-" * 40)
    for num, team in TEAMS.items():
        print(f"  {num:2}.  {team}")
    print("  " + "-" * 40)


def select_team(prompt, exclude=None):
    while True:
        try:
            choice = int(input(f"\n  {prompt}"))
            if choice not in TEAMS:
                print("  [!] Enter a number between 1 and 10.")
                continue
            if exclude and TEAMS[choice] == exclude:
                print("  [!] Choose a different team from the first selection.")
                continue
            return TEAMS[choice]
        except ValueError:
            print("  [!] Please enter a valid number.")


def main():
    clear()
    print_banner()

    while True:
        display_teams()

        print("\n  Select two teams to predict the match outcome:")
        team1 = select_team("Select Home Team  (1-10): ")
        team2 = select_team("Select Away Team  (1-10): ", exclude=team1)

        print(f"\n  {'=' * 56}")
        print(f"  Matchup  :  {team1}  (H)  vs  {team2}  (A)")
        print(f"  {'=' * 56}")

        predictor = FootballPredictor()
        predictor.predict(team1, team2)

        again = input("\n  Predict another match? (y/n): ").strip().lower()
        if again != 'y':
            break
        clear()
        print_banner()

    print("\n  Thanks for using Football Match Predictor!\n")


if __name__ == '__main__':
    main()
