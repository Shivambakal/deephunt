"""Demo: the engine thinking like a human on three live cases.

Usage: python -m brain order | gitlab | pinterest
"""
import sys
from .model import WorldModel
from .engine import Engine
from . import hypotheses as H


def scenario_order():
    """The user's own H17 example: GET validates ownership, PATCH unknown."""
    m = WorldModel("shop-api", objects=["Order", "Account"],
                   trust_boundaries=["browser->API", "API->database"],
                   state_machines={"Order": ["created", "paid", "shipped"]})
    m.assume("A1", "only the order owner can mutate an order",
             "GET /api/order/:id ownership check",
             "PATCH/PUT/DELETE as non-owner succeeds")
    e = Engine(m)
    e.run("GET /api/order checks ownership; PATCH behavior unknown")
    # simulate the test coming back rejected -> learning loop fires
    ranked = H.rank(H.generate(m))
    e.learn(ranked[0].id, ranked, "rejected",
            "PATCH returned 403 for non-owner",
            "ownership validated on PATCH too; enforcement lives in a shared before_action")
    e.on_contradiction("PATCH should skip ownership like GET enforces it",
                       "PATCH returned 403")


def scenario_gitlab():
    """Code-confirmed finding: job-token allowlist skipped on package routes."""
    m = WorldModel("gitlab", objects=["Package", "Project", "JobToken"],
                   trust_boundaries=["runner->API", "API->database"],
                   state_machines={"JobToken": ["issued", "scoped", "used"]})
    m.assume("A1", "a job token can only reach its allowlisted projects",
             "authorize_job_token_policies! in API helpers",
             "PyPI/Composer/npm routes serve packages outside the allowlist")
    m.assume("A2", "skip_job_token_policies is only an auth convenience flag",
             "route-level flag on package endpoints",
             "the flag silently drops scope enforcement too")
    context = {
        "known_facts": [
            # devil's evidence: these kill any hypothesis claiming the GraphQL path is affected
            "graphql rejects job tokens outright",
        ],
        "experiment": {
            "method": "GET",
            "target_url": "https://gitlab.com/api/v4/projects/<PROJECT_B_ID>/packages/pypi/simple/<pkg>/",
            "headers": {"JOB-TOKEN": "<ci_job_token_from_project_A_pipeline>"},
            "control": "same job token downloads a package from project A (the allowlisted project) -> expect 200",
            "variant": "same job token requests project B's PyPI simple index (NOT allowlisted) -> one variable changed: target project",
            "expect_if_true": "project B serves the package index -> allowlist not enforced on lib/api/pypi_packages.rb routes -> finding CONFIRMED live",
            "expect_if_false": "project B returns 404/403 identical to a tokenless request -> enforcement holds at another layer -> hypothesis dead, pivot to container registry differential",
        },
    }
    e = Engine(m)
    e.run("code: lib/api/pypi_packages.rb etc. accept job tokens without allowlist check; "
          "container registry routes carry job_token_scope: :project",
          context=context)


def scenario_pinterest():
    """Live probe: scheduled pin to a secret board deleted before publish."""
    m = WorldModel("pinterest", objects=["Pin", "Board", "Schedule"],
                   trust_boundaries=["browser->API", "API->scheduler", "scheduler->CDN cache"],
                   state_machines={"Board": ["secret", "public", "deleted"],
                                   "Pin": ["scheduled", "published"]})
    m.assume("A1", "deleting a board cancels its scheduled pins",
             "board delete handler",
             "scheduled pin still publishes to a resurrected/public surface")
    m.assume("A2", "re-secreting a board removes its public cache",
             "board privacy update",
             "unauthenticated cache still serves the pins")
    context = {
        "experiment": {
            "method": "GET",
            "target_url": "https://www.pinterest.com/<username>/<deleted-board-slug>/",
            "control": "while board is secret: unauthenticated GET -> expect login-wall/404 (baseline)",
            "variant": "schedule pin -> delete board before publish -> wait past publish time -> unauthenticated GET the pin URL and board slug (one variable changed: board deleted pre-publish)",
            "expect_if_true": "pin is reachable or board resurrects publicly -> stale-state desync CONFIRMED",
            "expect_if_false": "pin never publishes, slug stays dead -> scheduler honors delete -> hypothesis dead, pivot to secret->public->secret cache window",
        },
    }
    e = Engine(m)
    e.run("secret board scheduled pin; board deleted before publish time", context=context)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "order"
    {"order": scenario_order, "gitlab": scenario_gitlab,
     "pinterest": scenario_pinterest}[which]()
