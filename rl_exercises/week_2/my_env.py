from __future__ import annotations

from typing import Any, SupportsFloat

import gymnasium as gym
import numpy as np


# ------------- TODO: Implement the following environment -------------
class MyEnv(gym.Env):
    """
    Simple 2-state, 2-action environment with deterministic transitions.

    Actions
    -------
    Discrete(2):
    - 0: move to state 0
    - 1: move to state 1

    Observations
    ------------
    Discrete(2): the current state (0 or 1)

    Reward
    ------
    Equal to the action taken.

    Start/Reset State
    -----------------
    Always starts in state 0.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        transition_probabilities: np.ndarray = np.ones((2, 2)),
        horizon=10,
        rewards: list[float] = [0, 1],
        seed: int | None = None,
    ):
        """Initializes the observation and action space for the environment."""
        self.rng = np.random.default_rng(seed)
        self.P = np.array(transition_probabilities)
        self.rewards = list(rewards)
        self.horizon = int(horizon)
        self.state = 0  # start at pos 0

        # spaces
        n = self.P.shape[0]
        self.observation_space = gym.spaces.Discrete(n)
        self.action_space = gym.spaces.Discrete(n)

        # helpers
        self.states = np.arange(n)
        self.actions = np.arange(n)

        # transition matrix
        self.transition_matrix = self.T = self.get_transition_matrix()
        pass

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        """
        Reset the environment to its initial state.

        Parameters
        ----------
        seed : int, optional
            Seed for environment reset (unused).
        options : dict, optional
            Additional reset options (unused).

        Returns
        -------
        state : int
            Initial state (always 0).
        info : dict
            An empty info dictionary.
        """
        self.transition_count = 0
        self.state = 0
        return self.state, {}

    def step(
        self, action: int
    ) -> tuple[int, SupportsFloat, bool, bool, dict[str, Any]]:
        """
        Take one step in the environment.

        Parameters
        ----------
        action : int
            Action to take (0: go to state 0, 1: go to state 1).

        Returns
        -------
        next_state : int
            The next chosen state.
        reward : float
            The reward at the new state.
        terminated : bool
            Whether the episode ended due to task success.
        truncated : bool
            Whether the episode ended due to reaching the time limit.
        info : dict
            An empty dictionary.
        """
        action = int(action)
        if not self.action_space.contains(action):
            raise RuntimeError(f"{action} is not a valid action (needs to be 0 or 1)")

        self.state = max(
            0,
            min(self.observation_space.n - 1, self.state + (-1 if action == 0 else 1)),
        )  # choose a state between 0 and n-1. n is a parameter of discrete spaces
        reward = float(self.rewards[self.state])
        terminated = False
        truncated = self.transition_count >= self.horizon

        return self.state, reward, terminated, truncated, {}

    def get_reward_per_action(self) -> np.ndarray:
        """
        Return the reward function R[s, a] for each (state, action) pair.

        R[s, a] is the reward for the cell the rover would land in after taking action a in state s.

        Returns
        -------
        R : np.ndarray
            A (num_states, num_actions) array of rewards.
        """
        nS, nA = self.observation_space.n, self.action_space.n
        R = np.zeros((nS, nA), dtype=float)
        for s in range(nS):
            for a in range(nA):
                nxt = max(0, min(nS - 1, s + (-1 if a == 0 else 1)))
                R[s, a] = float(self.rewards[nxt])
        return R

    def get_transition_matrix(
        self,
        S: np.ndarray | None = None,
        A: np.ndarray | None = None,
        P: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Construct a deterministic transition matrix T[s, a, s'].

        Parameters
        ----------
        S : np.ndarray, optionalpip
            Array of states. Uses internal states if None.
        A : np.ndarray, optional
            Array of actions. Uses internal actions if None.
        P : np.ndarray, optional
            Action success probabilities. Uses internal P if None.

        Returns
        -------
        T : np.ndarray
            A (num_states, num_actions, num_states) tensor where
            T[s, a, s'] = probability of transitioning to s' from s via a.
        """
        if S is None or A is None or P is None:
            S, A, P = self.states, self.actions, self.P

        nS, nA = len(S), len(A)
        T = np.zeros((nS, nA, nS), dtype=float)
        for s in S:
            for a in A:
                s_next = max(0, min(nS - 1, s + (-1 if a == 0 else 1)))
                T[s, a, s_next] = float(P[s, a])
        return T

    class PartialObsWrapper(gym.Wrapper):
        """Wrapper that makes the underlying env partially observable by injecting
        observation noise: with probability `noise`, the true state is replaced by
        a random (incorrect) observation.

        Parameters
        ----------
        env : gym.Env
            The fully observable base environment.
        noise : float, default=0.1
            Probability in [0,1] of seeing a random wrong observation instead
            of the true one.
        seed : int | None, default=None
            Optional RNG seed for reproducibility.
        """

        metadata = {"render_modes": ["human"]}
