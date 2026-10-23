"""Ground one premise from the command line.

    omega-ground "((--> dolphin mammal) (stv 1.0 0.9))"
    omega-ground "((--> (× usdc 18) decimals) (stv 1.0 0.9))"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .grounder import default_grounder
from .nal import Truth, parse_premise


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("premise", help="NAL premise, e.g. '((--> dolphin mammal) (stv 1.0 0.9))'")
    parser.add_argument("--mode", choices=["live", "record", "replay"], default="live")
    parser.add_argument("--cassette", type=Path)
    parser.add_argument("--open-world", action="store_true",
                        help="treat a missing Wikidata path as UNKNOWN instead of weak refutation")
    args = parser.parse_args(argv)

    grounder = default_grounder(args.cassette, args.mode, closed_world=not args.open_world)
    statement, truth = parse_premise(args.premise)
    truth = truth or Truth(1.0, 0.9)
    result = grounder.ground(statement, truth)
    grounder.close()
    print(f"premise   {args.premise}")
    print(f"evidence  {result.evidence.to_metta()}")
    print(f"grounded  {result.to_metta()}")


if __name__ == "__main__":
    main()
