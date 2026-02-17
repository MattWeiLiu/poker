"""
ctypes 直接呼叫 C++ 共享函式庫 (整合 phevaluator Lookup Table)
完全繞過 stdin/stdout Pipe 且改用整數傳值，效能極大化。
"""

import ctypes
import os


class PokerEvaluatorCTypes:
    def __init__(self, lib_path=None):
        if lib_path is None:
            # 自動判斷系統：Linux 使用 .so, Mac 使用 .dylib
            import platform

            system = platform.system()
            ext = "so" if system == "Linux" else "dylib"

            lib_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "evaluator",
                f"libpoker_eval.{ext}",
            )

        if not os.path.exists(lib_path):
            raise FileNotFoundError(
                f"找不到評估器函式庫: {lib_path}\n請依據實作手冊在遠端環境重新編譯。"
            )

        self._lib = ctypes.CDLL(lib_path)

        # 設定函數簽名 - 整數接口
        self._lib.evaluate_7_ids.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        ]
        self._lib.evaluate_7_ids.restype = ctypes.c_int

        self._lib.batch_evaluate_board_ints.argtypes = [
            ctypes.POINTER(ctypes.c_int),  # pocket (2)
            ctypes.POINTER(ctypes.c_int),  # board (5)
            ctypes.POINTER(ctypes.c_int),  # remaining (n)
            ctypes.c_int,  # n_remaining
            ctypes.POINTER(ctypes.c_int),  # out_win
            ctypes.POINTER(ctypes.c_int),  # out_lose
            ctypes.POINTER(ctypes.c_int),  # out_draw
        ]
        self._lib.batch_evaluate_board_ints.restype = None

        self._lib.judge_hands_ids.argtypes = [
            ctypes.POINTER(ctypes.c_int),  # a (2)
            ctypes.POINTER(ctypes.c_int),  # b (2)
            ctypes.POINTER(ctypes.c_int),  # board (5)
        ]
        self._lib.judge_hands_ids.restype = ctypes.c_int

    def evaluate_7_ids(self, ids):
        """
        傳入 7 個 ID (0-51)，回傳 rank (1=最強)
        """
        return self._lib.evaluate_7_ids(*ids)

    def batch_evaluate_board_ints(self, pocket_ids, board_ids, remaining_ids):
        """
        批次評估 (整數模式)：在 C++ 端完成遍歷
        回傳: (win, lose, draw)
        """
        # 轉換為 ctypes 陣列
        p_arr = (ctypes.c_int * len(pocket_ids))(*pocket_ids)
        b_arr = (ctypes.c_int * len(board_ids))(*board_ids)
        r_arr = (ctypes.c_int * len(remaining_ids))(*remaining_ids)

        win = ctypes.c_int(0)
        lose = ctypes.c_int(0)
        draw = ctypes.c_int(0)

        self._lib.batch_evaluate_board_ints(
            p_arr,
            b_arr,
            r_arr,
            len(remaining_ids),
            ctypes.byref(win),
            ctypes.byref(lose),
            ctypes.byref(draw),
        )
        return win.value, lose.value, draw.value

    def judge_ints(self, a_ids, b_ids, board_ids):
        """
        比較兩手牌 (整數模式)
        回傳與 PokerEvaluatorBridge 相同格式
        """
        a_arr = (ctypes.c_int * len(a_ids))(*a_ids)
        b_arr = (ctypes.c_int * len(b_ids))(*b_ids)
        board_arr = (ctypes.c_int * len(board_ids))(*board_ids)

        result = self._lib.judge_hands_ids(a_arr, b_arr, board_arr)
        if result == 1:
            winner = "A"
        elif result == -1:
            winner = "B"
        else:
            winner = "TIE"
        return {"winner": winner}

    def close(self):
        pass
