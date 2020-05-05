#!/usr/bin/env python3
import yaml
import argparse
import os
import glob


class Flash:
    def __init__(self, deck):
        """
        Initializes the Flash class

        :param deck string: the user selected deck
        """
        # TODO allow absolute or relative path to a deck in addition to ones in
        # default location

        # construct the full path to flash decks
        deckpath = os.getenv('XDG_DATA_HOME')
        if deckpath is None:
            self.deckpath = os.getenv('HOME') + '/.local/share/flash'
        else:
            self.deckpath = deckpath + '/flash'

        # TODO create the '/flash' part of the directory if it doesn't exist

        # get list of all available decks
        self.decklist = glob.glob(self.deckpath + '/*.yaml')
        if not self.decklist:
            # TODO create a sample deck?
            print("Warning: no decks found in {}".format(self.deckpath))
            exit(1)

        # convert deck to a absolute path
        if deck:
            self.deck = self.deckpath + '/' + os.path.splitext(
                deck)[0] + '.yaml'

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
            exit(1)

        # process the deck
        with open(self.deck, 'r') as stream:
            try:
                print(yaml.safe_load(stream))
            except yaml.YAMLError as exc:
                print(exc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Flash cards for the terminal.")
    parser.add_argument('-d', '--deck', help="The deck to use")
    parser.add_argument('-l',
                        '--list',
                        action='store_true',
                        help="List the available decks")
    args = parser.parse_args()

    f = Flash(args.deck)

    # list avialable flash decks
    if args.list:
        f.List()
        exit(0)

    # verify user selected deck exists
    if not args.deck:
        print("Please select a deck. Use -l to list available decks.")

    # start flash card session
    f.Flash()
