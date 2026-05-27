import sys

import click

from components.input_handler import detect_url_type, is_valid_youtube_url
from components.prompt_handler import (
    get_download_options,
    ask_skip_or_abort,
    confirm_download,
    select_playlist_items,
)
from components.queue_manager import QueueManager, ItemStatus
from components.downloader import Downloader, DownloadError
from components.config_handler import load_config, save_config, AppConfig
from utils.logger import (
    print_banner,
    print_detection,
    print_error,
    print_info,
    print_success,
    print_warning,
    print_summary,
)


@click.command()
@click.option("--url", "-u", default=None, help="YouTube URL to download")
@click.option("--use-defaults", is_flag=True, help="Skip all prompts, use saved config")
def main(url: str | None, use_defaults: bool):
    config = load_config()

    print_banner()

    if not url:
        from InquirerPy import inquirer
        url = inquirer.text(message="Enter YouTube URL:").execute()

    if not is_valid_youtube_url(url):
        print_error("Invalid YouTube URL. Please try again.")
        sys.exit(1)

    try:
        info = detect_url_type(url)
    except Exception as e:
        print_error(f"Failed to fetch URL info: {e}")
        sys.exit(1)

    if info["type"] == "playlist":
        print_detection(f'Playlist \u2014 "{info["title"]}" ({info["count"]} videos)')
    else:
        print_detection(f'Video \u2014 "{info["title"]}"')

    if info["count"] == 0:
        print_warning("No videos found.")
        sys.exit(0)

    options = get_download_options(config, use_defaults)

    entries = info["entries"]
    if info["type"] == "playlist" and not use_defaults:
        selected = select_playlist_items(entries)
        if selected:
            entries = selected

    if not confirm_download(len(entries), options["output"]):
        print_info("Download cancelled.")
        sys.exit(0)

    queue = QueueManager(entries)
    downloader = Downloader()

    for item in queue.pending():
        print_info(f'Downloading [{item.index}/{len(queue.items)}] \u2014 "{item.title}"')
        try:
            downloader.download(item, options)
            queue.mark_done(item)
            print_success(f"[{item.index}/{len(queue.items)}] Done")
        except DownloadError as e:
            queue.mark_failed(item, str(e))
            print_error(f"[{item.index}/{len(queue.items)}] Failed \u2014 {e}")
            if not ask_skip_or_abort():
                break
        except KeyboardInterrupt:
            print_warning("\nInterrupted by user.")
            break

    summary = queue.summary()
    print_summary(summary["done"], summary["failed"], summary["total"])

    if config.remember_last:
        config.default_format = options["format"]
        config.default_quality = options["quality"]
        if options.get("audio_bitrate"):
            config.default_audio_bitrate = options["audio_bitrate"]
        config.default_output_path = options["output"]
        save_config(config)


if __name__ == "__main__":
    main()
