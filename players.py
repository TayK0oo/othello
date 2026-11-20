# Author: Théo Cornu
import json
import os

from config import DEFAULT_ALGO, DEFAULT_BUDGET_MS, DEFAULT_DEPTH, DEFAULT_STRATEGY
from agent import Agent
from evals import make_evaluator
from human import HumanPlayer

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "players_config.json")


def load_player_config(path=CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def make_ai(engine, strategy=DEFAULT_STRATEGY, algo=DEFAULT_ALGO, depth=DEFAULT_DEPTH, budget_ms=DEFAULT_BUDGET_MS, name=None):
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
            strategy=profile.get("strategy", DEFAULT_STRATEGY),
            algo=profile.get("algo", DEFAULT_ALGO),
            depth=int(profile.get("depth", DEFAULT_DEPTH)),
            budget_ms=int(profile.get("budget_ms", DEFAULT_BUDGET_MS)),
            name=profile.get("name"),
        )
    raise ValueError(f"type de joueur inconnu : {profile_type}")


def make_profile_player(engine, profile_name, config=None):
    config = config or load_player_config()
    profiles = config["profiles"]
    if profile_name not in profiles:
        raise ValueError(f"profil inconnu : {profile_name}")
    return make_player(engine, profiles[profile_name])