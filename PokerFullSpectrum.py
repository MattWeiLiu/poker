import csv
import itertools
import multiprocessing
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import os
import yaml


def load_yaml(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 全域變數用於 Worker 進程
_cards_config = None
_symbols = None


def init_worker():
    global _cards_config, _symbols
    _cards_config = load_yaml("cards.yaml")
    _symbols = [c["symbol"] for c in _cards_config.values()]


class PokerOptimizationEngine:
    def __init__(self):
        self.cards_config = load_yaml("cards.yaml")
        # 修正後的 169 種代表性起手牌
        self.representative_hands = self._generate_169_hands()
        self.all_cards = list(range(52))

        if not os.path.exists("./results"):
            os.makedirs("./results")

    def _generate_169_hands(self):
        """
        修正後的 169 種同構起手牌
        映射邏輯基於 cards.yaml: Index = (suit_idx * 13) + rank_idx
        rank_idx: 0=A, 1=2, 2=3 ... 12=K
        suit_idx: 0=S, 1=H, 2=D, 3=C
        """
        hands = []
        # 定義點數順序 (A, 2, 3... K)
        ranks = list(range(13))

        for i in range(13):
            r1 = ranks[i]
            for j in range(i, 13):
                r2 = ranks[j]
                if r1 == r2:
                    # 對子 (Pair): 使用 Spades + Hearts
                    hands.append({"cards": (r1, r1 + 13), "weight": 6, "type": "pair"})
                else:
                    # 同花 (Suited): 使用 Spades + Spades
                    # 放入 (r1, r2) 權重 4
                    hands.append({"cards": (r1, r2), "weight": 4, "type": "suited"})
                    # 雜色 (Offsuit): 使用 Spades + Hearts
                    # 放入 (r1, r2+13) 權重 12
                    hands.append(
                        {"cards": (r1, r2 + 13), "weight": 12, "type": "offsuit"}
                    )
        return hands

    @staticmethod
    def calculate_river_batch(pocket_indices, board_batch):
        from poker_eval_ctypes import PokerEvaluatorCTypes

        evaluator = PokerEvaluatorCTypes()
        batch_results = []

        pocket_mask = 0
        for idx in pocket_indices:
            pocket_mask |= 1 << idx

        remaining_after_pocket = [i for i in range(52) if not (pocket_mask & (1 << i))]

        for board_indices in board_batch:
            board_set = set(board_indices)
            remaining_ids = [i for i in remaining_after_pocket if i not in board_set]

            win, lose, draw = evaluator.batch_evaluate_board_ints(
                pocket_indices, board_indices, remaining_ids
            )

            total = win + lose + draw
            equity = (win + 0.5 * draw) / total
            tie_prob = draw / total
            batch_results.append((board_indices, equity, tie_prob))

        return batch_results

    def run_isomorphism_eval(self, hand_idx):
        hand = self.representative_hands[hand_idx]
        pocket = hand["cards"]
        pocket_symbols = sorted([self.cards_config[i]["symbol"] for i in pocket])

        print(
            f"[{hand_idx + 1}/169] 開始評估: {pocket_symbols} ({hand['type']}, 權重: {hand['weight']})"
        )

        remaining = [c for c in self.all_cards if c not in pocket]
        all_river_boards = list(itertools.combinations(remaining, 5))
        total_boards = len(all_river_boards)

        batch_size = 5000  # 增加批次大小減少多進程切換開銷
        batches = [
            all_river_boards[i : i + batch_size]
            for i in range(0, total_boards, batch_size)
        ]

        river_equities = {}

        with ProcessPoolExecutor(
            max_workers=multiprocessing.cpu_count(), initializer=init_worker
        ) as executor:
            futures = [
                executor.submit(self.calculate_river_batch, pocket, b) for b in batches
            ]
            for future in futures:
                results = future.result()
                for board_indices, eq, tp in results:
                    river_equities[board_indices] = (eq, tp)

        # --- 聚合 ---
        turn_sum_eq = defaultdict(float)
        turn_sum_tp = defaultdict(float)
        turn_count = defaultdict(int)
        for board, (eq, tp) in river_equities.items():
            for sub in itertools.combinations(board, 4):
                key = tuple(sorted(sub))
                turn_sum_eq[key] += eq
                turn_sum_tp[key] += tp
                turn_count[key] += 1

        turn_equity = {k: turn_sum_eq[k] / turn_count[k] for k in turn_count}
        turn_tie_prob = {k: turn_sum_tp[k] / turn_count[k] for k in turn_count}
        del river_equities

        flop_sum_eq = defaultdict(float)
        flop_sum_tp = defaultdict(float)
        flop_count = defaultdict(int)
        for board, eq in turn_equity.items():
            tp = turn_tie_prob[board]
            for sub in itertools.combinations(board, 3):
                key = tuple(sorted(sub))
                flop_sum_eq[key] += eq
                flop_sum_tp[key] += tp
                flop_count[key] += 1

        flop_equity = {k: flop_sum_eq[k] / flop_count[k] for k in flop_count}
        flop_tie_prob = {k: flop_sum_tp[k] / flop_count[k] for k in flop_count}

        pre_eq = sum(flop_equity.values()) / len(flop_equity)
        pre_tp = sum(flop_tie_prob.values()) / len(flop_tie_prob)

        self.save_to_csv(
            pocket_symbols,
            pre_eq,
            pre_tp,
            flop_equity,
            flop_tie_prob,
            turn_equity,
            turn_tie_prob,
        )

    def save_to_csv(
        self, pocket_symbols, pre_eq, pre_tp, flop_eq, flop_tp, turn_eq, turn_tp
    ):
        pocket_name = "_".join(pocket_symbols)
        filename = f"./results/{pocket_name}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Stage", "Board", "Equity", "TieProb"])
            writer.writerow(["Preflop", "", pre_eq, pre_tp])
            for b_indices, eq in flop_eq.items():
                tp = flop_tp[b_indices]
                symbols = ",".join(
                    sorted([self.cards_config[i]["symbol"] for i in b_indices])
                )
                writer.writerow(["Flop", symbols, eq, tp])
            for b_indices, eq in turn_eq.items():
                tp = turn_tp[b_indices]
                symbols = ",".join(
                    sorted([self.cards_config[i]["symbol"] for i in b_indices])
                )
                writer.writerow(["Turn", symbols, eq, tp])


if __name__ == "__main__":
    engine = PokerOptimizationEngine()
    for i in range(len(engine.representative_hands)):
        engine.run_isomorphism_eval(i)
