# Author: Théo Cornu
import json
import os

from agent import Agent
from evals import make_evaluator
from human import HumanPlayer

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "players_config.json")


def load_player_config(path=CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def make_ai(engine, strategy="mixed", algo="alphabeta", depth=6, budget_ms=1000, name=None):
    evaluator = make_evaluator(strategy, engine)
    return Agent(
        engine,
        evaluator,
        algo=algo,
        max_depth=depth,
        time_budget_ms=budget_ms,
        name=name or f"IA {strategy}",
    )


def make_human(engine, name="Humain"):
    return HumanPlayer(engine, name)


def make_player(engine, profile):
    profile_type = profile.get("type", "human").lower()
    if profile_type == "human":
        return make_human(engine, profile.get("name", "Humain"))
    if profile_type == "ai":
        return make_ai(
            engine,
            strategy=profile.get("strategy", "mixed"),
            algo=profile.get("algo", "alphabeta"),
            depth=int(profile.get("depth", 6)),
            budget_ms=int(profile.get("budget_ms", 1000)),
            name=profile.get("name"),
        )
    raise ValueError(f"type de joueur inconnu : {profile_type}")


def make_profile_player(engine, profile_name, config=None):
    config = config or load_player_config()
    profiles = config["profiles"]
    if profile_name not in profiles:
        raise ValueError(f"profil inconnu : {profile_name}")
    return make_player(engine, profiles[profile_name])