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
        將任意兩張手牌正規化為 169 手代表牌符號，並回傳對應的花色映射表。
        """
        ids = [self.symbol_to_id[s] for s in hand]
        cards = [(i % 13, i // 13) for i in ids]
        
        # 確保 r1 總是較小的 rank
        cards.sort(key=lambda x: x[0])
        r1, s1 = cards[0]
        r2, s2 = cards[1]

        suit_mapping = {}
        avail_target_suits = [0, 1, 2, 3]
        avail_src_suits = [0, 1, 2, 3]

        if r1 == r2:
            sym1 = self.cards_config[r1]["symbol"]
            sym2 = self.cards_config[r1 + 13]["symbol"]
            norm_hand_syms = sorted([sym1, sym2])
            
            suit_mapping[s1] = 0
            suit_mapping[s2] = 1
            avail_target_suits.remove(0)
            avail_target_suits.remove(1)
            avail_src_suits.remove(s1)
            avail_src_suits.remove(s2)
        elif s1 == s2:
            sym1 = self.cards_config[r1]["symbol"]
            sym2 = self.cards_config[r2]["symbol"]
            norm_hand_syms = sorted([sym1, sym2])
            
            suit_mapping[s1] = 0
            avail_target_suits.remove(0)
            avail_src_suits.remove(s1)
        else:
            sym1 = self.cards_config[r1]["symbol"]
            sym2 = self.cards_config[r2 + 13]["symbol"]
            norm_hand_syms = sorted([sym1, sym2])
            
            suit_mapping[s1] = 0
            suit_mapping[s2] = 1
            avail_target_suits.remove(0)
            avail_target_suits.remove(1)
            avail_src_suits.remove(s1)
            avail_src_suits.remove(s2)
            
        for src_s, tgt_s in zip(avail_src_suits, avail_target_suits):
            suit_mapping[src_s] = tgt_s

        return norm_hand_syms, suit_mapping

    def _normalize_board(self, board, suit_mapping):
        """
        根據手牌正規化時產生的花色映射表，將公共牌也進行等價映射。
        """
        if not board:
            return []
        norm_board = []
        for b_sym in board:
            b_id = self.symbol_to_id[b_sym]
            b_r = b_id % 13
            b_s = b_id // 13
            
            mapped_s = suit_mapping[b_s]
            mapped_idx = mapped_s * 13 + b_r
            norm_board.append(self.cards_config[mapped_idx]["symbol"])
        return sorted(norm_board)

    def query(self, hand, board=None):
        """
        hand: ['AH', 'KD']
        board: ['2S', '3H', '4D'] (Flop) 或 ['2S', '3H', '4D', '5C'] (Turn)
        """
        norm_hand_syms, suit_mapping = self._normalize_hand(hand)
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
        norm_board = self._normalize_board(board, suit_mapping)
        board_key = ",".join(norm_board)

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Stage"] == stage and row["Board"] == board_key:
                    return {
                        "Hand": hand,
                        "Board": board,
                        "NormalizedTo": norm_hand_syms,
                        "MappedBoard": norm_board,
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
