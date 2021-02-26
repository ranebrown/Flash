#!/usr/bin/env python3
"""
Flash cards for the terminal.

https://github.com/ranebrown/Flash
"""
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
    Get a single character from user.

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
    """
    Flash card main class.

    Contains the main functionality needed to display flash cards from a yaml deck.
    """

    # q, Q, ctrl-c, ctrl-d, ctrl-z
    exitChars = ["q", "Q", "\x03", "\x04", "\x1a"]

    def __init__(self, deck, xeric, priority, frequency):
        """
        Initialize the Flash Class.

        Parameters
        ----------
        deck : string
            the user selected deck
        xeric : boolean
            true if priority 0 cards should be hidden
        priority : int
            only display cards of this priority level
        """
        self.xeric = xeric

        self.priority = priority

        self.frequency = frequency

        # construct the full path to flash decks
        deckpath = os.getenv("XDG_DATA_HOME")
        if deckpath is None:
            self.deckpath = os.getenv("HOME") + "/.local/share/flash"
        else:
            self.deckpath = deckpath + "/flash"

        # create the directory if it doesn't exist
        if not os.path.exists(self.deckpath):
            try:
                os.mkdir(self.deckpath)
            except OSError:
                print("Creation of the directory {} failed".format(self.deckpath))
                sys.exit(1)

        # get list of all available decks
        self.decklist = glob.glob(self.deckpath + "/*.yaml")
        if not self.decklist:
            # TODO create a sample deck?
            print("Warning: no decks found in {}".format(self.deckpath))
            sys.exit(1)

        if deck:
            # check if abs or relative path passed
            tmpdeck = os.path.abspath(deck)
            if os.path.isfile(tmpdeck):
                self.localFile = True
                self.deck = tmpdeck
                self.deckname = os.path.splitext(os.path.basename(self.deck))[0]
            else:
                self.localFile = False
                # assume deck is in standard deck location
                self.deck = self.deckpath + "/" + os.path.splitext(deck)[0] + ".yaml"
                self.deckname = os.path.splitext(deck)[0]

    def List(self):
        """Print all available flash card decks."""
        print("Available Flash decks:")
        for i, f in enumerate(self.decklist):
            print("  {}. {}".format(i + 1, os.path.splitext(os.path.basename(f))[0]))

    def VerifyDeck(self):
        """
        Check if the user selected deck is valid.

        This first checks if the user passed an absolute or relative path to a deck and
        then checks the list of decks.

        Returns true if the deck is valid.
        """
        if self.localFile or self.deck in self.decklist:
            return True
        else:
            return False

    def LoadCards(self):
        """
        Load the cards from the yaml deck.

        The cards are separated into groups based on priority and the final flashcard
        deck is adjusted based on user flags for priority and xeric (exclude pri
        0 cards).
        """
        if not self.VerifyDeck():
            print("Invalid deck selected. Use -l to list available decks.")
            sys.exit(1)

        # process the deck
        self.yaml = YAML()
        cards = self.yaml.load(Path(self.deck))
        self.decksize = len(cards)

        # sort into groups based on priority
        cardsp0 = []
        cardsp1 = []
        cardsp2 = []
        cardsp3 = []
        for elm in cards:
            if elm["priority"] == 0:
                cardsp0.append(elm)
            elif elm["priority"] == 1:
                cardsp1.append(elm)
            elif elm["priority"] == 2:
                cardsp2.append(elm)
            elif elm["priority"] == 3:
                cardsp3.append(elm)
            else:
                elm["priority"] = 3
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
            print("No cards available of selected priority {}.".format(self.priority))
            sys.exit(1)

        self.cardlist = cardlist
        self.cardsp0 = cardsp0
        self.cardsp1 = cardsp1
        self.cardsp2 = cardsp2
        self.cardsp3 = cardsp3

    def WriteCards(self):
        """Write the new card priorites back to the deck file."""
        if self.xeric:
            self.cardlist.append(self.cardsp0)
        if self.priority == 1:
            self.cardlist.extend((self.cardsp1, self.cardsp2, self.cardsp3))
        elif self.priority == 2:
            self.cardlist.extend((self.cardsp0, self.cardsp2, self.cardsp3))
        elif self.priority == 3:
            self.cardlist.extend((self.cardsp0, self.cardsp1, self.cardsp3))
        elif self.priority == 4:
            self.cardlist.extend((self.cardsp0, self.cardsp1, self.cardsp2))

        # convert the list of lists back to a single list
        newcards = [item for sublist in self.cardlist for item in sublist]

        # write the updates back to the card deck file
        self.yaml.dump(newcards, Path(self.deck))

    def DisplayCardQuestion(self, term, card):
        """
        Print the card header and question to terminal.

        Parameters
        ----------
        term : Terminal
            Terminal handle for displaying ANSI escape sequences
        card : yaml object
            yaml entry for the current card
        """
        print(term.clear())
        print(
            term.bold_reverse(
                "                          Flash Cards for the Terminal                          "  # noqa:E501
            )
        )
        print(term.bold("Deck name: ") + self.deckname)
        print(term.bold("Cards in deck: ") + str(self.decksize))
        print(term.bold("Cards remaining in run: ") + str(self.cardCount))
        print(term.bold("Question category: ") + card["subject"])
        print(term.bold("Question priority: ") + str(card["priority"] + 1))
        print()
        print(term.bold_yellow("Question:"))
        print(card["question"])

    def DisplayCardAnswer(self, term, card):
        """
        Print the card answer to terminal.

        Parameters
        ----------
        term : Terminal
            Terminal handle for displaying ANSI escape sequences
        card : yaml object
            yaml entry for the current card
        """
        print(term.bold_green("Answer:"))
        print(card["answer"])
        print(
            term.reverse(
                "================================================================================"  # noqa:E501
            )
        )
        print()
        print(term.bold("How difficult was the question?"))
        print()
        print(
            term.bold("Xeric ")
            + "[1]  "
            + term.green("Easy ")
            + "[2]  "
            + term.yellow("Normal ")
            + "[3]  "
            + term.red("Difficult ")
            + "[4]"
        )

    def UpdatePriority(self, newPri, card):
        """
        Update the priority of a card based on user input.

        An invalid priority results in no change to the priority.

        Parameters
        ----------
        newPri : char
            The new priority
        card : yaml object
            the card that is currently being updated
        """
        if newPri == "1":
            card["priority"] = 0
        elif newPri == "2":
            card["priority"] = 1
        elif newPri == "3":
            card["priority"] = 2
        elif newPri == "4":
            card["priority"] = 3

    def Flash(self):
        """
        Primary flash function.

        The questions are read in from the yaml deck and sorted into priority groups to
        display. Upon completion the deck is written back to the original file with the
        updated priorities entered by the user.

        If the user doesn't enter a specific priority to show then all high priority
        cards will be shown twice. Once at the beginning and then periodically as the
        remainder of the cards are shown.
        """
        self.LoadCards()

        t = Terminal()

        numHighPri = 0
        if self.priority == -1 and self.frequency != 0:
            numHighPri = len(self.cardsp3)

        # number of cards shown for this run
        self.cardCount = sum([len(c) for c in self.cardlist]) + numHighPri

        cardsSeen = 0
        for prio in self.cardlist:
            random.shuffle(prio)
            for card in prio:
                cardsSeen += 1

                # shuffle a random high priority card back in occasionally
                if (
                    self.frequency != 0
                    and numHighPri > 0
                    and card["priority"] != 3
                    and cardsSeen % self.frequency == 0
                ):
                    highPriCard = random.choice(self.cardsp3)
                    numHighPri -= 1

                    # show the card header and question
                    self.DisplayCardQuestion(t, highPriCard)

                    # remaining cards for the run
                    self.cardCount -= 1

                    # exit if user wants, else display answer on keypress
                    c = getch()
                    if c in self.exitChars:
                        break

                    # show the card answer and priority options
                    self.DisplayCardAnswer(t, highPriCard)

                    # get user input and then store new priority
                    c = getch()
                    if c in self.exitChars:
                        break
                    else:
                        self.UpdatePriority(c, highPriCard)

                # show the card header and question
                self.DisplayCardQuestion(t, card)

                # remaining cards for the run
                self.cardCount -= 1

                # exit if user wants, else display answer on keypress
                c = getch()
                if c in self.exitChars:
                    break

                # show the card answer and priority options
                self.DisplayCardAnswer(t, card)

                # get user input and then store new priority
                c = getch()
                if c in self.exitChars:
                    break
                else:
                    self.UpdatePriority(c, card)

            # see https://stackoverflow.com/a/654002/4162894 for an explanation
            # of how the nested loops are exited
            else:
                continue
            break

        self.WriteCards()


if __name__ == "__main__":
    # filter ANSI escape sequences for Windows
    if os.name == "nt":
        import colorama

        colorama.init()

    parser = argparse.ArgumentParser(description="Flash cards for the terminal.")
    parser.add_argument("-d", "--deck", help="The deck to use")
    parser.add_argument(
        "-p",
        "--priority",
        type=int,
        default=-1,
        help="Only show cards of the given priority. Valid values are 1,2,3,4",
    )
    parser.add_argument(
        "-f",
        "--frequency",
        type=int,
        default=5,
        help="""
            How often to shuffle back in high priority cards. The frequency is
            determined by the number of cards in run modulo this argument. The default
            is 5. Set to 0 to disable.
            """,
    )
    parser.add_argument(
        "-x",
        "--xeric",
        action="store_true",
        help="If this flag is used cards with a priority of " "0 will not be shown.",
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="List the available decks"
    )
    args = parser.parse_args()

    f = Flash(args.deck, args.xeric, args.priority, args.frequency)

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
