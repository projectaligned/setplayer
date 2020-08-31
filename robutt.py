"""
I need to execute javascript code from within python in order to subscribe to the realplexor connection:
https://github.com/DmitryKoterov/dklab_realplexor
Reading the js code makes it clear that I don't want to reimplement this from scratch.

"""
import re
import time

from lxml import html
from requests import Session
import itertools
from typing import Tuple, List, Optional

SET_URL = 'https://smart-games.org/en/set'
SUBMIT_SINGLE_URL = f'{SET_URL}/submit_set'
SUBMIT_MULTI_URL = f'{SET_URL}/submit_multiplayer_set'
OPEN_URL = f'{SET_URL}/open_cards'
MULTIPLAYER_URL = f'{SET_URL}/multiplayer'
MAIN_URL = 'https://smart-games.org/en/main'
LOGIN_URL = f'{MAIN_URL}/login'
USER_NAME = 'emteetwo'
PASSWORD = 'emteetwo'

SHAPE_MAP = {'oval': 0, 'squiggle': 1, 'diamond': 2}
SHADING_MAP = {'solid': 0, 'open': 1, 'striped': 2}
COLOR_MAP = {'blue': 0, 'green': 1, 'red': 2}
NUMBER_MAP = {'1': 0, '2': 1, '3': 2}

MAP_ORDER = ['shape', 'shading', 'color', 'number']

CardCode = Tuple[int, int, int, int]
CardCombination = Tuple[Tuple[int, CardCode], Tuple[int, CardCode], Tuple[int, CardCode]]
WinningIndices = Tuple[int, int, int]

session = Session()


def get_invite_url(user: str) -> str:
    return f'{SET_URL}/invite_multiplayer/{user}'


def log_in():
    form = {'login': USER_NAME, 'password': PASSWORD, 'signin': 'Login'}
    response = session.post(LOGIN_URL, data=form)
    print(f'Logged In: {response.status_code == 200}')


def get_available_players() -> List[str]:
    page = session.get(MULTIPLAYER_URL)
    tree = html.fromstring(page.content)
    users = tree.xpath('//ul[@id="online_users"]/li/a/text()')
    return users


def get_realplexor_id() -> str:
    page = session.get(MULTIPLAYER_URL)
    text = page.text
    return re.search(r'realplexor.subscribe\("(id_[a-zA-Z0-9]+)"', text).group(1)


def invite_user(users: List[str], specific_user: Optional[str] = None):
    user = specific_user or users[0]
    invite_url = get_invite_url(user)
    session.get(invite_url)
    """
    notification = check_for_invite_sent()
    while not notification:
        time.sleep(1)
        notification = check_for_invite_sent()
    print(f'Invite Notification: {notification}')
    """


def check_for_invite_sent() -> Optional[str]:
    print('Checking for notification')
    page = session.get(MULTIPLAYER_URL)
    tree = html.fromstring(page.content)
    invite_notification = tree.xpath('//div[@id="user_box"]')
    print(invite_notification)
    if invite_notification:
        return invite_notification


def get_card_codes(home_url: str) -> Tuple[List[CardCode], List[str]]:
    page = session.get(home_url)
    tree = html.fromstring(page.content)
    cards = tree.xpath('//td[@class="card" and @id]/img[1]')
    card_alts = [card.get('alt') for card in cards]
    print(card_alts)
    split_card_alts = [tuple(card_name.strip().split(' ')) for card_name in card_alts]

    def map_card_alt(split_card_alt: Tuple[str, str, str, str]) -> CardCode:
        return (
            SHAPE_MAP[split_card_alt[0]],
            SHADING_MAP[split_card_alt[1]],
            COLOR_MAP[split_card_alt[2]],
            NUMBER_MAP[split_card_alt[3]]
        )

    return [map_card_alt(split_card_alt)for split_card_alt in split_card_alts], card_alts


def test_combination(card_combination: CardCombination) -> Tuple[bool, WinningIndices]:
    (indices_a, code_a), (indices_b, code_b), (indices_c, code_c) = card_combination
    winning = True
    for i in range(4):
        coord_sum = code_a[i] + code_b[i] + code_c[i]
        coord_remainder = coord_sum % 3
        winning = winning and coord_remainder == 0
    return winning, (indices_a, indices_b, indices_c)


def filter_test_result(test_result: Tuple[bool, WinningIndices]) -> bool:
    winning, combination = test_result
    return winning


def find_collinear(card_codes: List[CardCode]) -> Optional[WinningIndices]:
    card_combinations = itertools.combinations(enumerate(card_codes), 3)
    test_results = [test_combination(combination) for combination in card_combinations]

    winners = list(filter(filter_test_result, test_results))
    if len(winners) > 0:
        winning_indices = winners[0][1]
    else:
        winning_indices = None
    return winning_indices


def submit_set(winning_indices: WinningIndices, num_cards: int, submit_url: str) -> None:
    form = {f'card[{index}]': int(index in winning_indices) for index in range(num_cards)}
    response = session.post(submit_url, data=form)
    print(f'Set Submitted: {response.status_code == 200}')


def open_cards() -> None:
    response = session.get(OPEN_URL)
    print(f'Cards Opened: {response.status_code == 200}')


def print_duration(home_url: str) -> None:
    page = session.get(home_url)
    tree = html.fromstring(page.content)
    duration = tree.xpath('//span[@id="duration"]/text()')
    if duration:
        print(f'Duration: {duration[0]}')


def get_score(home_url: str) -> None:
    page = session.get(home_url)
    text = page.text
    score = re.search(r'Score: \d+', text).group(0)
    print(score)


def get_cards_in_deck(home_url: str) -> int:
    page = session.get(home_url)
    text = page.text
    cards_in_deck = re.search(r'(Cards in deck:)</span> (\d+)', text)
    print(cards_in_deck.group(1) + ' ' + cards_in_deck.group(2))
    return int(cards_in_deck.group(2))


def game_turn(turn_number: int, home_url: str, submit_url: str) -> bool:
    print()
    print(f'Turn Number: {turn_number}')

    card_codes, card_alts = get_card_codes(home_url)
    cards_in_deck = get_cards_in_deck(home_url)
    winning_indices = find_collinear(card_codes)
    game_over = False
    if winning_indices and len(card_codes) > 9:
        print([card_alts[index] for index in winning_indices])
        submit_set(winning_indices, len(card_codes), submit_url)
    else:
        if cards_in_deck == 0:
            game_over = True
            print('Game Over')
        else:
            open_cards()
    print_duration(home_url)
    get_score(home_url)
    print()
    return game_over


def play(home_url: str, submit_url: str):
    turn_number = 1
    game_over = False
    while not game_over:
        game_over = game_turn(turn_number, home_url, submit_url)
        turn_number += 1


def play_single_player():
    play(home_url=SUBMIT_SINGLE_URL, submit_url=SUBMIT_SINGLE_URL)


def play_multiplayer(start_link: str):
    play(home_url=start_link, submit_url=SUBMIT_MULTI_URL)


def invite_players(specific_user: Optional[str] = None) -> str:
    users = get_available_players()
    invite_user(users, specific_user)
    """
    time.sleep(1)
    start_link = check_for_start()
    while not start_link:
        time.sleep(1)
        start_link = check_for_start()
    return start_link
    """


def check_for_start() -> Optional[str]:
    page = session.get(MULTIPLAYER_URL)
    tree = html.fromstring(page.content)
    starts = tree.xpath('//div[@class="success"]/a')
    if starts:
        return starts[0].get('href')


def seek_matches(specific_user: Optional[str] = None):
    log_in()
    realplexor_id = get_realplexor_id()
    print(realplexor_id)
    # start_link = invite_players(specific_user=specific_user)
    # play_multiplayer(start_link)


def poll_for_start() -> str:
    start_link = check_for_start()
    while not start_link:
        time.sleep(1)
        start_link = check_for_start()
    return start_link


def check_for_invite_received(specific_user: Optional[str] = None) -> Optional[str]:
    print('Checking for notification')
    page = session.get(MULTIPLAYER_URL)
    tree = html.fromstring(page.content)
    invite_notification = tree.xpath('//div[@id="user_box"]')
    print(invite_notification)
    if invite_notification:
        return invite_notification


def accept_invite(invite_received: str) -> None:
    pass


def receive_matches(specific_user: Optional[str] = None):
    log_in()
    realplexor_id = get_realplexor_id()
    print(realplexor_id)
    """
    invite_received = check_for_invite_received(specific_user)
    while not invite_received:
        time.sleep(1)
        invite_received = check_for_invite_received(specific_user)
    accept_invite(invite_received)
    start_link = poll_for_start()
    play_multiplayer(start_link)
    """


if __name__ == '__main__':
    #seek_matches('jonwardme')
    #receive_matches('jonwardme')
    play_single_player()
