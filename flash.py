#!/usr/bin/env python3
import argparse
import glob
import os
import random
import sys
from pathlib import Path

from blessings import Terminal
from ruamel.yaml import YAML


def _find_getch():
    """
    Gets a single character from user.
    Reference: https://stackoverflow.com/a/21659588

    """
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys
    import tty

    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch


getch = _find_getch()


class Flash:
    def __init__(self, deck, xeric, priority):
        """
        Initializes the Flash class

        :param deck string: the user selected deck
        :param xeric boolean: true if priority 0 cards should be hidden
        :param priority int: only display cards of this priority level
        """
        # TODO allow absolute or relative path to a deck in addition to ones in
        # default location

        self.xeric = xeric

        self.priority = priority

        # construct the full path to flash decks
        deckpath = os.getenv('XDG_DATA_HOME')
        if deckpath is None:
            self.deckpath = os.getenv('HOME') + '/.local/share/flash'
        else:
            self.deckpath = deckpath + '/flash'

        # create the directory if it doesn't exist
        if not os.path.exists(self.deckpath):
            try:
                os.mkdir(self.deckpath)
            except OSError:
                print("Creation of the directory {} failed".format(
                    self.deckpath))
                sys.exit(1)

        # get list of all available decks
        self.decklist = glob.glob(self.deckpath + '/*.yaml')
        if not self.decklist:
            # TODO create a sample deck?
            print("Warning: no decks found in {}".format(self.deckpath))
            sys.exit(1)

        # convert deck to a absolute path
        if deck:
            self.deck = self.deckpath + '/' + os.path.splitext(
                deck)[0] + '.yaml'
            self.deckname = os.path.splitext(deck)[0]

    def List(self):
        """
        Print all available flash card decks

        """
        print("Available Flash decks:")
        for i, f in enumerate(self.decklist):
            print("  {}. {}".format(i + 1,
                                    os.path.splitext(os.path.basename(f))[0]))

    def VerifyDeck(self):
        """
        Checks if the user selected deck exists in the list of available decks.
        Returns true if the deck is valid.

        """
        if self.deck in self.decklist:
            return True
        else:
            return False

    def Flash(self):
        if not self.VerifyDeck():
            print("Invalid deck selected. Use -l to list available decks.")
            sys.exit(1)

        # process the deck
        yaml = YAML()
        cards = yaml.load(Path(self.deck))
        decksize = len(cards)

        # sort into groups based on priority
        cardsp0 = []
        cardsp1 = []
        cardsp2 = []
        cardsp3 = []
        for elm in cards:
            if elm['priority'] == 0:
                cardsp0.append(elm)
            elif elm['priority'] == 1:
                cardsp1.append(elm)
            elif elm['priority'] == 2:
                cardsp2.append(elm)
            elif elm['priority'] == 3:
                cardsp3.append(elm)
            else:
                elm['priority'] = 3
                cardsp3.append(elm)

        if self.priority == -1:
            if not self.xeric:
                # all cards
                cardlist = [cardsp3, cardsp2, cardsp1, cardsp0]
            else:
                # exclude priority 0 cards
                cardlist = [cardsp3, cardsp2, cardsp1]
        else:
            # only show cards of the selected priority
            if self.priority == 1:
                cardlist = [cardsp0]
            elif self.priority == 2:
                cardlist = [cardsp1]
            elif self.priority == 3:
                cardlist = [cardsp2]
            elif self.priority == 4:
                cardlist = [cardsp3]
            else:
                print("Invalid priority ({}) selected.".format(self.priority))
                sys.exit(1)

        if all([not elem for elem in cardlist]):
            print("No cards available of selected priority {}.".format(
                self.priority))
            sys.exit(1)

        t = Terminal()

        for prio in cardlist:
            random.shuffle(prio)
            for card in prio:
                # TODO shuffle a random hard priority card back in occasionally
                print(t.clear())
                print(t.bold_reverse(
                    "                          Flash Cards for the Terminal                          "
                ))
                print(t.bold("Deck name: ") + self.deckname)
                print(t.bold("Cards in deck: ") + str(decksize))
                print(t.bold("Question category: ") + card['subject'])
                print(t.bold("Question priority: ") + str(card['priority'] + 1))
                print()
                print(t.bold_yellow("Question:"))
                print(card['question'])
                c = getch()
                if c == 'q' or c == 'Q':
                    break
                elif c == '\x03' or c == '\x04' or c == '\x1a':
                    # handle ctrl-c, ctrl-d, ctrl-z
                    break
                print(t.bold_green("Answer:"))
                print(card['answer'])
                print(t.reverse(
                    "================================================================================"
                ))
                print()
                print(t.bold("How difficult was the question?"))
                print()
                print(t.bold("Xeric ") + "[1]  " + t.green("Easy ") + "[2]  " +
                      t.yellow("Normal ") + "[3]  " + t.red("Difficult ") +
                      "[4]")
                c = getch()
                if c == 'q' or c == 'Q':
                    break
                elif c == '\x03' or c == '\x04' or c == '\x1a':
                    # handle ctrl-c, ctrl-d, ctrl-z
                    break
                elif c == '1':
                    card['priority'] = 0
                elif c == '2':
                    card['priority'] = 1
                elif c == '3':
                    card['priority'] = 2
                elif c == '4':
                    card['priority'] = 3
            # see https://stackoverflow.com/a/654002/4162894 for an explanation
            # of how the nested loops are exited
            else:
                continue
            break

        # make sure all cards get written back to the file
        if self.xeric:
            cardlist.append(cardsp0)
        if self.priority == 1:
            cardlist.extend((cardsp1, cardsp2, cardsp3))
        elif self.priority == 2:
            cardlist.extend((cardsp0, cardsp2, cardsp3))
        elif self.priority == 3:
            cardlist.extend((cardsp0, cardsp1, cardsp3))
        elif self.priority == 4:
            cardlist.extend((cardsp0, cardsp1, cardsp2))

        # convert the list of lists back to a single list
        newcards = [item for sublist in cardlist for item in sublist]

        # write the updates back to the card deck file
        yaml.dump(newcards, Path(self.deck))


if __name__ == "__main__":
    # filter ANSI escape sequences for Windows
    if os.name == 'nt':
        import colorama
        colorama.init()

    parser = argparse.ArgumentParser(
        description="Flash cards for the terminal.")
    parser.add_argument('-d', '--deck', help="The deck to use")
    parser.add_argument(
        '-p',
        '--priority',
        type=int,
        default=-1,
        help="Only show cards of the given priority. Valid values are 1,2,3,4")
    parser.add_argument('-x',
                        '--xeric',
                        action='store_true',
                        help="If this flag is used cards with a priority of "
                        "0 will not be shown.")
    parser.add_argument('-l',
                        '--list',
                        action='store_true',
                        help="List the available decks")
    args = parser.parse_args()

    f = Flash(args.deck, args.xeric, args.priority)

    # list avialable flash decks
    if args.list:
        f.List()
        sys.exit(0)

    # verify user selected deck exists
    if not args.deck:
        print("Please select a deck. Use -l to list available decks.")
        sys.exit(1)

    # start flash card session
    f.Flash()
