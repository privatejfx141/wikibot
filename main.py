import argparse
import wikibot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--move-category", "-mc", type=str, nargs=2)
    args = parser.parse_args(['--move-category', 'test', 'test2']) 
    print(args.move_category)


if __name__ == "__main__":
    main()
