import sys

from evals.dashboard.page import DashboardPage

if __name__ == "__main__":
    sys.stdout.write(f"{DashboardPage.write()}\n")
