"""Command-line interface for tex-repo."""

import sys
import argparse
from . import __version__
from .cmd_init import cmd_init
from .cmd_authoring import cmd_book, cmd_paper, cmd_part, cmd_chapter
from .cmd_build import cmd_build
from .cmd_release import cmd_release
from .cmd_validation import cmd_status, cmd_fix, cmd_guard


def create_parser():
    """Create the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog='tex-repo',
        description='Structural manager for LaTeX repositories'
    )
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # init command
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize a new repository'
    )
    init_parser.add_argument('name', help='Repository name')
    init_parser.set_defaults(func=cmd_init)
    
    # book command
    book_parser = subparsers.add_parser(
        'book',
        help='Create a book-class document'
    )
    book_parser.add_argument('title', help='Book title')
    book_parser.set_defaults(func=cmd_book)
    
    # paper command
    paper_parser = subparsers.add_parser(
        'paper',
        help='Create an article-class paper'
    )
    paper_parser.add_argument('title', help='Paper title')
    paper_parser.set_defaults(func=cmd_paper)
    
    # part command
    part_parser = subparsers.add_parser(
        'part',
        help='Create a part inside a book'
    )
    part_parser.add_argument('title', help='Part title')
    part_parser.set_defaults(func=cmd_part)
    
    # chapter command
    chapter_parser = subparsers.add_parser(
        'chapter',
        help='Create a chapter inside a part'
    )
    chapter_parser.add_argument('title', help='Chapter title')
    chapter_parser.set_defaults(func=cmd_chapter)
    
    # build command
    build_parser = subparsers.add_parser(
        'build',
        help='Build LaTeX documents'
    )
    build_parser.add_argument(
        'target',
        nargs='?',
        help='Target to build (default: current directory, "all" for everything)'
    )
    build_parser.set_defaults(func=cmd_build)
    
    # release command
    release_parser = subparsers.add_parser(
        'release',
        help='Create immutable release bundle'
    )
    release_parser.add_argument('target', help='Document to release')
    release_parser.set_defaults(func=cmd_release)
    
    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Validate repository structure'
    )
    status_parser.set_defaults(func=cmd_status)
    
    # fix command
    fix_parser = subparsers.add_parser(
        'fix',
        help='Create missing required files and directories'
    )
    fix_parser.set_defaults(func=cmd_fix)
    
    # guard command
    guard_parser = subparsers.add_parser(
        'guard',
        help='Enforce repository invariants for CI'
    )
    guard_parser.set_defaults(func=cmd_guard)
    
    return parser


def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute the command
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
