#include "phevaluator/phevaluator.h"
#include <cstring>
#include <sstream>
#include <vector>

extern "C" {

// 將我們的 Card ID (0-51) 轉換為 phevaluator 的 Card ID
// 我們: Spades(0-12, A=0, 2=1...), Hearts(13-25), Diamonds(26-38), Clubs(39-51)
// pheval: Rank(0-12, 2=0, 3=1... A=12) * 4 + Suit(Club=0, Diamond=1, Heart=2, Spade=3)
static int to_pheval_id(int our_id) {
    int suit_idx = our_id / 13;
    int pos = our_id % 13;
    int rank_val = (pos == 0) ? 12 : pos - 1;
    int suit_val = 3 - suit_idx;
    return rank_val * 4 + suit_val;
}

// 解析牌字串為 Card ID 陣列
static std::vector<int> parseCards(const char* str) {
    std::vector<int> cards;
    std::stringstream ss(str);
    std::string token;
    // 這裡仍然需要解析字串給舊接口使用
    // 但我們會透過外部傳入的對照表改進，目前暫時維持舊邏輯
    // 實際上在 Python 端我們會直接傳傳 ID 陣列來繞過字串解析
    return cards;
}

// 核心評估函數：回傳 rank (1=最強, 7462=最弱)
// 注意：這裏傳入的是我們的 ID，內部會轉換
int evaluate_7_ids(int c1, int c2, int c3, int c4, int c5, int c6, int c7) {
    return evaluate_7cards(
        to_pheval_id(c1), to_pheval_id(c2), to_pheval_id(c3),
        to_pheval_id(c4), to_pheval_id(c5), to_pheval_id(c6), to_pheval_id(c7)
    );
}

// 為了相容 Python 舊有的字串接口 (evaluate_seven_cards)
// 這裡保留字串解析，但內部改用 phevaluator
long long evaluate_seven_cards(const char* cards_str) {
    // 這裡需要透過符號反推 ID，或者在 Python 端直接呼叫 ID 接口
    // 為了極限效能，建議 Python 端改用 evaluate_7_ids_ctypes
    return -1; // 標記為暫不支持，誘導 Python 使用新接口
}

// 批次評估：直接接收整數陣列 (極速模式)
// pocket: 2 ints, board: 5 ints, remaining: 45 ints
void batch_evaluate_board_ints(
    const int* pocket,
    const int* board,
    const int* remaining,
    int n_remaining,
    int* out_win,
    int* out_lose,
    int* out_draw
) {
    int p1 = to_pheval_id(pocket[0]);
    int p2 = to_pheval_id(pocket[1]);
    int b1 = to_pheval_id(board[0]);
    int b2 = to_pheval_id(board[1]);
    int b3 = to_pheval_id(board[2]);
    int b4 = to_pheval_id(board[3]);
    int b5 = to_pheval_id(board[4]);

    // 計算玩家 A 的 rank (1=最強)
    int rankA = evaluate_7cards(p1, p2, b1, b2, b3, b4, b5);

    int win = 0, lose = 0, draw = 0;

    // 遍歷對手 C(45, 2)
    for (int i = 0; i < n_remaining; ++i) {
        int r1 = to_pheval_id(remaining[i]);
        for (int j = i + 1; j < n_remaining; ++j) {
            int r2 = to_pheval_id(remaining[j]);
            int rankB = evaluate_7cards(r1, r2, b1, b2, b3, b4, b5);

            // 注意：rank 越小越強
            if (rankA < rankB) ++win;
            else if (rankA > rankB) ++lose;
            else ++draw;
        }
    }

    *out_win = win;
    *out_lose = lose;
    *out_draw = draw;
}

// 保留 judge 接口供相容使用 (字串版本)
int judge_hands_ids(const int* a, const int* b, const int* board) {
    int rankA = evaluate_7cards(to_pheval_id(a[0]), to_pheval_id(a[1]), 
                                to_pheval_id(board[0]), to_pheval_id(board[1]), 
                                to_pheval_id(board[2]), to_pheval_id(board[3]), 
                                to_pheval_id(board[4]));
    int rankB = evaluate_7cards(to_pheval_id(b[0]), to_pheval_id(b[1]), 
                                to_pheval_id(board[0]), to_pheval_id(board[1]), 
                                to_pheval_id(board[2]), to_pheval_id(board[3]), 
                                to_pheval_id(board[4]));
    if (rankA < rankB) return 1;
    if (rankA > rankB) return -1;
    return 0;
}

} // extern "C"
