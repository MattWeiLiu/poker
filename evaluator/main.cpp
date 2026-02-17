#include <iostream>
#include <vector>
#include <sstream>
#include "poker_evaluator.h"

std::vector<Card> stringToCards(const std::string& input) {
    std::vector<Card> cards;
    std::stringstream ss(input);
    std::string temp;
    while (ss >> temp) {
        cards.push_back(PokerEvaluator::parseCard(temp));
    }
    return cards;
}

int main(int argc, char* argv[]) {
    bool machineMode = false;
    for (int i = 1; i < argc; ++i) {
        if (std::string(argv[i]) == "--machine") machineMode = true;
    }

    if (!machineMode) {
        std::cout << "=== Poker Evaluator Interactive Mode ===" << std::endl;
        std::cout << "Format: Rank+Suit (e.g., AS for Ace of Spades, 10H for 10 of Hearts)" << std::endl;
        std::cout << "Enter Player A hand (2 cards), Player B hand (2 cards), and Community cards (5 cards)." << std::endl;
        std::cout << "Example input: AS KS | QH QD | 2D 5S 7C 8D JH" << std::endl;
        std::cout << "Type 'exit' to quit." << std::endl;
    }

    std::string line;
    if (!machineMode) std::cout << "> ";
    while (std::getline(std::cin, line) && line != "exit") {
        if (line.empty()) {
            if (!machineMode) std::cout << "> ";
            continue;
        }

        // 新增 EVAL 命令：輸入 7 張牌，回傳牌力分數
        // 格式: EVAL AS KS 2D QS 7C 9S JS
        if (line.substr(0, 4) == "EVAL") {
            std::string cardsStr = line.substr(5); // 跳過 "EVAL "
            std::vector<Card> cards = stringToCards(cardsStr);
            if (cards.size() != 7) {
                if (!machineMode) std::cout << "Error: EVAL requires exactly 7 cards." << std::endl;
                else std::cout << "ERROR_EVAL_CARDS" << std::endl;
            } else {
                long long score = PokerEvaluator::evaluateSeven(cards);
                EvalResult res = PokerEvaluator::getBestHand(
                    std::vector<Card>(cards.begin(), cards.begin() + 2),
                    std::vector<Card>(cards.begin() + 2, cards.end())
                );
                std::cout << "RANK: " << score << std::endl;
                std::cout << "HAND: " << PokerEvaluator::handRankToString(res.handRank) << std::endl;
                std::cout << std::endl;
            }
            if (!machineMode) std::cout << "> ";
            continue;
        }

        // 原有的 judge 格式: "AS KS | QH QD | 2D 5S 7C 8D JH"
        std::stringstream ss(line);
        std::string part;
        std::vector<std::string> parts;
        while (std::getline(ss, part, '|')) {
            parts.push_back(part);
        }

        if (parts.size() < 3) {
            if (!machineMode) std::cout << "Error: Invalid format. Use '|' to separate A, B, and Community." << std::endl;
            else std::cout << "ERROR_FORMAT" << std::endl;
            if (!machineMode) std::cout << "> ";
            continue;
        }

        std::vector<Card> pA = stringToCards(parts[0]);
        std::vector<Card> pB = stringToCards(parts[1]);
        std::vector<Card> comm = stringToCards(parts[2]);

        if (pA.size() != 2 || pB.size() != 2 || comm.size() != 5) {
            if (!machineMode) std::cout << "Error: Need 2 cards each for players and 5 for community." << std::endl;
            else std::cout << "ERROR_CARDS_COUNT" << std::endl;
            if (!machineMode) std::cout << "> ";
            continue;
        }

        EvalResult resA = PokerEvaluator::getBestHand(pA, comm);
        EvalResult resB = PokerEvaluator::getBestHand(pB, comm);

        std::cout << "A's Best: " << PokerEvaluator::handRankToString(resA.handRank) << std::endl;
        std::cout << "B's Best: " << PokerEvaluator::handRankToString(resB.handRank) << std::endl;

        int result = PokerEvaluator::judge(pA, pB, comm);
        if (result == 1) std::cout << "Result: A" << std::endl;
        else if (result == -1) std::cout << "Result: B" << std::endl;
        else std::cout << "Result: TIE" << std::endl;
        std::cout << std::endl;
        
        if (!machineMode) std::cout << "> ";
    }

    return 0;
}
