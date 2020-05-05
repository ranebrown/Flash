#!/usr/bin/env python3
import yaml
import argparse
import os
import glob

# with open("test.yaml", 'r') as stream:
#     try:
#         print(yaml.safe_load(stream))
#     except yaml.YAMLError as exc:
#         print(exc)


class Flash:
    def __init__(self, deck):
        # TODO allow absolute or relative path to a deck in addition to ones in
        # default location

        # construct the full path to flash decks
        deckpath = os.getenv('XDG_DATA_HOME')
        if deckpath is None:
            self.deckpath = os.getenv('HOME') + '/.local/share/flash'
        else:
            self.deckpath = deckpath + '/flash'

        # get list of all available decks
        self.decklist = glob.glob(self.deckpath + '/*.yaml')
        if not self.decklist:
            print("Warning: no decks found in {}".format(self.deckpath))
            exit(0)

        # convert deck to a absolute path
        if deck:
            self.deck = self.deckpath + '/' + os.path.splitext(
                deck)[0] + '.yaml'

    def List(self):
        """
        Print all available flash card decks
        """
        for f in self.decklist:
            print(f)

    def VerifyDeck(self):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Flash cards for the terminal.')
    parser.add_argument('-d', '--deck', help='The deck to use')
    parser.add_argument('-l',
                        '--list',
                        action='store_true',
                        help='List the available decks')
    args = parser.parse_args()

    f = Flash(args.deck)

    # list avialable flash decks
    if args.list:
        f.list()
        exit(0)

    # verify user selected deck exists
