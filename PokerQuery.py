import csv
import os
import yaml


class PokerQuery:
    def __init__(self, results_dir="./results", config_path="cards.yaml"):
        self.results_dir = results_dir
        with open(config_path, "r", encoding="utf-8") as f:
            self.cards_config = yaml.safe_load(f)

        # 建立符號到 ID 的反向索引
        self.symbol_to_id = {v["symbol"]: int(k) for k, v in self.cards_config.items()}

    def _normalize_hand(self, hand):
        """
        將任意兩張手牌正規化為 169 手代表牌符號
        邏輯：
        1. 獲取兩張牌的 rank_idx (0-12) 和 suit_idx (0-3)
        2. 判斷是 Pair, Suited, 還是 Offsuit
        3. 根據 PokerFullSpectrum.py 的生成邏輯映射回代表符號
        """
        ids = [self.symbol_to_id[s] for s in hand]
        # rank_idx = idx % 13; suit_idx = idx // 13
        r1, s1 = ids[0] % 13, ids[0] // 13
        r2, s2 = ids[1] % 13, ids[1] // 13

        # 排序 rank，讓 rmin 永遠是點數較小的索引 (A=0, 2=1...)
        # 注意：在我的 cards.yaml 中，0 是 A，1 是 2... 12 是 K
        ranks = sorted([r1, r2])
        r_min, r_max = ranks[0], ranks[1]

        if r1 == r2:
            # Pair -> 代表牌是 [rank]S, [rank]H (idx: r, r+13)
            # 例如 AA -> AS, AH
            sym1 = self.cards_config[r_min]["symbol"]
            sym2 = self.cards_config[r_min + 13]["symbol"]
        elif s1 == s2:
            # Suited -> 代表牌是 [r_min]S, [r_max]S (idx: r_min, r_max)
            # 例如 AKs -> AS, KS
            sym1 = self.cards_config[r_min]["symbol"]
            sym2 = self.cards_config[r_max]["symbol"]
        else:
            # Offsuit -> 代表牌是 [r_min]S, [r_max]H (idx: r_min, r_max+13)
            # 例如 AKo -> AS, KH
            sym1 = self.cards_config[r_min]["symbol"]
            sym2 = self.cards_config[r_max + 13]["symbol"]

        return sorted([sym1, sym2])

    def query(self, hand, board=None):
        """
        hand: ['AH', 'KD']
        board: ['2S', '3H', '4D'] (Flop) 或 ['2S', '3H', '4D', '5C'] (Turn)
        """
        norm_hand_syms = self._normalize_hand(hand)
        hand_name = "_".join(norm_hand_syms)
        file_path = os.path.join(self.results_dir, f"{hand_name}.csv")

        if not os.path.exists(file_path):
            return f"找不到數據檔案: {file_path}。請確保已跑完該手牌的全譜計算。"

        if board is None or len(board) == 0:
            # 查詢 Preflop
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["Stage"] == "Preflop":
                        return {
                            "Hand": hand,
                            "NormalizedTo": norm_hand_syms,
                            "Stage": "Preflop",
                            "Equity": float(row["Equity"]),
                            "TieProb": float(row["TieProb"]),
                        }

        # 查詢 Flop 或 Turn
        stage = "Flop" if len(board) == 3 else "Turn"
        # 注意：CSV 中的 Board 是排序後的符號，逗號分隔
        board_key = ",".join(sorted(board))

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Stage"] == stage and row["Board"] == board_key:
                    return {
                        "Hand": hand,
                        "Board": board,
                        "NormalizedTo": norm_hand_syms,
                        "Stage": stage,
                        "Equity": float(row["Equity"]),
                        "TieProb": float(row["TieProb"]),
                    }

        return f"在 {hand_name} 的數據中找不到對應的公共牌組合: {board_key}"


if __name__ == "__main__":
    import sys

    query_tool = PokerQuery()

    # 範例用法
    # python PokerQuery.py AS KH 2D 3S 4H
    if len(sys.argv) < 3:
        print("用法: python PokerQuery.py [Card1] [Card2] [Board...]")
        print("例如: python PokerQuery.py AH KD")
        print("例如: python PokerQuery.py AH KD 2S 3H 4D")
    else:
        my_hand = sys.argv[1:3]
        my_board = sys.argv[3:]
        result = query_tool.query(my_hand, my_board)
        print(result)
